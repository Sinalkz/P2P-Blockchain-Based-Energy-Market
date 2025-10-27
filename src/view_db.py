import sqlite3
from tabulate import tabulate

def view_table(cursor, table_name):
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    if rows:
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in cursor.fetchall()]
        # Print table contents
        print(f"\n=== {table_name} Table ===")
        print(tabulate(rows, headers=columns, tablefmt='grid'))
    else:
        print(f"\n=== {table_name} Table is empty ===")

def main():
    # Connect to the database
    conn = sqlite3.connect('p2p_energy_trading.db')
    cursor = conn.cursor()

    # Get list of all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print("Available tables in the database:")
    for table in tables:
        print(f"- {table[0]}")
        view_table(cursor, table[0])

    conn.close()

if __name__ == "__main__":
    main() 