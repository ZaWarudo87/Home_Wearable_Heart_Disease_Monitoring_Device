import sqlite3

conn = sqlite3.connect('data/data.db')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print("=== Tables ===")
print(tables)

# Show data from each table
for table in tables:
    print(f"\n=== {table} ===")
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    
    # Get column names
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Columns: {columns}")
    print(f"Rows: {len(rows)}")
    
    for row in rows[:10]:  # Show first 10 rows
        print(row)

conn.close()
