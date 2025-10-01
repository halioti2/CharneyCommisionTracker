# Quick Reference Guide

## 🚀 Getting Started (30 seconds)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
copy .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Run the application
python run.py
```

## 📝 Common Commands

### Running the Application
```bash
# Standard way
python run.py

# Direct Flask app
python src/api/app.py

# With custom port
FLASK_PORT=8000 python run.py
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_models.py

# Run integration tests only
pytest -m integration

# Verbose output
pytest -v
```

### Database Operations
```bash
# Initialize database
python -c "from src.database.models import DatabaseManager; DatabaseManager().create_tables()"

# Reset database (WARNING: deletes all data)
python -c "from src.database.models import DatabaseManager; DatabaseManager().reset_database()"
```

## 🔌 API Quick Reference

### Base URL
```
http://localhost:5000/api/v1
```

### Essential Endpoints

**Health Check**
```bash
curl http://localhost:5000/api/v1/health
```

**Parse Email**
```bash
curl -X POST http://localhost:5000/api/v1/parse \
  -H "Content-Type: application/json" \
  -d '{
    "email_content": "Your email content here...",
    "email_subject": "Commission Statement",
    "email_source": "sender@example.com"
  }'
```

**Get All Commissions**
```bash
curl http://localhost:5000/api/v1/commissions
```

**Get Commissions with Filters**
```bash
curl "http://localhost:5000/api/v1/commissions?status=verified&limit=10"
```

**Get Single Commission**
```bash
curl http://localhost:5000/api/v1/commissions/1
```

**Update Status**
```bash
curl -X PATCH http://localhost:5000/api/v1/commissions/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "verified", "notes": "Approved"}'
```

**Get Agent Summary**
```bash
curl http://localhost:5000/api/v1/agents/summary
```

**Get Agent Commissions**
```bash
curl http://localhost:5000/api/v1/agents/John%20Smith/commissions
```

**Delete Commission**
```bash
curl -X DELETE http://localhost:5000/api/v1/commissions/1
```

## 🐍 Python Usage Examples

### Parse Email Programmatically
```python
from src.parsers.email_parser import AIEmailParser
from config.config import config

parser = AIEmailParser(api_key=config.OPENAI_API_KEY)
commission_data = parser.parse_commission_email(
    email_content="Your email content...",
    email_subject="Commission Statement",
    email_source="sender@example.com"
)
print(f"Transaction: {commission_data.transaction_id}")
```

### Save to Database
```python
from src.database.repository import CommissionRepository

repository = CommissionRepository()
commission = repository.save_commission(commission_data)
print(f"Saved with ID: {commission.id}")
```

### Query Commissions
```python
from datetime import datetime
from decimal import Decimal

# Get all verified commissions
verified = repository.query_commissions(status="verified")

# Get commissions in date range
commissions = repository.query_commissions(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

# Get high-value commissions
high_value = repository.query_commissions(
    min_amount=Decimal("25000.00")
)
```

### Get Agent Data
```python
# Get all commissions for an agent
agent_commissions = repository.get_agent_commissions("John Smith")

# Get agent summary
summary = repository.get_total_commissions_by_agent()
for agent in summary:
    print(f"{agent['agent_name']}: ${agent['total_amount']}")
```

## 🔧 Configuration

### Environment Variables (.env)

**Required**
```
OPENAI_API_KEY=your-api-key-here
```

**Optional (with defaults)**
```
# Application
DEBUG=False
ENVIRONMENT=production
FLASK_PORT=5000

# Database
DATABASE_URL=sqlite:///commissions.db

# OpenAI
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.1

# Email (for IMAP processing)
EMAIL_HOST=imap.gmail.com
EMAIL_PORT=993
EMAIL_USERNAME=your-email@example.com
EMAIL_PASSWORD=your-password

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

## 📊 Database Schema Quick Reference

### Commissions Table
```sql
CREATE TABLE commissions (
    id INTEGER PRIMARY KEY,
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    property_address VARCHAR(500) NOT NULL,
    sale_amount DECIMAL(12,2) NOT NULL,
    commission_rate FLOAT NOT NULL,
    total_commission DECIMAL(10,2) NOT NULL,
    closing_date DATETIME NOT NULL,
    email_source VARCHAR(255) NOT NULL,
    email_subject VARCHAR(500),
    raw_email_content TEXT,
    confidence_score FLOAT DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    notes TEXT
);
```

### Commission Splits Table
```sql
CREATE TABLE commission_splits (
    id INTEGER PRIMARY KEY,
    commission_id INTEGER NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    agent_email VARCHAR(255),
    agent_id VARCHAR(100),
    percentage FLOAT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    role VARCHAR(100),
    notes TEXT,
    FOREIGN KEY (commission_id) REFERENCES commissions(id) ON DELETE CASCADE
);
```

## 🐛 Troubleshooting

### Common Issues

**"OPENAI_API_KEY not configured"**
```bash
# Solution: Add your API key to .env file
echo "OPENAI_API_KEY=your-key-here" >> .env
```

**"Module not found" errors**
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**"Database locked" error**
```bash
# Solution: Close other connections or use a different database
# In .env, change to:
DATABASE_URL=sqlite:///commissions_new.db
```

**Port already in use**
```bash
# Solution: Use a different port
FLASK_PORT=8000 python run.py
```

**Tests failing**
```bash
# Solution: Ensure you're in the project root and venv is activated
cd CharneyCommisionTracker
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pytest
```

## 📁 Project Structure

```
CharneyCommisionTracker/
├── src/                    # Source code
│   ├── api/               # Flask API
│   ├── database/          # Database models & repository
│   ├── models/            # Pydantic validation models
│   └── parsers/           # Email parsing logic
├── config/                # Configuration
├── tests/                 # Test suite
├── examples/              # Usage examples
├── logs/                  # Application logs
├── requirements.txt       # Dependencies
├── run.py                # Quick start script
└── README.txt            # Full documentation
```

## 🔗 Important Files

- **README.txt**: Complete documentation
- **PROJECT_SUMMARY.md**: Project overview and achievements
- **QUICK_REFERENCE.md**: This file
- **.env.example**: Environment variables template
- **run.py**: Application entry point
- **examples/sample_usage.py**: Code examples

## 📞 Getting Help

1. **Setup Issues**: Check README.txt
2. **API Usage**: See API documentation in README.txt
3. **Code Examples**: Review examples/sample_usage.py
4. **Test Examples**: Look at test files in tests/
5. **Logs**: Check logs/app.log for errors

## 🎯 Next Steps

1. **Test the API**: Use curl commands above
2. **Run Examples**: `python examples/sample_usage.py`
3. **Run Tests**: `pytest`
4. **Parse Real Emails**: Configure IMAP and process emails
5. **Build Dashboard**: Use API to create frontend

---

**Quick Links**
- API Base: http://localhost:5000/api/v1
- Health Check: http://localhost:5000/api/v1/health
- Documentation: README.txt
- Examples: examples/sample_usage.py

