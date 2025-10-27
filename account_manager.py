import sqlite3
import uuid
import logging
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def create_account(name):
    try:
        # Connect to SQLite database (or create it if it doesn't exist)
        conn = sqlite3.connect('p2p_energy_trading.db')
        cursor = conn.cursor()

        # Create the accounts table if it doesn't exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
                        id TEXT PRIMARY KEY,
                        name TEXT UNIQUE,
                        public_key TEXT,
                        private_key TEXT,
                        balance REAL DEFAULT 0.0,
                        power_balance REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
        conn.commit()

        # Check if account name already exists
        cursor.execute("SELECT id FROM accounts WHERE name = ?", (name,))
        if cursor.fetchone():
            raise ValueError(f"Account with name '{name}' already exists")

        # Generate a random ID
        account_id = str(uuid.uuid4())

        # Generate a pair of RSA keys
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()

        # Serialize keys to store them as strings in the database
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        # Insert the new account into the database
        cursor.execute("INSERT INTO accounts (id, name, public_key, private_key, balance, power_balance) VALUES (?, ?, ?, ?, ?, ?)",
                       (account_id, name, public_key_pem, private_key_pem, 0.0, 0.0))
        conn.commit()

        return {"id": account_id, "name": name, "public_key": public_key_pem, "balance": 0.0, "power_balance": 0.0}
    
    except sqlite3.Error as e:
        logging.error(f"Database error in create_account: {e}")
        raise ValueError("Failed to create account")
    finally:
        # Close the database connection
        conn.close()

def get_account(name):
    try:
        # Connect to SQLite database
        conn = sqlite3.connect('p2p_energy_trading.db')
        cursor = conn.cursor()

        # First, let's check the table structure
        cursor.execute("PRAGMA table_info(accounts)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"DEBUG: Account table columns: {columns}")

        cursor.execute("SELECT * FROM accounts WHERE name = ?", (name,))
        account = cursor.fetchone()
        if account:
            print(f"DEBUG: Raw account data: {account}")
            # Create account dictionary with proper type conversion
            account_dict = {
                "id": account[0],
                "name": account[1],
                "public_key": account[2],
                "balance": float(account[4]) if account[4] is not None else 0.0,
                "power_balance": float(account[5]) if account[5] is not None else 0.0,
                "created_at": account[6]
            }
            print(f"DEBUG: Processed account data: {account_dict}")
            return account_dict
        else:
            return None
        
    except sqlite3.Error as e:
        logging.error(f"Database error in get_account: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error in get_account: {e}")
        print(f"ERROR: {str(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        return None
    finally:
        # Close the database connection
        conn.close()

def update_balance(name, amount):
    try:
        conn = sqlite3.connect('p2p_energy_trading.db')
        cursor = conn.cursor()
        
        # Get current balance
        cursor.execute("SELECT balance FROM accounts WHERE name = ?", (name,))
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"Account {name} not found")
            
        current_balance = float(result[0]) if result[0] is not None else 0.0
        new_balance = current_balance + float(amount)
        
        if new_balance < 0:
            raise ValueError(f"Insufficient balance for account {name}")
            
        # Update balance
        cursor.execute("UPDATE accounts SET balance = ? WHERE name = ?", (new_balance, name))
        conn.commit()
        
        return new_balance
        
    except sqlite3.Error as e:
        logging.error(f"Database error in update_balance: {e}")
        raise ValueError("Failed to update balance")
    finally:
        conn.close()

def update_power_balance(name, amount):
    try:
        conn = sqlite3.connect('p2p_energy_trading.db')
        cursor = conn.cursor()
        
        # Get current power balance
        cursor.execute("SELECT power_balance FROM accounts WHERE name = ?", (name,))
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"Account {name} not found")
            
        current_power_balance = float(result[0]) if result[0] is not None else 0.0
        new_power_balance = current_power_balance + float(amount)
        
        if new_power_balance < 0:
            raise ValueError(f"Insufficient power balance for account {name}")
            
        # Update power balance
        cursor.execute("UPDATE accounts SET power_balance = ? WHERE name = ?", (new_power_balance, name))
        conn.commit()
        
        return new_power_balance
        
    except sqlite3.Error as e:
        logging.error(f"Database error in update_power_balance: {e}")
        raise ValueError("Failed to update power balance")
    finally:
        conn.close()

def migrate_database():
    try:
        conn = sqlite3.connect('p2p_energy_trading.db')
        cursor = conn.cursor()
        
        # Check if power_balance column exists
        cursor.execute("PRAGMA table_info(accounts)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'power_balance' not in columns:
            # Add power_balance column
            cursor.execute("ALTER TABLE accounts ADD COLUMN power_balance REAL DEFAULT 0.0")
            conn.commit()
            logging.info("Added power_balance column to accounts table")
            
        conn.close()
        return True
    except sqlite3.Error as e:
        logging.error(f"Database migration error: {e}")
        return False

def get_all_accounts():
    try:
        # Ensure database is migrated
        migrate_database()
        
        conn = sqlite3.connect('p2p_energy_trading.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, balance, power_balance, created_at FROM accounts")
        accounts = cursor.fetchall()
        
        return [{
            "id": account[0],
            "name": account[1],
            "balance": float(account[2]) if account[2] is not None else 0.0,
            "power_balance": float(account[3]) if account[3] is not None else 0.0,
            "created_at": account[4]
        } for account in accounts]
        
    except sqlite3.Error as e:
        logging.error(f"Database error in get_all_accounts: {e}")
        return []
    finally:
        conn.close()