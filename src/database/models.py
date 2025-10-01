"""
Database Models for Commission Tracking System

This module defines the SQLAlchemy ORM models for storing commission data.
The schema is designed to capture all relevant transaction details while
maintaining data integrity and supporting complex commission split scenarios.
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Float, ForeignKey, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
from typing import Optional

Base = declarative_base()


class Commission(Base):
    """
    Main commission transaction table.
    
    This table stores the core details of each commission transaction,
    including property information, financial details, and metadata about
    the data extraction process.
    
    Fields Explained:
    - id: Primary key for internal database operations
    - transaction_id: Unique identifier from the source system (e.g., MLS, title company)
    - property_address: Full address of the property involved in the transaction
    - sale_amount: Final sale price of the property
    - commission_rate: Percentage rate of commission (e.g., 0.06 for 6%)
    - total_commission: Total commission amount before splits
    - closing_date: Date when the transaction closed
    - email_source: Email address or identifier of the source
    - email_subject: Subject line of the source email (for traceability)
    - raw_email_content: Full text of the original email (for audit trail)
    - confidence_score: AI parser confidence (0.0-1.0) for data quality monitoring
    - created_at: Timestamp when record was created in our system
    - updated_at: Timestamp of last update (for tracking corrections)
    - status: Processing status (pending, verified, paid, disputed)
    - notes: Additional notes or comments about the transaction
    """
    __tablename__ = "commissions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Property Information
    property_address = Column(String(500), nullable=False)
    
    # Financial Details
    sale_amount = Column(Numeric(12, 2), nullable=False)  # Up to $9,999,999,999.99
    commission_rate = Column(Float, nullable=False)  # Stored as decimal (e.g., 0.06)
    total_commission = Column(Numeric(10, 2), nullable=False)  # Up to $99,999,999.99
    
    # Transaction Dates
    closing_date = Column(DateTime, nullable=False, index=True)
    
    # Email Source Information
    email_source = Column(String(255), nullable=False)
    email_subject = Column(String(500))
    raw_email_content = Column(Text)  # Store full email for audit trail
    
    # Data Quality & Metadata
    confidence_score = Column(Float, default=0.0)  # AI parsing confidence
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Status Tracking
    status = Column(String(50), default="pending", index=True)  # pending, verified, paid, disputed
    notes = Column(Text)
    
    # Relationships
    splits = relationship("CommissionSplit", back_populates="commission", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Commission(id={self.id}, transaction_id='{self.transaction_id}', amount=${self.total_commission})>"
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "property_address": self.property_address,
            "sale_amount": float(self.sale_amount),
            "commission_rate": self.commission_rate,
            "total_commission": float(self.total_commission),
            "closing_date": self.closing_date.isoformat() if self.closing_date else None,
            "email_source": self.email_source,
            "email_subject": self.email_subject,
            "confidence_score": self.confidence_score,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "splits": [split.to_dict() for split in self.splits] if self.splits else []
        }


class CommissionSplit(Base):
    """
    Commission split details for individual agents.
    
    This table handles the distribution of commission among multiple agents
    involved in a transaction. Supports complex split scenarios including
    multiple agents, varying percentages, and hierarchical splits.
    
    Fields Explained:
    - id: Primary key
    - commission_id: Foreign key linking to parent Commission record
    - agent_name: Full name of the agent receiving this split
    - agent_email: Email address for the agent (for notifications/verification)
    - agent_id: Optional internal agent identifier
    - percentage: Percentage of total commission (e.g., 0.60 for 60%)
    - amount: Calculated dollar amount for this split
    - role: Agent's role in transaction (listing, buyer, referral, etc.)
    - notes: Additional notes about this specific split
    """
    __tablename__ = "commission_splits"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    commission_id = Column(Integer, ForeignKey("commissions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Agent Information
    agent_name = Column(String(255), nullable=False, index=True)
    agent_email = Column(String(255))
    agent_id = Column(String(100))  # Optional internal agent ID
    
    # Split Details
    percentage = Column(Float, nullable=False)  # Stored as decimal (e.g., 0.60)
    amount = Column(Numeric(10, 2), nullable=False)
    
    # Additional Context
    role = Column(String(100))  # listing_agent, buyer_agent, referral, etc.
    notes = Column(Text)
    
    # Relationships
    commission = relationship("Commission", back_populates="splits")
    
    def __repr__(self):
        return f"<CommissionSplit(agent='{self.agent_name}', percentage={self.percentage}, amount=${self.amount})>"
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            "id": self.id,
            "agent_name": self.agent_name,
            "agent_email": self.agent_email,
            "agent_id": self.agent_id,
            "percentage": self.percentage,
            "amount": float(self.amount),
            "role": self.role,
            "notes": self.notes
        }


class DatabaseManager:
    """
    Database connection and session management.
    
    This class handles database initialization, connection pooling,
    and session lifecycle management.
    """
    
    def __init__(self, database_url: str = "sqlite:///commissions.db"):
        """
        Initialize database manager.
        
        Args:
            database_url: SQLAlchemy database URL. Defaults to SQLite file.
        """
        self.engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL query logging during development
            pool_pre_ping=True,  # Verify connections before using
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self):
        """
        Get a new database session.
        
        Usage:
            db = DatabaseManager()
            session = db.get_session()
            try:
                # Do database operations
                session.commit()
            except Exception as e:
                session.rollback()
                raise
            finally:
                session.close()
        """
        return self.SessionLocal()
    
    def reset_database(self):
        """Drop and recreate all tables (for testing/development)"""
        self.drop_tables()
        self.create_tables()

