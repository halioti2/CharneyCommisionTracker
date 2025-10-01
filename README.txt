# Charney Commission Tracker

**AI-Powered Email-to-Database Pipeline for Real Estate Commission Tracking**

## 🎯 Project Overview

The Charney Commission Tracker is an automated system that transforms manual commission tracking into a streamlined, AI-powered process. It extracts structured data from commission emails, applies business rules, and provides real-time financial insights.

### Key Features

- **AI-Powered Email Parsing**: Uses OpenAI GPT-4 to extract commission data from unstructured emails
- **n8n Integration**: Visual workflow automation for email processing (recommended)
- **Structured Data Storage**: SQLite database with comprehensive schema for commissions and splits
- **REST API**: Flask-based API for integration with dashboards and other systems
- **Data Validation**: Pydantic models ensure data integrity and consistency
- **Flexible Email Processing**: Use n8n (recommended) or built-in IMAP processor
- **Agent Tracking**: Track individual agent commissions and generate summaries

### Technology Stack

- **Backend**: Python 3.8+
- **Web Framework**: Flask 3.0
- **Database**: SQLite (easily upgradeable to PostgreSQL)
- **AI/ML**: OpenAI GPT-4
- **Automation**: n8n (recommended for email processing)
- **Data Validation**: Pydantic
- **Testing**: Pytest
- **ORM**: SQLAlchemy

## 📁 Project Structure

```
CharneyCommisionTracker/
├── src/
│   ├── api/
│   │   └── app.py              # Flask API application
│   ├── database/
│   │   ├── models.py           # SQLAlchemy database models
│   │   └── repository.py       # Data access layer
│   ├── models/
│   │   └── commission.py       # Pydantic validation models
│   └── parsers/
│       ├── email_parser.py     # AI email parser
│       └── email_processor.py  # IMAP email processor (optional)
├── config/
│   └── config.py               # Configuration management
├── docs/
│   ├── N8N_INTEGRATION_GUIDE.md    # n8n setup guide (recommended)
│   └── N8N_DECISION_GUIDE.md       # Why use n8n
├── n8n-workflows/
│   ├── commission-email-parser.json # Ready-to-use n8n workflow
│   └── README.md                    # n8n workflow documentation
├── tests/
│   ├── test_models.py          # Model validation tests
│   ├── test_repository.py      # Database tests
│   └── test_api.py             # API endpoint tests
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
└── README.txt                  # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- n8n (recommended for email processing) - See installation below
- Git (for version control)

### Installation

1. **Clone the repository** (if using Git):
   ```bash
   git clone <repository-url>
   cd CharneyCommisionTracker
   ```

2. **Create and activate virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   # Copy the example file
   copy .env.example .env

   # Edit .env and add your OpenAI API key
   # OPENAI_API_KEY=your-api-key-here
   ```

5. **Initialize the database**:
   ```bash
   python -c "from src.database.models import DatabaseManager; DatabaseManager().create_tables()"
   ```

6. **Run the application**:
   ```bash
   python src/api/app.py
   ```

The API will be available at `http://localhost:5000/api/v1`

### Email Processing Setup (Recommended: n8n)

**Option A: n8n (Recommended)** - Visual workflow automation

1. **Install n8n**:
   ```bash
   npx n8n
   # Opens at http://localhost:5678
   ```

2. **Import workflow**:
   - Open n8n at http://localhost:5678
   - Import `n8n-workflows/commission-email-parser.json`
   - Configure email credentials
   - Activate workflow

3. **Complete guide**: See `docs/N8N_INTEGRATION_GUIDE.md`

**Option B: Built-in IMAP Processor** - Code-based automation

1. Configure email settings in `.env`:
   ```
   EMAIL_HOST=imap.gmail.com
   EMAIL_PORT=993
   EMAIL_USERNAME=your-email@example.com
   EMAIL_PASSWORD=your-password
   ```

2. Run the processor:
   ```python
   from src.parsers.email_processor import EmailProcessor
   processor = EmailProcessor()
   processor.connect()
   processor.process_new_emails()
   ```

**Why n8n?** See `docs/N8N_DECISION_GUIDE.md` for comparison and benefits.

## 📚 API Documentation

### Base URL
```
http://localhost:5000/api/v1
```

### Endpoints

#### Health Check
```
GET /health
```
Returns application health status.

**Response:**
```json
{
  "status": "healthy",
  "app": "Charney Commission Tracker",
  "version": "0.1.0",
  "environment": "development",
  "parser_available": true
}
```

#### Parse Email
```
POST /parse
```
Parse commission data from email content.

**Request Body:**
```json
{
  "email_content": "Commission Statement\nTransaction: TXN-2024-001...",
  "email_subject": "Commission Statement",
  "email_source": "escrow@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "transaction_id": "TXN-2024-001",
    "property_address": "123 Main St",
    "sale_amount": 450000.00,
    "commission_rate": 0.06,
    "total_commission": 27000.00,
    "splits": [...]
  },
  "validation": {
    "valid": true,
    "confidence_score": 0.95
  }
}
```

#### Get All Commissions
```
GET /commissions?status=verified&limit=50&offset=0
```
Query commissions with optional filters.

