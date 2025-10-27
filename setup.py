import sqlite3

# Create the database and tables
def setup_database():
    conn = sqlite3.connect('p2p_energy_trading.db')
    cursor = conn.cursor()

    # Create the Blockchain table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Blockchain (
        block_id INTEGER PRIMARY KEY AUTOINCREMENT,
        block_index INTEGER,
        timestamp TEXT,
        proof INTEGER,
        previous_hash TEXT,
        block_hash TEXT
    )
    ''')

    # Create the Transactions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        block_id INTEGER,
        Seller TEXT,
        Buyer TEXT,
        Power REAL,
        Price REAL
    )
    ''')

    # Create the BlockchainLogs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS BlockchainLogs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        operation_type TEXT,
        details TEXT
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()
    print("Database setup completed successfully!")