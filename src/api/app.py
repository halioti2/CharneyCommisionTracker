"""
Flask API Application for Commission Tracker.

This module provides REST API endpoints for:
- Parsing commission emails
- Querying commission data
- Managing commission records
"""

import logging
import sys
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.config import config
from src.database.models import DatabaseManager
from src.database.repository import CommissionRepository
from src.parsers.email_parser import AIEmailParser
from src.models.commission import EmailParseRequest, CommissionQueryParams


# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE) if config.LOG_FILE else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)


# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

# Enable CORS
CORS(app, origins=config.CORS_ORIGINS)

# Initialize database
db_manager = DatabaseManager(config.get_database_url())
db_manager.create_tables()
logger.info("Database tables created/verified")

# Initialize repository
repository = CommissionRepository(db_manager)

# Initialize parser
try:
    parser = AIEmailParser(api_key=config.OPENAI_API_KEY, model=config.OPENAI_MODEL)
    logger.info(f"AI Parser initialized with model: {config.OPENAI_MODEL}")
except Exception as e:
    logger.error(f"Failed to initialize AI Parser: {e}")
    parser = None


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found", "message": str(error)}), 404


@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request", "message": str(error)}), 400


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error", "message": "An unexpected error occurred"}), 500


# Health check endpoint
@app.route(f'{config.API_PREFIX}/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
        "environment": config.ENVIRONMENT,
        "parser_available": parser is not None
    })


# Configuration endpoint
@app.route(f'{config.API_PREFIX}/config', methods=['GET'])
def get_config():
    """Get current configuration (non-sensitive values)"""
    return jsonify(config.to_dict())


