"""
Repository layer for database operations.

This module provides a clean abstraction over database operations,
implementing the Repository pattern for better testability and maintainability.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from .models import Commission, CommissionSplit, DatabaseManager
from ..models.commission import CommissionData, CommissionSplitData


class CommissionRepository:
    """
    Repository for Commission and CommissionSplit database operations.
    
    Provides high-level methods for CRUD operations and complex queries,
    abstracting away SQLAlchemy details from the rest of the application.
    """
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize repository.
        
        Args:
            db_manager: DatabaseManager instance. If None, creates a default one.
        """
        self.db_manager = db_manager or DatabaseManager()
    
    def save_commission(self, commission_data: CommissionData) -> Commission:
        """
        Save a new commission record with its splits.
        
        Args:
            commission_data: Validated CommissionData object
            
        Returns:
            Created Commission database object
            
        Raises:
            ValueError: If transaction_id already exists
            Exception: For other database errors
        """
        session = self.db_manager.get_session()
        try:
            # Check if transaction_id already exists
            existing = session.query(Commission).filter_by(
                transaction_id=commission_data.transaction_id
            ).first()
            
            if existing:
                raise ValueError(f"Transaction ID {commission_data.transaction_id} already exists")
            
            # Create Commission record
            commission = Commission(
                transaction_id=commission_data.transaction_id,
                property_address=commission_data.property_address,
                sale_amount=commission_data.sale_amount,
                commission_rate=commission_data.commission_rate,
                total_commission=commission_data.total_commission,
                closing_date=commission_data.closing_date,
                email_source=commission_data.email_source,
                email_subject=commission_data.email_subject,
                raw_email_content=commission_data.raw_email_content,
                confidence_score=commission_data.confidence_score,
                status=commission_data.status,
                notes=commission_data.notes
            )
            
            # Create CommissionSplit records
            for split_data in commission_data.splits:
                split = CommissionSplit(
                    agent_name=split_data.agent_name,
                    agent_email=split_data.agent_email,
                    agent_id=split_data.agent_id,
                    percentage=split_data.percentage,
                    amount=split_data.amount,
                    role=split_data.role,
                    notes=split_data.notes
                )
                commission.splits.append(split)
            
            session.add(commission)
            session.commit()
            session.refresh(commission)
            
            return commission
            
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_commission_by_id(self, commission_id: int) -> Optional[Commission]:
        """Get a commission record by its database ID"""
        session = self.db_manager.get_session()
        try:
            return session.query(Commission).filter_by(id=commission_id).first()
        finally:
            session.close()
    
    def get_commission_by_transaction_id(self, transaction_id: str) -> Optional[Commission]:
        """Get a commission record by its transaction ID"""
        session = self.db_manager.get_session()
        try:
            return session.query(Commission).filter_by(transaction_id=transaction_id).first()
        finally:
            session.close()
    
    def update_commission_status(self, commission_id: int, status: str, notes: Optional[str] = None) -> bool:
        """
        Update the status of a commission record.
        
        Args:
            commission_id: Database ID of the commission
            status: New status value
            notes: Optional notes to add
            
        Returns:
            True if updated, False if not found
        """
        session = self.db_manager.get_session()
        try:
            commission = session.query(Commission).filter_by(id=commission_id).first()
            if not commission:
                return False
            
            commission.status = status
            if notes:
                commission.notes = notes
            commission.updated_at = datetime.utcnow()
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def query_commissions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        agent_name: Optional[str] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Commission]:
        """
        Query commissions with various filters.
        
        Args:
            start_date: Filter by closing date >= this date
            end_date: Filter by closing date <= this date
            status: Filter by status
            agent_name: Filter by agent name (searches in splits)
            min_amount: Filter by total_commission >= this amount
            max_amount: Filter by total_commission <= this amount
            limit: Maximum number of results
            offset: Number of results to skip (for pagination)
            
        Returns:
            List of Commission objects matching the filters
        """
        session = self.db_manager.get_session()
        try:
            query = session.query(Commission)
            
            # Apply filters
            filters = []
            
            if start_date:
                filters.append(Commission.closing_date >= start_date)
            
            if end_date:
                filters.append(Commission.closing_date <= end_date)
            
            if status:
                filters.append(Commission.status == status)
            
            if min_amount is not None:
                filters.append(Commission.total_commission >= min_amount)
            
            if max_amount is not None:
                filters.append(Commission.total_commission <= max_amount)
            
            if filters:
                query = query.filter(and_(*filters))
            
            # Filter by agent name (requires join with splits)
            if agent_name:
                query = query.join(CommissionSplit).filter(
                    CommissionSplit.agent_name.ilike(f"%{agent_name}%")
                ).distinct()
            
            # Order by closing date (most recent first)
            query = query.order_by(desc(Commission.closing_date))
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            return query.all()
            
        finally:
            session.close()
    
    def get_agent_commissions(
        self,
        agent_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all commission splits for a specific agent.
        
        Args:
            agent_name: Name of the agent
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of dictionaries with commission and split details
        """
        session = self.db_manager.get_session()
        try:
            query = session.query(Commission, CommissionSplit).join(
                CommissionSplit
            ).filter(
                CommissionSplit.agent_name.ilike(f"%{agent_name}%")
            )
            
            if start_date:
                query = query.filter(Commission.closing_date >= start_date)
            
            if end_date:
                query = query.filter(Commission.closing_date <= end_date)
            
            query = query.order_by(desc(Commission.closing_date))
            
            results = []
            for commission, split in query.all():
                results.append({
                    "commission": commission.to_dict(),
                    "split": split.to_dict()
                })
            
            return results
            
        finally:
            session.close()
    
    def get_total_commissions_by_agent(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get total commission amounts grouped by agent.
        
        Useful for dashboard summaries and reporting.
        
        Returns:
            List of dictionaries with agent_name and total_amount
        """
        session = self.db_manager.get_session()
        try:
            from sqlalchemy import func
            
            query = session.query(
                CommissionSplit.agent_name,
                func.sum(CommissionSplit.amount).label('total_amount'),
                func.count(CommissionSplit.id).label('transaction_count')
            ).join(Commission)
            
            if start_date:
                query = query.filter(Commission.closing_date >= start_date)
            
            if end_date:
                query = query.filter(Commission.closing_date <= end_date)
            
            query = query.group_by(CommissionSplit.agent_name).order_by(
                desc('total_amount')
            )
            
            results = []
            for row in query.all():
                results.append({
                    "agent_name": row.agent_name,
                    "total_amount": float(row.total_amount),
                    "transaction_count": row.transaction_count
                })
            
            return results
            
        finally:
            session.close()
    
    def delete_commission(self, commission_id: int) -> bool:
        """
        Delete a commission record (and its splits via cascade).
        
        Args:
            commission_id: Database ID of the commission
            
        Returns:
            True if deleted, False if not found
        """
        session = self.db_manager.get_session()
        try:
            commission = session.query(Commission).filter_by(id=commission_id).first()
            if not commission:
                return False
            
            session.delete(commission)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

