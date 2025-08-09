#!/usr/bin/env python3
"""
Enhanced Personal Expense Tracker - Python Backend
Advanced Flask API with multiple configuration options
"""

import os
import sys
import sqlite3
import json
import argparse
from datetime import datetime, date
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

# ===== CONFIGURATION CLASS =====
class AppConfig:
    """Application configuration management"""
    
    def __init__(self):
        # Default configuration
        self.HOST = os.getenv('HOST', '0.0.0.0')
        self.PORT = int(os.getenv('PORT', 5000))
        self.DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
        self.DATABASE_NAME = os.getenv('DATABASE_NAME', 'expense_tracker.db')
        self.API_PREFIX = os.getenv('API_PREFIX', '/api')
        self.CORS_ENABLED = os.getenv('CORS_ENABLED', 'True').lower() == 'true'
        
        # Advanced settings
        self.MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size
        self.JSON_SORT_KEYS = False
        self.JSONIFY_PRETTYPRINT_REGULAR = True
        
        # Security settings
        self.SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
        
        # Database settings
        self.DB_TIMEOUT = 30.0  # SQLite timeout in seconds
        self.DB_CHECK_SAME_THREAD = False
        
    def from_file(self, config_file):
        """Load configuration from file"""
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                for key, value in config_data.items():
                    if hasattr(self, key.upper()):
                        setattr(self, key.upper(), value)
    
    def to_dict(self):
        """Convert configuration to dictionary"""
        return {key: value for key, value in self.__dict__.items() if not key.startswith('_')}

# ===== INITIALIZE CONFIGURATION =====
config = AppConfig()

# Load configuration from file if exists
if os.path.exists('config.json'):
    config.from_file('config.json')

# ===== FLASK APP INITIALIZATION =====
app = Flask(__name__)
app.config.update(config.to_dict())

