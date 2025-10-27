import json
import hashlib
import sqlite3
from datetime import datetime
from uuid import uuid4
from urllib.parse import urlparse
from flask import Flask, jsonify, request
import logging
import requests
import random
import string

# Initialize the SQLite database
conn = sqlite3.connect('p2p_energy_trading.db', check_same_thread=False)
cursor = conn.cursor()

# Create tables for blocks, transactions, and blockchain logs
create_tables = '''
CREATE TABLE IF NOT EXISTS Blockchain (
    block_id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_index INTEGER,
    timestamp TEXT,
    proof INTEGER,
    previous_hash TEXT,
    block_hash TEXT
);
'''

create_transactions_table = '''
CREATE TABLE IF NOT EXISTS Transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_id INTEGER,
    Seller TEXT,
    Buyer TEXT,
    Power REAL,
    Price REAL,
    transaction_timestamp TEXT
);
'''

create_logs_table = '''
CREATE TABLE IF NOT EXISTS BlockchainLogs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    operation_type TEXT,
    details TEXT
);
'''

cursor.execute(create_tables)
cursor.execute(create_transactions_table)
cursor.execute(create_logs_table)
conn.commit()

def migrate_transactions_table():
    try:
        # Check if transaction_timestamp column exists
        cursor.execute("PRAGMA table_info(Transactions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'transaction_timestamp' not in columns:
            # Add transaction_timestamp column
            cursor.execute("ALTER TABLE Transactions ADD COLUMN transaction_timestamp TEXT")
            # Update existing records with current timestamp
            cursor.execute("UPDATE Transactions SET transaction_timestamp = ? WHERE transaction_timestamp IS NULL", 
                         (str(datetime.now()),))
            conn.commit()
            print("Added transaction_timestamp column to Transactions table")
    except sqlite3.Error as e:
        print(f"Error migrating transactions table: {e}")

# Run migration
migrate_transactions_table()

# Now that tables are created, we can add the block_hash column if needed
def add_block_hash_column():
    cursor.execute("PRAGMA table_info(Blockchain);")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'block_hash' not in columns:
        cursor.execute("ALTER TABLE Blockchain ADD COLUMN block_hash TEXT;")
        conn.commit()
        print("Added 'block_hash' column to the Blockchain table.")

add_block_hash_column()

# Helper function to log changes in the BlockchainLogs table
def log_change(operation_type, details):
    try:
        with sqlite3.connect('p2p_energy_trading.db', timeout=10, check_same_thread=False) as conn:
            cursor = conn.cursor()
            timestamp = str(datetime.now())
            
            print(f"DEBUG: Processing details for logging: {details}")
            print(f"DEBUG: Details type: {type(details)}")
            
            # Ensure details is a dictionary and handle each field appropriately
            if isinstance(details, dict):
                processed_details = {}
                for key, value in details.items():
                    print(f"DEBUG: Processing field {key} with value {value} of type {type(value)}")
                    try:
                        if key in ['Power', 'Price']:
                            try:
                                processed_details[key] = float(value)
                                print(f"DEBUG: Converted {key} to float: {processed_details[key]}")
                            except (ValueError, TypeError) as e:
                                print(f"DEBUG: Failed to convert {key} to float: {str(e)}")
                                processed_details[key] = value
                        elif key == 'transaction_timestamp':
                            processed_details[key] = str(value)
                            print(f"DEBUG: Set {key} as string: {processed_details[key]}")
                        else:
                            processed_details[key] = str(value)
                            print(f"DEBUG: Set {key} as string: {processed_details[key]}")
                    except Exception as e:
                        print(f"DEBUG: Error processing field {key}: {str(e)}")
                        processed_details[key] = str(value)
            else:
                print(f"DEBUG: Converting non-dict details to string: {details}")
                processed_details = str(details)
                
            print(f"DEBUG: Final processed details: {processed_details}")
            
            # Convert the processed details to JSON string
            try:
                details_json = json.dumps(processed_details)
                print(f"DEBUG: JSON conversion successful: {details_json}")
            except Exception as e:
                print(f"DEBUG: JSON conversion failed: {str(e)}")
                details_json = json.dumps(str(processed_details))
            
            cursor.execute('''INSERT INTO BlockchainLogs (timestamp, operation_type, details) 
                            VALUES (?, ?, ?)''', 
                        (timestamp, operation_type, details_json))
            conn.commit()
            print(f"[{timestamp}] {operation_type}: {processed_details}")
    except Exception as e:
        print(f"ERROR in log_change: {str(e)}")
        print(f"ERROR details: {type(e).__name__}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        # Don't raise the error, just log it
        pass

# Function to insert a block and associated transactions into the database
def insert_block_to_db(block, transactions):
    with sqlite3.connect('p2p_energy_trading.db', timeout=10, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO Blockchain (block_index, timestamp, proof, previous_hash, block_hash) 
                          VALUES (?, ?, ?, ?, ?)''', 
                       (block['index'], block['timestamp'], block['proof'], block['previous_hash'], block['block_hash']))
        conn.commit()
        block_id = cursor.lastrowid
        
        for tx in transactions:
            cursor.execute('''INSERT INTO Transactions (block_id, Seller, Buyer, Power, Price, transaction_timestamp) 
                              VALUES (?, ?, ?, ?, ?, ?)''', 
                           (block_id, 
                            str(tx['Seller']), 
                            str(tx['Buyer']), 
                            float(tx['Power']), 
                            float(tx['Price']),
                            tx.get('transaction_timestamp', str(datetime.now()))))
        conn.commit()
        return block_id

class Blockchain:
    def __init__(self, reset_chain=False):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        
        # Connect to database
        self.conn = sqlite3.connect('p2p_energy_trading.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        if reset_chain:
            self._reset_blockchain()
        else:
            self._load_blockchain()
            
        # If chain is empty, create genesis block
        if not self.chain:
            self.new_block(previous_hash='1', proof=1000)

    def _reset_blockchain(self):
        """Reset the blockchain and database"""
        self.cursor.execute("DELETE FROM Blockchain")
        self.cursor.execute("DELETE FROM Transactions")
        self.cursor.execute("DELETE FROM BlockchainLogs")
        self.conn.commit()
        self.chain = []
        self.current_transactions = []

    def _load_blockchain(self):
        """Load blockchain from database"""
        try:
            # Load blocks
            self.cursor.execute("SELECT * FROM Blockchain ORDER BY block_index")
            blocks = self.cursor.fetchall()
            
            for block in blocks:
                block_data = {
                    'index': block[1],
                    'timestamp': block[2],
                    'proof': block[3],
                    'previous_hash': block[4],
                    'block_hash': block[5],
                    'transactions': []
                }
                
                # Load transactions for this block
                self.cursor.execute("SELECT * FROM Transactions WHERE block_id = ?", (block[0],))
                transactions = self.cursor.fetchall()
                
                for tx in transactions:
                    # Handle both old and new transaction records
                    transaction = {
                        'Seller': str(tx[2]),
                        'Buyer': str(tx[3]),
                        'Power': float(tx[4]) if tx[4] is not None else 0.0,
                        'Price': float(tx[5]) if tx[5] is not None else 0.0
                    }
                    
                    # Add timestamp if it exists in the record
                    if len(tx) > 6 and tx[6] is not None:
                        transaction['transaction_timestamp'] = str(tx[6])
                    else:
                        transaction['transaction_timestamp'] = str(datetime.now())
                    
                    block_data['transactions'].append(transaction)
                
                self.chain.append(block_data)
            
            # Load pending transactions
            self.cursor.execute("SELECT * FROM Transactions WHERE block_id IS NULL")
            pending_txs = self.cursor.fetchall()
            for tx in pending_txs:
                transaction = {
                    'Seller': str(tx[2]),
                    'Buyer': str(tx[3]),
                    'Power': float(tx[4]) if tx[4] is not None else 0.0,
                    'Price': float(tx[5]) if tx[5] is not None else 0.0
                }
                
                # Add timestamp if it exists in the record
                if len(tx) > 6 and tx[6] is not None:
                    transaction['transaction_timestamp'] = str(tx[6])
                else:
                    transaction['transaction_timestamp'] = str(datetime.now())
                
                self.current_transactions.append(transaction)
                
        except sqlite3.Error as e:
            logging.error(f"Error loading blockchain: {e}")
            self._reset_blockchain()

    def new_block(self, proof, previous_hash=None):
        if previous_hash is None:
            previous_hash = self.hash(self.last_block) if self.chain else '1'
        
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.now()),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash,
        }
        
        block_hash = self.hash(block)
        block['block_hash'] = block_hash
        
        # Insert block into database
        self.cursor.execute('''INSERT INTO Blockchain 
                              (block_index, timestamp, proof, previous_hash, block_hash) 
                              VALUES (?, ?, ?, ?, ?)''',
                          (block['index'], block['timestamp'], block['proof'], 
                           block['previous_hash'], block_hash))
        block_id = self.cursor.lastrowid
        
        # Insert transactions
        for tx in self.current_transactions:
            self.cursor.execute('''INSERT INTO Transactions 
                                  (block_id, Seller, Buyer, Power, Price, transaction_timestamp) 
                                  VALUES (?, ?, ?, ?, ?, ?)''',
                              (block_id, 
                               str(tx['Seller']), 
                               str(tx['Buyer']), 
                               float(tx['Power']), 
                               float(tx['Price']),
                               tx.get('transaction_timestamp', str(datetime.now()))))
        
        self.conn.commit()
        
        # Reset current transactions
        self.current_transactions = []
        self.chain.append(block)
        
        return block

    def new_transaction_seller(self, Seller, Buyer, Power, Price):
        try:
            print(f"DEBUG: Starting new_transaction_seller with values:")
            print(f"DEBUG: Seller: {Seller} ({type(Seller)})")
            print(f"DEBUG: Buyer: {Buyer} ({type(Buyer)})")
            print(f"DEBUG: Power: {Power} ({type(Power)})")
            print(f"DEBUG: Price: {Price} ({type(Price)})")
            
            # Convert Power and Price to float to ensure numeric values
            try:
                power = float(Power)
                price = float(Price)
                print(f"DEBUG: Converted Power to float: {power}")
                print(f"DEBUG: Converted Price to float: {price}")
            except (ValueError, TypeError) as e:
                print(f"ERROR: Failed to convert Power/Price to float: {str(e)}")
                raise ValueError("Power and Price must be numeric values")
            
            # Create transaction object
            transaction = {
                'Seller': str(Seller),
                'Buyer': str(Buyer),
                'Power': power,
                'Price': price,
                'transaction_timestamp': str(datetime.now())
            }
            print(f"DEBUG: Created transaction object: {transaction}")
            
            # Add transaction to current transactions
            self.current_transactions.append(transaction)
            print(f"DEBUG: Added transaction to current_transactions")
            
            # Log the transaction with proper type handling
            try:
                print(f"DEBUG: Attempting to log transaction")
                log_change("New Transaction", {
                    'Seller': str(Seller),
                    'Buyer': str(Buyer),
                    'Power': power,
                    'Price': price,
                    'transaction_timestamp': str(datetime.now())
                })
                print(f"DEBUG: Transaction logged successfully")
            except Exception as e:
                print(f"WARNING: Failed to log transaction: {str(e)}")
                print(f"WARNING traceback: {traceback.format_exc()}")
                # Continue even if logging fails
            
            return self.last_block['index'] + 1
            
        except Exception as e:
            print(f"ERROR in new_transaction_seller: {str(e)}")
            print(f"ERROR details: {type(e).__name__}")
            print(f"ERROR traceback: {traceback.format_exc()}")
            raise
    
    def validate_chain(self):
        # Validate the blockchain by checking hash links between blocks
        for i in range(1, len(self.chain)):
            previous_block = self.chain[i - 1]
            current_block = self.chain[i]
            #current_block['previous_hash'] = previous_block['block_hash']
            if current_block['previous_hash'] != previous_block['block_hash']:
                print(f"Validation failed: {current_block['previous_hash']} != {previous_block['block_hash']}")
                return False
            
            if not self.valid_proof(previous_block['proof'], current_block['proof']):
                print(f"Proof of work validation failed for block {current_block['index']}")
                return False

        return True
    
    @property
    def last_block(self):
        # Returns the last block in the chain
        return self.chain[-1]
    @staticmethod
    def hash(block):
        # Create a copy of the block without the block_hash field
        block_copy = block.copy()
        if 'block_hash' in block_copy:
            del block_copy['block_hash']
        # Hash a block to generate a unique identifier
        block_string = json.dumps(block_copy, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
   
    @staticmethod
    def valid_proof(last_proof, proof):
        # Check if the proof of work is valid
        this_proof = f'{proof}{last_proof}'.encode()
        this_proof_hash = hashlib.sha256(this_proof).hexdigest()
        return this_proof_hash[:4] == '0000'

    def proof_of_work(self, last_proof):
        # Proof of work algorithm
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof
    
    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
    
    def resolve_conflicts(self):
        neighbours = self.nodes.copy()
        max_length = len(self.chain)
        new_chain = None
        
        for node in neighbours:
            try:
                response = requests.get(f'http://{node}/chain').json()
                length = response['length']
                chain = response['chain']
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
            except requests.exceptions.RequestException as e:
                print(f"Error connecting to node {node}: {e}")

        if new_chain:
            self.chain = new_chain
            log_change("Chain Replaced", {"new_length": len(self.chain)})
            return True
        return False

    def __del__(self):
        """Cleanup database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()