# Parse email endpoint
@app.route(f'{config.API_PREFIX}/parse', methods=['POST'])
def parse_email():
    """
    Parse commission data from email content.
    
    Request body:
    {
        "email_content": "raw email text",
        "email_subject": "optional subject",
        "email_source": "optional sender email"
    }
    
    Returns:
    {
        "success": true,
        "data": {...parsed commission data...},
        "validation": {...validation results...}
    }
    """
    if not parser:
        return jsonify({
            "success": False,
            "error": "Parser not initialized. Check OPENAI_API_KEY configuration."
        }), 500
    
    try:
        # Get request data
        data = request.get_json()
        if not data or 'email_content' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field: email_content"
            }), 400
        
        # Parse email
        logger.info("Parsing email content...")
        commission_data = parser.parse_commission_email(
            email_content=data['email_content'],
            email_subject=data.get('email_subject'),
            email_source=data.get('email_source')
        )
        
        # Validate extraction
        validation = parser.validate_extraction(commission_data)
        
        # Save to database
        logger.info(f"Saving commission data for transaction: {commission_data.transaction_id}")
        commission = repository.save_commission(commission_data)
        
        return jsonify({
            "success": True,
            "data": commission.to_dict(),
            "validation": validation,
            "message": "Commission data parsed and saved successfully"
        }), 201
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        return jsonify({
            "success": False,
            "error": "Validation error",
            "message": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error parsing email: {e}")
        return jsonify({
            "success": False,
            "error": "Parsing failed",
            "message": str(e)
        }), 500


# Get all commissions endpoint
@app.route(f'{config.API_PREFIX}/commissions', methods=['GET'])
def get_commissions():
    """
    Query commissions with optional filters.
    
    Query parameters:
    - start_date: Filter by closing date >= this date (ISO format)
    - end_date: Filter by closing date <= this date (ISO format)
    - status: Filter by status
    - agent_name: Filter by agent name
    - min_amount: Minimum commission amount
    - max_amount: Maximum commission amount
    - limit: Maximum number of results (default: 100)
    - offset: Number of results to skip (default: 0)
    
    Returns:
    {
        "success": true,
        "data": [...list of commissions...],
        "count": 10,
        "limit": 100,
        "offset": 0
    }
    """
    try:
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status = request.args.get('status')
        agent_name = request.args.get('agent_name')
        min_amount = request.args.get('min_amount')
        max_amount = request.args.get('max_amount')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Convert dates
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        if min_amount:
            min_amount = Decimal(min_amount)
        if max_amount:
            max_amount = Decimal(max_amount)
        
        # Query commissions
        commissions = repository.query_commissions(
            start_date=start_date,
            end_date=end_date,
            status=status,
            agent_name=agent_name,
            min_amount=min_amount,
            max_amount=max_amount,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            "success": True,
            "data": [c.to_dict() for c in commissions],
            "count": len(commissions),
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        logger.error(f"Error querying commissions: {e}")
        return jsonify({
            "success": False,
            "error": "Query failed",
            "message": str(e)
        }), 500


# Get single commission endpoint
@app.route(f'{config.API_PREFIX}/commissions/<int:commission_id>', methods=['GET'])
def get_commission(commission_id):
    """Get a single commission by ID"""
    try:
        commission = repository.get_commission_by_id(commission_id)
        if not commission:
            return jsonify({
                "success": False,
                "error": "Not found",
                "message": f"Commission with ID {commission_id} not found"
            }), 404
        
        return jsonify({
            "success": True,
            "data": commission.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting commission: {e}")
        return jsonify({
            "success": False,
            "error": "Query failed",
            "message": str(e)
        }), 500


# Update commission status endpoint
@app.route(f'{config.API_PREFIX}/commissions/<int:commission_id>/status', methods=['PATCH'])
def update_commission_status(commission_id):
    """
    Update commission status.
    
    Request body:
    {
        "status": "verified",
        "notes": "optional notes"
    }
    """
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field: status"
            }), 400
        
        success = repository.update_commission_status(
            commission_id=commission_id,
            status=data['status'],
            notes=data.get('notes')
        )
        
        if not success:
            return jsonify({
                "success": False,
                "error": "Not found",
                "message": f"Commission with ID {commission_id} not found"
            }), 404
        
        return jsonify({
            "success": True,
            "message": "Status updated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        return jsonify({
            "success": False,
            "error": "Update failed",
            "message": str(e)
        }), 500


# Get agent commissions endpoint
@app.route(f'{config.API_PREFIX}/agents/<agent_name>/commissions', methods=['GET'])
def get_agent_commissions(agent_name):
    """
    Get all commissions for a specific agent.

    Query parameters:
    - start_date: Filter by closing date >= this date
    - end_date: Filter by closing date <= this date
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)

        results = repository.get_agent_commissions(
            agent_name=agent_name,
            start_date=start_date,
            end_date=end_date
        )

        return jsonify({
            "success": True,
            "agent_name": agent_name,
            "data": results,
            "count": len(results)
        })

    except Exception as e:
        logger.error(f"Error getting agent commissions: {e}")
        return jsonify({
            "success": False,
            "error": "Query failed",
            "message": str(e)
        }), 500


# Get agent summary endpoint
@app.route(f'{config.API_PREFIX}/agents/summary', methods=['GET'])
def get_agent_summary():
    """
    Get summary of total commissions by agent.

    Query parameters:
    - start_date: Filter by closing date >= this date
    - end_date: Filter by closing date <= this date
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)

        summary = repository.get_total_commissions_by_agent(
            start_date=start_date,
            end_date=end_date
        )

        return jsonify({
            "success": True,
            "data": summary,
            "count": len(summary)
        })

    except Exception as e:
        logger.error(f"Error getting agent summary: {e}")
        return jsonify({
            "success": False,
            "error": "Query failed",
            "message": str(e)
        }), 500


# Delete commission endpoint
@app.route(f'{config.API_PREFIX}/commissions/<int:commission_id>', methods=['DELETE'])
def delete_commission(commission_id):
    """Delete a commission record"""
    try:
        success = repository.delete_commission(commission_id)

        if not success:
            return jsonify({
                "success": False,
                "error": "Not found",
                "message": f"Commission with ID {commission_id} not found"
            }), 404

        return jsonify({
            "success": True,
            "message": "Commission deleted successfully"
        })

    except Exception as e:
        logger.error(f"Error deleting commission: {e}")
        return jsonify({
            "success": False,
            "error": "Delete failed",
            "message": str(e)
        }), 500


if __name__ == '__main__':
    # Validate configuration
    errors = config.validate()
    if errors:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)

    logger.info(f"Starting {config.APP_NAME} v{config.APP_VERSION}")
    logger.info(f"Environment: {config.ENVIRONMENT}")
    logger.info(f"API available at: http://{config.FLASK_HOST}:{config.FLASK_PORT}{config.API_PREFIX}")

    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.DEBUG
    )

