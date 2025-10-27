import sqlite3
import os
import time
import psutil

def kill_process_using_file(filepath):
    """Kill any process that's using the specified file"""
    for proc in psutil.process_iter(['pid', 'open_files']):
        try:
            for file in proc.open_files():
                if file.path == os.path.abspath(filepath):
                    print(f"Killing process {proc.pid} that's using the database")
                    proc.kill()
                    time.sleep(1)  # Wait for process to die
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

def reset_database():
    try:
        db_path = os.path.abspath('p2p_energy_trading.db')
        
        # Kill any process using the database file
        kill_process_using_file(db_path)
        
        # Try to close any existing connections
        try:
            conn = sqlite3.connect(db_path)
            conn.close()
        except:
            pass
        
        # Wait a moment to ensure connections are closed
        time.sleep(1)
        
        # Delete the database file
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print("Database file deleted.")
            except PermissionError:
                print("Could not delete database file. Please close any programs using it and try again.")
                return False
        
        # Wait a moment to ensure file is deleted
        time.sleep(1)
        
        # Recreate the database and tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Drop all existing tables if they exist
        cursor.execute("DROP TABLE IF EXISTS Blockchain")
        cursor.execute("DROP TABLE IF EXISTS Transactions")
        cursor.execute("DROP TABLE IF EXISTS BlockchainLogs")
        cursor.execute("DROP TABLE IF EXISTS accounts")
        
        # Create Blockchain table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Blockchain (
            block_id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_index INTEGER,
            timestamp TEXT,
            proof INTEGER,
            previous_hash TEXT,
            block_hash TEXT
        )''')
        
        # Create Transactions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_id INTEGER,
            Seller TEXT,
            Buyer TEXT,
            Power REAL,
            Price REAL
        )''')
        
        # Create BlockchainLogs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS BlockchainLogs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            operation_type TEXT,
            details TEXT
        )''')
        
        # Create accounts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE,
            public_key TEXT,
            private_key TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        conn.commit()
        conn.close()
        print("Database reset complete. All tables have been recreated.")
        return True
        
    except Exception as e:
        print(f"Error resetting database: {e}")
        return False

def clear_tables():
    """Clear all tables but keep the database structure"""
    try:
        conn = sqlite3.connect('p2p_energy_trading.db')
        cursor = conn.cursor()
        
        # Clear all tables
        cursor.execute("DELETE FROM Blockchain")
        cursor.execute("DELETE FROM Transactions")
        cursor.execute("DELETE FROM BlockchainLogs")
        cursor.execute("DELETE FROM accounts")
        
        # Reset auto-increment counters
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='Blockchain'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='Transactions'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='BlockchainLogs'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='accounts'")
        
        conn.commit()
        conn.close()
        print("All tables cleared successfully.")
        return True
    except Exception as e:
        print(f"Error clearing tables: {e}")
        return False

if __name__ == "__main__":
    # First reset the database completely
    if reset_database():
        print("Database reset successful.")
    else:
        print("Failed to reset database.") 