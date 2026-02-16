import os
import sys

# Add the root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app import app, db

def init_db():
    print("Initializing Database...")
    with app.app_context():
        try:
            # Create tables
            db.create_all()
            print("Database tables created successfully!")
            
            # Verify tables exist (optional but good for debugging)
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tables in database: {tables}")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            sys.exit(1)

if __name__ == "__main__":
    init_db()