**Query Parameters:**
- `start_date`: Filter by closing date (ISO format)
- `end_date`: Filter by closing date (ISO format)
- `status`: Filter by status (pending, verified, paid, disputed)
- `agent_name`: Filter by agent name
- `min_amount`: Minimum commission amount
- `max_amount`: Maximum commission amount
- `limit`: Maximum results (default: 100)
- `offset`: Pagination offset (default: 0)

#### Get Single Commission
```
GET /commissions/{id}
```
Get a specific commission by ID.

#### Update Commission Status
```
PATCH /commissions/{id}/status
```
Update the status of a commission.

**Request Body:**
```json
{
  "status": "verified",
  "notes": "Approved by manager"
}
```

#### Get Agent Commissions
```
GET /agents/{agent_name}/commissions
```
Get all commissions for a specific agent.

#### Get Agent Summary
```
GET /agents/summary
```
Get total commissions grouped by agent.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "agent_name": "John Smith",
      "total_amount": 50000.00,
      "transaction_count": 5
    }
  ]
}
```

#### Delete Commission
```
DELETE /commissions/{id}
```
Delete a commission record.

## 🗄️ Database Schema

### Commissions Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| transaction_id | String(100) | Unique transaction identifier |
| property_address | String(500) | Property address |
| sale_amount | Numeric(12,2) | Sale price |
| commission_rate | Float | Commission rate (0.06 = 6%) |
| total_commission | Numeric(10,2) | Total commission amount |
| closing_date | DateTime | Transaction closing date |
| email_source | String(255) | Source email address |
| email_subject | String(500) | Email subject line |
| raw_email_content | Text | Full email content (audit trail) |
| confidence_score | Float | AI parsing confidence (0.0-1.0) |
| created_at | DateTime | Record creation timestamp |
| updated_at | DateTime | Last update timestamp |
| status | String(50) | Status (pending, verified, paid, disputed) |
| notes | Text | Additional notes |

### Commission Splits Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| commission_id | Integer | Foreign key to commissions |
| agent_name | String(255) | Agent name |
| agent_email | String(255) | Agent email |
| agent_id | String(100) | Internal agent ID |
| percentage | Float | Split percentage (0.60 = 60%) |
| amount | Numeric(10,2) | Split dollar amount |
| role | String(100) | Agent role (listing, buyer, referral) |
| notes | Text | Additional notes |

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_models.py

# Run specific test
pytest tests/test_models.py::TestCommissionData::test_valid_commission
```

## 🔧 Configuration

All configuration is managed through environment variables. See `.env.example` for all available options.

### Key Configuration Options

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `DATABASE_URL`: Database connection string (default: sqlite:///commissions.db)
- `FLASK_PORT`: API server port (default: 5000)
- `DEBUG`: Enable debug mode (default: False)
- `MIN_CONFIDENCE_SCORE`: Minimum acceptable confidence score (default: 0.5)

## 📧 Email Processing

To enable automated email processing:

1. Configure email settings in `.env`:
   ```
   EMAIL_HOST=imap.gmail.com
   EMAIL_PORT=993
   EMAIL_USERNAME=your-email@example.com
   EMAIL_PASSWORD=your-app-password
   ```

2. Run the email processor:
   ```python
   from src.parsers.email_processor import EmailProcessor
   from config.config import config

   processor = EmailProcessor(
       host=config.EMAIL_HOST,
       port=config.EMAIL_PORT,
       username=config.EMAIL_USERNAME,
       password=config.EMAIL_PASSWORD,
       api_key=config.OPENAI_API_KEY
   )

   results = processor.process_new_emails()
   print(f"Processed {results['processed']} emails")
   ```

## 🚢 Deployment

### Local Development
```bash
python src/api/app.py
```

### Production Deployment

1. **Set production environment variables**:
   ```
   ENVIRONMENT=production
   DEBUG=False
   SECRET_KEY=<strong-random-key>
   ```

2. **Use a production WSGI server** (e.g., Gunicorn):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 src.api.app:app
   ```

3. **Consider upgrading to PostgreSQL**:
   ```
   DATABASE_URL=postgresql://user:password@localhost/commissions
   ```

4. **Set up reverse proxy** (e.g., Nginx) for SSL and load balancing

## 🔒 Security Considerations

- Store API keys in environment variables, never in code
- Use strong SECRET_KEY in production
- Enable HTTPS in production
- Implement rate limiting for API endpoints
- Regularly update dependencies
- Validate and sanitize all input data

## 📊 Monitoring and Logging

Logs are written to:
- Console (stdout)
- File: `logs/app.log` (if configured)

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

Configure logging in `.env`:
```
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Ensure all tests pass
5. Submit a pull request

## 📝 License

[Add your license information here]

## 🆘 Support

For issues or questions:
- Check the documentation
- Review test files for usage examples
- Contact the development team

## 🎯 Roadmap

### Phase 1 (Current - 2 Week Sprint)
- ✅ Email parsing with AI
- ✅ Database schema and models
- ✅ REST API endpoints
- ✅ Unit tests
- ✅ Documentation

### Phase 2 (Future)
- Dashboard UI
- Advanced reporting
- Email notifications
- Multi-user support
- Role-based access control
- Audit logging
- Export functionality (PDF, Excel)

## 📞 Contact

[Add contact information here]
