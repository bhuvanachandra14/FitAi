import sqlite3

def check_db():
    try:
        conn = sqlite3.connect('faces.db')
        cursor = conn.cursor()
        
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables:", tables)
        
        # Check messages table
        cursor.execute("PRAGMA table_info(messages);")
        columns = cursor.fetchall()
        print("Messages Columns:", columns)
        
        conn.close()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    check_db()