# Enable CORS if configured
if config.CORS_ENABLED:
    CORS(app, resources={
        f"{config.API_PREFIX}/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

# ===== ENHANCED EXPENSE TRACKER CLASS =====
class EnhancedExpenseTracker:
    """Enhanced expense tracker with advanced features"""
    
    def __init__(self, db_name=None):
        self.db_name = db_name or config.DATABASE_NAME
        self.setup_database()
    
    def get_connection(self):
        """Get database connection with proper configuration"""
        conn = sqlite3.connect(
            self.db_name,
            timeout=config.DB_TIMEOUT,
            check_same_thread=config.DB_CHECK_SAME_THREAD
        )
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def setup_database(self):
        """Create database and tables with enhanced schema"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Main transactions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
                        amount REAL NOT NULL CHECK (amount > 0),
                        category TEXT NOT NULL,
                        description TEXT NOT NULL,
                        date TEXT NOT NULL,
                        timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Categories table for dynamic categories
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
                        color TEXT DEFAULT '#007bff',
                        icon TEXT DEFAULT '💰',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Settings table for app configuration
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Performance indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp)')
                
                # Insert default categories if they don't exist
                self._insert_default_categories(cursor)
                
                # Insert default settings
                self._insert_default_settings(cursor)
                
                conn.commit()
                print(f"✅ Database setup completed: {self.db_name}")
                
        except sqlite3.Error as e:
            print(f"❌ Database setup error: {e}")
            raise
    
    def _insert_default_categories(self, cursor):
        """Insert default categories"""
        default_categories = [
            # Income categories
            ('Salary', 'income', '#28a745', '💰'),
            ('Freelance', 'income', '#17a2b8', '💻'),
            ('Business', 'income', '#6f42c1', '🏢'),
            ('Investment', 'income', '#fd7e14', '📈'),
            ('Gift', 'income', '#e83e8c', '🎁'),
            ('Bonus', 'income', '#20c997', '🎉'),
            ('Other Income', 'income', '#6c757d', '💵'),
            
            # Expense categories
            ('Food & Dining', 'expense', '#dc3545', '🍽️'),
            ('Transportation', 'expense', '#ffc107', '🚗'),
            ('Housing', 'expense', '#795548', '🏠'),
            ('Utilities', 'expense', '#607d8b', '⚡'),
            ('Healthcare', 'expense', '#f44336', '🏥'),
            ('Entertainment', 'expense', '#9c27b0', '🎬'),
            ('Shopping', 'expense', '#ff9800', '🛍️'),
            ('Education', 'expense', '#3f51b5', '📚'),
            ('Other Expense', 'expense', '#757575', '💸')
        ]
        
        for name, type_val, color, icon in default_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO categories (name, type, color, icon)
                VALUES (?, ?, ?, ?)
            ''', (name, type_val, color, icon))
    
    def _insert_default_settings(self, cursor):
        """Insert default application settings"""
        default_settings = [
            ('app_version', '2.0.0'),
            ('currency', 'USD'),
            ('date_format', 'YYYY-MM-DD'),
            ('theme', 'light'),
            ('auto_backup', 'true'),
            ('backup_frequency', 'weekly')
        ]
        
        for key, value in default_settings:
            cursor.execute('''
                INSERT OR IGNORE INTO settings (key, value)
                VALUES (?, ?)
            ''', (key, value))
    
    def add_transaction(self, transaction_data):
        """Add transaction with enhanced validation"""
        try:
            # Validate required fields
            required_fields = ['type', 'amount', 'category', 'description', 'date']
            for field in required_fields:
                if field not in transaction_data or not transaction_data[field]:
                    raise ValueError(f"Missing required field: {field}")
            
            # Enhanced validation
            if transaction_data['type'] not in ['income', 'expense']:
                raise ValueError("Transaction type must be 'income' or 'expense'")
            
            amount = float(transaction_data['amount'])
            if amount <= 0:
                raise ValueError("Amount must be greater than zero")
            
            # Validate date format
            try:
                datetime.strptime(transaction_data['date'], '%Y-%m-%d')
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
            
            # Insert transaction
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO transactions (type, amount, category, description, date, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    transaction_data['type'],
                    amount,
                    transaction_data['category'].strip(),
                    transaction_data['description'].strip(),
                    transaction_data['date'],
                    datetime.now().isoformat()
                ))
                
                transaction_id = cursor.lastrowid
                conn.commit()
                
                print(f"✅ Transaction added: ID {transaction_id}")
                return transaction_id
                
        except (sqlite3.Error, ValueError) as e:
            print(f"❌ Error adding transaction: {e}")
            raise
    
    def get_all_transactions(self, filters=None, limit=None, offset=None):
        """Get transactions with enhanced filtering and pagination"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build query
                query = '''
                    SELECT id, type, amount, category, description, date, timestamp,
                           created_at, updated_at
                    FROM transactions
                '''
                params = []
                conditions = []
                
                # Apply filters
                if filters:
                    if filters.get('type') and filters['type'] != 'all':
                        conditions.append('type = ?')
                        params.append(filters['type'])
                    
                    if filters.get('category') and filters['category'] != 'all':
                        conditions.append('category = ?')
                        params.append(filters['category'])
                    
                    if filters.get('month'):
                        conditions.append("strftime('%Y-%m', date) = ?")
                        params.append(filters['month'])
                    
                    if filters.get('start_date'):
                        conditions.append('date >= ?')
                        params.append(filters['start_date'])
                    
                    if filters.get('end_date'):
                        conditions.append('date <= ?')
                        params.append(filters['end_date'])
                    
                    if filters.get('min_amount'):
                        conditions.append('amount >= ?')
                        params.append(float(filters['min_amount']))
                    
                    if filters.get('max_amount'):
                        conditions.append('amount <= ?')
                        params.append(float(filters['max_amount']))
                    
                    if filters.get('search'):
                        conditions.append('(description LIKE ? OR category LIKE ?)')
                        search_term = f"%{filters['search']}%"
                        params.extend([search_term, search_term])
                
                # Add WHERE clause
                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)
                
                # Add ordering
                query += ' ORDER BY date DESC, timestamp DESC'
                
                # Add pagination
                if limit:
                    query += ' LIMIT ?'
                    params.append(limit)
                    
                    if offset:
                        query += ' OFFSET ?'
                        params.append(offset)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                transactions = []
                for row in rows:
                    transactions.append(dict(row))
                
                return transactions
                
        except sqlite3.Error as e:
            print(f"❌ Error fetching transactions: {e}")
            raise
    
    def get_categories(self):
        """Get all categories with enhanced information"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT name, type, color, icon, created_at
                    FROM categories
                    ORDER BY type, name
                ''')
                rows = cursor.fetchall()
                
                categories = {
                    'income': [],
                    'expense': []
                }
                
                for row in rows:
                    category_data = dict(row)
                    category_type = category_data.pop('type')
                    categories[category_type].append(category_data)
                
                return categories
                
        except sqlite3.Error as e:
            print(f"❌ Error fetching categories: {e}")
            raise
    
    def get_statistics(self, filters=None):
        """Get enhanced statistics"""
        try:
            transactions = self.get_all_transactions(filters)
            
            # Basic totals
            total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
            total_expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')
            balance = total_income - total_expenses
            
            # Category breakdown
            income_by_category = {}
            expense_by_category = {}
            
            for t in transactions:
                if t['type'] == 'income':
                    income_by_category[t['category']] = income_by_category.get(t['category'], 0) + t['amount']
                else:
                    expense_by_category[t['category']] = expense_by_category.get(t['category'], 0) + t['amount']
            
            # Monthly breakdown
            monthly_data = {}
            for t in transactions:
                month = t['date'][:7]  # YYYY-MM
                if month not in monthly_data:
                    monthly_data[month] = {'income': 0, 'expense': 0}
                monthly_data[month][t['type']] += t['amount']
            
            return {
                'total_income': round(total_income, 2),
                'total_expenses': round(total_expenses, 2),
                'balance': round(balance, 2),
                'transaction_count': len(transactions),
                'income_by_category': income_by_category,
                'expense_by_category': expense_by_category,
                'monthly_breakdown': monthly_data,
                'average_transaction': round(sum(t['amount'] for t in transactions) / len(transactions), 2) if transactions else 0
            }
            
        except Exception as e:
            print(f"❌ Error calculating statistics: {e}")
            raise
    
    def delete_transaction(self, transaction_id):
        """Delete transaction with enhanced error handling"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
                
                if cursor.rowcount == 0:
                    raise ValueError(f"Transaction with ID {transaction_id} not found")
                
                conn.commit()
                print(f"✅ Transaction {transaction_id} deleted")
                return True
                
        except (sqlite3.Error, ValueError) as e:
            print(f"❌ Error deleting transaction: {e}")
            raise

# ===== INITIALIZE EXPENSE TRACKER =====
expense_tracker = EnhancedExpenseTracker()

# ===== ENHANCED API ROUTES =====

@app.route('/')
def index():
    """Enhanced API documentation"""
    api_docs = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enhanced Personal Expense Tracker API</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; line-height: 1.6; background: #f8f9fa; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
            .status {{ background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 5px solid #28a745; }}
            .endpoint {{ background: #f8f9fa; padding: 15px; margin: 15px 0; border-left: 4px solid #007bff; border-radius: 5px; }}
            .method {{ font-weight: bold; color: #007bff; font-size: 1.1em; }}
            .config {{ background: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
            .card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #6c757d; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Enhanced Personal Expense Tracker API</h1>
            
            <div class="status">
                <strong>✅ API Status:</strong> Running successfully!<br>
                <strong>🐍 Python Version:</strong> {sys.version.split()[0]}<br>
                <strong>🗄️ Database:</strong> {config.DATABASE_NAME}<br>
                <strong>🌐 Host:</strong> {config.HOST}:{config.PORT}<br>
                <strong>🔧 Debug Mode:</strong> {config.DEBUG}
            </div>
            
            <div class="card">
                <h3>🎯 Quick Test</h3>
                <p>Test the API with these URLs:</p>
                <ul>
                    <li><a href="{config.API_PREFIX}/transactions" target="_blank">View Transactions</a></li>
                    <li><a href="{config.API_PREFIX}/categories" target="_blank">View Categories</a></li>
                    <li><a href="{config.API_PREFIX}/statistics" target="_blank">View Statistics</a></li>
                </ul>
            </div>
            
            <h2>📡 Available Endpoints</h2>
            
            <div class="grid">
                <div class="endpoint">
                    <div class="method">GET {config.API_PREFIX}/transactions</div>
                    <p><strong>Get all transactions</strong></p>
                    <p>Query parameters: type, category, month, start_date, end_date, min_amount, max_amount, search, limit, offset</p>
                </div>
                
                <div class="endpoint">
                    <div class="method">POST {config.API_PREFIX}/transactions</div>
                    <p><strong>Add a new transaction</strong></p>
                    <p>Required: type, amount, category, description, date</p>
                </div>
                
                <div class="endpoint">
                    <div class="method">DELETE {config.API_PREFIX}/transactions/&lt;id&gt;</div>
                    <p><strong>Delete a transaction</strong></p>
                    <p>Removes transaction by ID</p>
                </div>
                
                <div class="endpoint">
                    <div class="method">GET {config.API_PREFIX}/statistics</div>
                    <p><strong>Get financial statistics</strong></p>
                    <p>Includes totals, category breakdown, monthly data</p>
                </div>
                
                <div class="endpoint">
                    <div class="method">GET {config.API_PREFIX}/categories</div>
                    <p><strong>Get all categories</strong></p>
                    <p>Returns categorized list with colors and icons</p>
                </div>
                
                <div class="endpoint">
                    <div class="method">GET {config.API_PREFIX}/export</div>
                    <p><strong>Export all data</strong></p>
                    <p>Downloads complete data as JSON</p>
                </div>
            </div>
            
            <div class="config">
                <h3>🔧 Configuration</h3>
                <p>This API supports multiple configuration methods:</p>
                <ul>
                    <li><strong>Environment Variables:</strong> Set HOST, PORT, DEBUG, etc.</li>
                    <li><strong>Config File:</strong> Create config.json in the same directory</li>
                    <li><strong>Command Line:</strong> Use --port, --host, --debug flags</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(api_docs)

@app.route(f'{config.API_PREFIX}/transactions', methods=['GET'])
def get_transactions():
    """Get transactions with enhanced filtering"""
    try:
        # Parse query parameters
        filters = {}
        for param in ['type', 'category', 'month', 'start_date', 'end_date', 'min_amount', 'max_amount', 'search']:
            value = request.args.get(param)
            if value:
                filters[param] = value
        
        # Pagination parameters
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int, default=0)
        
        transactions = expense_tracker.get_all_transactions(filters, limit, offset)
        
        return jsonify({
            'success': True,
            'data': transactions,
            'count': len(transactions),
            'filters_applied': filters,
            'pagination': {
                'limit': limit,
                'offset': offset
            } if limit else None
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route(f'{config.API_PREFIX}/transactions', methods=['POST'])
def add_transaction():
    """Add new transaction with enhanced validation"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        transaction_id = expense_tracker.add_transaction(data)
        
        return jsonify({
            'success': True,
            'message': 'Transaction added successfully',
            'transaction_id': transaction_id,
            'data': data
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route(f'{config.API_PREFIX}/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """Delete transaction with enhanced error handling"""
    try:
        expense_tracker.delete_transaction(transaction_id)
        
        return jsonify({
            'success': True,
            'message': f'Transaction {transaction_id} deleted successfully'
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route(f'{config.API_PREFIX}/statistics', methods=['GET'])
def get_statistics():
    """Get enhanced financial statistics"""
    try:
        # Parse filter parameters
        filters = {}
        for param in ['type', 'category', 'month', 'start_date', 'end_date']:
            value = request.args.get(param)
            if value:
                filters[param] = value
        
        stats = expense_tracker.get_statistics(filters)
        
        return jsonify({
            'success': True,
            'data': stats,
            'filters_applied': filters
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route(f'{config.API_PREFIX}/categories', methods=['GET'])
def get_categories():
    """Get all categories with enhanced information"""
    try:
        categories = expense_tracker.get_categories()
        
        return jsonify({
            'success': True,
            'data': categories
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route(f'{config.API_PREFIX}/export', methods=['GET'])
def export_data():
    """Export all data with enhanced format"""
    try:
        transactions = expense_tracker.get_all_transactions()
        categories = expense_tracker.get_categories()
        stats = expense_tracker.get_statistics()
        
        export_data = {
            'export_info': {
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0',
                'total_transactions': len(transactions)
            },
            'transactions': transactions,
            'categories': categories,
            'statistics': stats
        }
        
        return app.response_class(
            json.dumps(export_data, indent=2, default=str),
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment; filename=expense_tracker_export.json'}
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route(f'{config.API_PREFIX}/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        with expense_tracker.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM transactions')
            transaction_count = cursor.fetchone()[0]
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'database': 'connected',
            'transaction_count': transaction_count,
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route(f'{config.API_PREFIX}/config', methods=['GET'])
def get_config():
    """Get current configuration (non-sensitive data only)"""
    safe_config = {
        'api_prefix': config.API_PREFIX,
        'cors_enabled': config.CORS_ENABLED,
        'database_name': config.DATABASE_NAME,
        'debug': config.DEBUG,
        'host': config.HOST,
        'port': config.PORT,
        'version': '2.0.0'
    }
    
    return jsonify({
        'success': True,
        'data': safe_config
    })

# ===== ERROR HANDLERS =====
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'available_endpoints': [
            f'{config.API_PREFIX}/transactions',
            f'{config.API_PREFIX}/statistics',
            f'{config.API_PREFIX}/categories',
            f'{config.API_PREFIX}/export',
            f'{config.API_PREFIX}/health',
            f'{config.API_PREFIX}/config'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request'
    }), 400

# ===== COMMAND LINE ARGUMENT PARSER =====
def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Enhanced Personal Expense Tracker API')
    
    parser.add_argument('--host', type=str, default=config.HOST,
                        help=f'Host to bind to (default: {config.HOST})')
    parser.add_argument('--port', type=int, default=config.PORT,
                        help=f'Port to bind to (default: {config.PORT})')
    parser.add_argument('--debug', action='store_true', default=config.DEBUG,
                        help='Enable debug mode')
    parser.add_argument('--no-debug', action='store_true',
                        help='Disable debug mode')
    parser.add_argument('--database', type=str, default=config.DATABASE_NAME,
                        help=f'Database file name (default: {config.DATABASE_NAME})')
    parser.add_argument('--config', type=str,
                        help='Load configuration from JSON file')
    parser.add_argument('--create-config', action='store_true',
                        help='Create a sample configuration file')
    
    return parser.parse_args()

def create_sample_config():
    """Create a sample configuration file"""
    sample_config = {
        "host": "0.0.0.0",
        "port": 5000,
        "debug": True,
        "database_name": "expense_tracker.db",
        "api_prefix": "/api",
        "cors_enabled": True
    }
    
    with open('config.json', 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print("✅ Sample configuration file created: config.json")
    print("💡 You can edit this file to customize your settings")

# ===== STARTUP FUNCTIONS =====
def print_startup_info():
    """Print startup information"""
    print("\n" + "="*60)
    print("🚀 Enhanced Personal Expense Tracker API")
    print("="*60)
    print(f"📊 Version: 2.0.0")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"🌐 Host: {config.HOST}")
    print(f"🔌 Port: {config.PORT}")
    print(f"🗄️ Database: {config.DATABASE_NAME}")
    print(f"🔧 Debug: {config.DEBUG}")
    print(f"🌍 CORS: {config.CORS_ENABLED}")
    print(f"📡 API Prefix: {config.API_PREFIX}")
    print("-" * 60)
    print(f"🔗 API Documentation: http://{config.HOST}:{config.PORT}/")
    print(f"🔗 Health Check: http://{config.HOST}:{config.PORT}{config.API_PREFIX}/health")
    print(f"🔗 Transactions: http://{config.HOST}:{config.PORT}{config.API_PREFIX}/transactions")
    print("-" * 60)
    print("✅ Server is ready to accept connections!")
    print("="*60 + "\n")

if __name__ == '__main__':
    # Parse command line arguments
    args = parse_arguments()
    
    # Handle special commands
    if args.create_config:
        create_sample_config()
        sys.exit(0)
    
    # Load custom configuration file if specified
    if args.config:
        config.from_file(args.config)
    
    # Override with command line arguments
    config.HOST = args.host
    config.PORT = args.port
    config.DATABASE_NAME = args.database
    
    if args.debug:
        config.DEBUG = True
    elif args.no_debug:
        config.DEBUG = False
    
    # Print startup information
    print_startup_info()
    
    # Run the Flask application
    try:
        app.run(
            debug=config.DEBUG,
            host=config.HOST,
            port=config.PORT,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)