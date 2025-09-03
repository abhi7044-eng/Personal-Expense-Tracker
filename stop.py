#!/usr/bin/env python3
"""
Personal Expense Tracker - Python Backend
Simple Flask API for managing income and expense transactions
Uses SQLite database for persistent storage
"""

import sqlite3
import json
from datetime import datetime, date
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os

# Initialize Flask application
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for frontend

# Database configuration
DATABASE_NAME = 'expense_tracker.db'

class ExpenseTracker:
    """Main class for handling expense tracking operations"""
    
    def __init__(self, db_name=DATABASE_NAME):
        """Initialize the expense tracker with database setup"""
        self.db_name = db_name
        self.setup_database()
    
    def setup_database(self):
        """Create the database and transactions table if they don't exist"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Create transactions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
                        amount REAL NOT NULL CHECK (amount > 0),
                        category TEXT NOT NULL,
                        description TEXT NOT NULL,
                        date TEXT NOT NULL,
                        timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create index for better query performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_date ON transactions(date)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_type ON transactions(type)
                ''')
                
                conn.commit()
                print("Database setup completed successfully!")
                
        except sqlite3.Error as e:
            print(f"Database setup error: {e}")
            raise
    
    def add_transaction(self, transaction_data):
        """Add a new transaction to the database"""
        try:
            # Validate required fields
            required_fields = ['type', 'amount', 'category', 'description', 'date']
            for field in required_fields:
                if field not in transaction_data or not transaction_data[field]:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate transaction type
            if transaction_data['type'] not in ['income', 'expense']:
                raise ValueError("Transaction type must be 'income' or 'expense'")
            
            # Validate amount
            amount = float(transaction_data['amount'])
            if amount <= 0:
                raise ValueError("Amount must be greater than zero")
            
            # Validate date format
            try:
                datetime.strptime(transaction_data['date'], '%Y-%m-%d')
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
            
            # Insert transaction into database
            with sqlite3.connect(self.db_name) as conn:
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
                
                print(f"Transaction added successfully with ID: {transaction_id}")
                return transaction_id
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            raise
        except ValueError as e:
            print(f"Validation error: {e}")
            raise
    
    def get_all_transactions(self, filters=None):
        """Get all transactions with optional filtering"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Base query
                query = '''
                    SELECT id, type, amount, category, description, date, timestamp
                    FROM transactions
                '''
                params = []
                conditions = []
                
                # Apply filters if provided
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
                
                # Add WHERE clause if there are conditions
                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)
                
                # Order by date (newest first)
                query += ' ORDER BY date DESC, timestamp DESC'
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                transactions = []
                for row in rows:
                    transactions.append({
                        'id': row[0],
                        'type': row[1],
                        'amount': row[2],
                        'category': row[3],
                        'description': row[4],
                        'date': row[5],
                        'timestamp': row[6]
                    })
                
                return transactions
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            raise
    
    def get_transaction_by_id(self, transaction_id):
        """Get a specific transaction by its ID"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, type, amount, category, description, date, timestamp
                    FROM transactions WHERE id = ?
                ''', (transaction_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return {
                    'id': row[0],
                    'type': row[1],
                    'amount': row[2],
                    'category': row[3],
                    'description': row[4],
                    'date': row[5],
                    'timestamp': row[6]
                }
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            raise
    
    def update_transaction(self, transaction_id, updated_data):
        """Update an existing transaction"""
        try:
            # First check if transaction exists
            if not self.get_transaction_by_id(transaction_id):
                raise ValueError("Transaction not found")
            
            # Validate updated data
            if 'amount' in updated_data:
                amount = float(updated_data['amount'])
                if amount <= 0:
                    raise ValueError("Amount must be greater than zero")
            
            if 'type' in updated_data and updated_data['type'] not in ['income', 'expense']:
                raise ValueError("Transaction type must be 'income' or 'expense'")
            
            if 'date' in updated_data:
                try:
                    datetime.strptime(updated_data['date'], '%Y-%m-%d')
                except ValueError:
                    raise ValueError("Date must be in YYYY-MM-DD format")
            
            # Build update query dynamically
            update_fields = []
            params = []
            
            for field in ['type', 'amount', 'category', 'description', 'date']:
                if field in updated_data:
                    update_fields.append(f'{field} = ?')
                    params.append(updated_data[field])
            
            if not update_fields:
                raise ValueError("No valid fields to update")
            
            # Add timestamp update
            update_fields.append('timestamp = ?')
            params.append(datetime.now().isoformat())
            params.append(transaction_id)
            
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                query = f'''
                    UPDATE transactions 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                '''
                cursor.execute(query, params)
                conn.commit()
                
                if cursor.rowcount == 0:
                    raise ValueError("Transaction not found")
                
                print(f"Transaction {transaction_id} updated successfully")
                return True
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            raise
        except ValueError as e:
            print(f"Validation error: {e}")
            raise
    
    def delete_transaction(self, transaction_id):
        """Delete a transaction by its ID"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
                conn.commit()
                
                if cursor.rowcount == 0:
                    raise ValueError("Transaction not found")
                
                print(f"Transaction {transaction_id} deleted successfully")
                return True
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            raise
        except ValueError as e:
            print(f"Validation error: {e}")
            raise
    
    def get_summary(self, filters=None):
        """Get financial summary (total income, expenses, balance)"""
        try:
            transactions = self.get_all_transactions(filters)
            
            total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
            total_expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')
            balance = total_income - total_expenses
            
            return {
                'total_income': round(total_income, 2),
                'total_expenses': round(total_expenses, 2),
                'balance': round(balance, 2),
                'transaction_count': len(transactions)
            }
            
        except Exception as e:
            print(f"Error calculating summary: {e}")
            raise
    
    def get_categories(self):
        """Get all unique categories from transactions"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT category, type 
                    FROM transactions 
                    ORDER BY type, category
                ''')
                rows = cursor.fetchall()
                
                categories = {
                    'income': [],
                    'expense': []
                }
                
                for row in rows:
                    categories[row[1]].append(row[0])
                
                return categories
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            raise
    
    def export_data(self):
        """Export all transactions as JSON"""
        try:
            transactions = self.get_all_transactions()
            return json.dumps(transactions, indent=2, default=str)
        except Exception as e:
            print(f"Export error: {e}")
            raise
    
    def import_data(self, json_data):
        """Import transactions from JSON data"""
        try:
            transactions = json.loads(json_data)
            
            if not isinstance(transactions, list):
                raise ValueError("JSON data must be a list of transactions")
            
            imported_count = 0
            errors = []
            
            for i, transaction in enumerate(transactions):
                try:
                    # Remove ID if present (will be auto-generated)
                    if 'id' in transaction:
                        del transaction['id']
                    
                    self.add_transaction(transaction)
                    imported_count += 1
                except Exception as e:
                    errors.append(f"Transaction {i+1}: {e}")
            
            return {
                'imported_count': imported_count,
                'errors': errors,
                'success': len(errors) == 0
            }
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON data: {e}")
        except Exception as e:
            print(f"Import error: {e}")
            raise

# Initialize the expense tracker
expense_tracker = ExpenseTracker()

# API Routes

@app.route('/')
def index():
    """Serve a simple API documentation page"""
    api_docs = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Personal Expense Tracker API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            h1 { color: #333; }
            .endpoint { background: #f4f4f4; padding: 10px; margin: 10px 0; border-left: 4px solid #007cba; }
            .method { font-weight: bold; color: #007cba; }
        </style>
    </head>
    <body>
        <h1>Personal Expense Tracker API</h1>
        <p>Backend API for managing personal income and expenses</p>
        
        <h2>Available Endpoints:</h2>
        
        <div class="endpoint">
            <div class="method">GET /api/transactions</div>
            <p>Get all transactions with optional filtering</p>
            <p>Query parameters: type, category, month, start_date, end_date</p>
        </div>
        
        <div class="endpoint">
            <div class="method">POST /api/transactions</div>
            <p>Add a new transaction</p>
            <p>Required fields: type, amount, category, description, date</p>
        </div>
        
        <div class="endpoint">
            <div class="method">GET /api/transactions/&lt;id&gt;</div>
            <p>Get a specific transaction by ID</p>
        </div>
        
        <div class="endpoint">
            <div class="method">PUT /api/transactions/&lt;id&gt;</div>
            <p>Update a specific transaction</p>
        </div>
        
        <div class="endpoint">
            <div class="method">DELETE /api/transactions/&lt;id&gt;</div>
            <p>Delete a specific transaction</p>
        </div>
        
        <div class="endpoint">
            <div class="method">GET /api/summary</div>
            <p>Get financial summary (income, expenses, balance)</p>
        </div>
        
        <div class="endpoint">
            <div class="method">GET /api/categories</div>
            <p>Get all unique categories</p>
        </div>
        
        <div class="endpoint">
            <div class="method">GET /api/export</div>
            <p>Export all data as JSON</p>
        </div>
        
        <div class="endpoint">
            <div class="method">POST /api/import</div>
            <p>Import data from JSON</p>
        </div>
        
        <p><strong>Database:</strong> SQLite (expense_tracker.db)</p>
        <p><strong>Status:</strong> API is running successfully!</p>
    </body>
    </html>
    '''
    return render_template_string(api_docs)

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Get all transactions with optional filtering"""
    try:
        # Get query parameters for filtering
        filters = {
            'type': request.args.get('type'),
            'category': request.args.get('category'),
            'month': request.args.get('month'),
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date')
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        transactions = expense_tracker.get_all_transactions(filters)
        
        return jsonify({
            'success': True,
            'data': transactions,
            'count': len(transactions)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    """Add a new transaction"""
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
            'transaction_id': transaction_id
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

@app.route('/api/transactions/<int:transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    """Get a specific transaction by ID"""
    try:
        transaction = expense_tracker.get_transaction_by_id(transaction_id)
        
        if not transaction:
            return jsonify({
                'success': False,
                'error': 'Transaction not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': transaction
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/transactions/<int:transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    """Update a specific transaction"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        expense_tracker.update_transaction(transaction_id, data)
        
        return jsonify({
            'success': True,
            'message': 'Transaction updated successfully'
        })
        
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

@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """Delete a specific transaction"""
    try:
        expense_tracker.delete_transaction(transaction_id)
        
        return jsonify({
            'success': True,
            'message': 'Transaction deleted successfully'
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

@app.route('/api/summary', methods=['GET'])
def get_summary():
    """Get financial summary"""
    try:
        # Get query parameters for filtering
        filters = {
            'type': request.args.get('type'),
            'category': request.args.get('category'),
            'month': request.args.get('month'),
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date')
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        summary = expense_tracker.get_summary(filters)
        
        return jsonify({
            'success': True,
            'data': summary
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all unique categories"""
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

@app.route('/api/export', methods=['GET'])
def export_data():
    """Export all data as JSON"""
    try:
        json_data = expense_tracker.export_data()
        
        return app.response_class(
            json_data,
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment; filename=expense_tracker_export.json'}
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/import', methods=['POST'])
def import_data():
    """Import data from JSON"""
    try:
        data = request.get_json()
        
        if not data or 'json_data' not in data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        result = expense_tracker.import_data(data['json_data'])
        
        return jsonify({
            'success': result['success'],
            'message': f"Imported {result['imported_count']} transactions",
            'imported_count': result['imported_count'],
            'errors': result['errors']
        })
        
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

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    print("Starting Personal Expense Tracker API...")
    print(f"Database: {DATABASE_NAME}")
    print("API Documentation: http://127.0.0.1:5501/index.html")
    print("API Base URL: http://localhost:5000/api")
    
    # Run the Flask application
    app.run(debug=True, host='https://abhi7044-eng.github.io/Personal-Expense-Tracker/', port=5000)