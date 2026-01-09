import sqlite3
import os

DB_PATH = 'instance/pokemon.db'
if not os.path.exists(DB_PATH):
    DB_PATH = 'pokemon.db' # Try root if instance not found

def migrate():
    print(f"Migrating database at {DB_PATH}...")
    
    if not os.path.exists(DB_PATH):
        print("Database not found. Skipping migration (will be created by app).")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Add columns to users table
    columns_to_add = [
        ('level', 'INTEGER DEFAULT 1'),
        ('exp', 'INTEGER DEFAULT 0'),
        ('current_streak', 'INTEGER DEFAULT 0'),
        ('last_streak_update', 'DATETIME')
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            print(f"Added column: {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Column {col_name} already exists.")
            else:
                print(f"Error adding {col_name}: {e}")
                
    # 2. Check if Badges table exists (let app.py handle creation via db.create_all, 
    # but we can force it here if we imported app/db. Simpler to let app handle new tables)
    
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == '__main__':
    migrate()
