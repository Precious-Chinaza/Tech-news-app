from backend.app import app, db
from sqlalchemy import text

def update_schema():
    with app.app_context():
        print("Starting schema update...")
        try:
            # Use raw SQL to add the column safely
            db.session.execute(text("ALTER TABLE cached_articles ADD COLUMN IF NOT EXISTS debate_script TEXT;"))
            db.session.commit()
            print("Successfully added 'debate_script' column to 'cached_articles' table.")
        except Exception as e:
            db.session.rollback()
            print(f"Error updating schema: {e}")

if __name__ == "__main__":
    update_schema()
