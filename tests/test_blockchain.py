"""
Unit tests for the Blockchain module.
Tests core blockchain functionality including block creation, validation, and transactions.
"""

import unittest
import sys
import os
import tempfile
import shutil
import sqlite3
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from Blockchain import Blockchain, log_change
import account_manager

def create_test_tables():
    """Helper function to create database tables for testing"""
    conn = sqlite3.connect('p2p_energy_trading.db')
    cursor = conn.cursor()
    
    # Create Blockchain table
    cursor.execute('''CREATE TABLE IF NOT EXISTS Blockchain (
        block_id INTEGER PRIMARY KEY AUTOINCREMENT,
        block_index INTEGER,
        timestamp TEXT,
        proof INTEGER,
        previous_hash TEXT,
        block_hash TEXT
    )''')
    
    # Create Transactions table
    cursor.execute('''CREATE TABLE IF NOT EXISTS Transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        block_id INTEGER,
        Seller TEXT,
        Buyer TEXT,
        Power REAL,
        Price REAL,
        transaction_timestamp TEXT
    )''')
    
    # Create BlockchainLogs table
    cursor.execute('''CREATE TABLE IF NOT EXISTS BlockchainLogs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        operation_type TEXT,
        details TEXT
    )''')
    
    conn.commit()
    conn.close()


class TestBlockchain(unittest.TestCase):
    """Test suite for Blockchain class"""
    
    def setUp(self):
        """Set up test fixtures with a temporary database"""
        # Create temporary directory for test database
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create tables manually
        create_test_tables()
        
        # Now initialize blockchain
        self.blockchain = Blockchain(reset_chain=True)
        
    def tearDown(self):
        """Clean up test fixtures"""
        if hasattr(self, 'blockchain'):
            self.blockchain.conn.close()
        if hasattr(self, 'original_dir'):
            os.chdir(self.original_dir)
        if hasattr(self, 'test_dir'):
            try:
                shutil.rmtree(self.test_dir)
            except PermissionError:
                # Windows file handle timing issue - ignore cleanup errors
                pass
    
    def test_genesis_block_creation(self):
        """Test that genesis block is created on initialization"""
        self.assertEqual(len(self.blockchain.chain), 1)
        self.assertEqual(self.blockchain.chain[0]['index'], 1)
        self.assertEqual(self.blockchain.chain[0]['previous_hash'], '1')
        self.assertIn('transactions', self.blockchain.chain[0])
        self.assertIn('timestamp', self.blockchain.chain[0])
        self.assertIn('proof', self.blockchain.chain[0])
    
    def test_block_mining(self):
        """Test that a new block can be mined"""
        last_block = self.blockchain.last_block
        last_proof = last_block['proof']
        
        # Mine a new block
        proof = self.blockchain.proof_of_work(last_proof)
        previous_hash = self.blockchain.hash(last_block)
        new_block = self.blockchain.new_block(proof, previous_hash)
        
        # Verify the new block
        self.assertEqual(len(self.blockchain.chain), 2)
        self.assertEqual(new_block['index'], 2)
        self.assertEqual(new_block['previous_hash'], previous_hash)
        self.assertIn('block_hash', new_block)
        self.assertIsInstance(new_block['transactions'], list)
    
    def test_transaction_added(self):
        """Test that transactions are added to pending transactions"""
        # Add a transaction
        self.blockchain.new_transaction_seller("Alice", "Bob", 10.0, 0.001)
        
        # Verify transaction is pending
        self.assertEqual(len(self.blockchain.current_transactions), 1)
        self.assertEqual(self.blockchain.current_transactions[0]['Seller'], "Alice")
        self.assertEqual(self.blockchain.current_transactions[0]['Buyer'], "Bob")
        self.assertEqual(self.blockchain.current_transactions[0]['Power'], 10.0)
        self.assertEqual(self.blockchain.current_transactions[0]['Price'], 0.001)
    
    def test_proof_of_work(self):
        """Test that proof of work generates valid proofs"""
        last_block = self.blockchain.last_block
        last_proof = last_block['proof']
        
        # Generate proof
        proof = self.blockchain.proof_of_work(last_proof)
        
        # Verify proof is valid
        self.assertTrue(Blockchain.valid_proof(last_proof, proof))
        
        # Verify proof produces hash starting with 0000
        proof_hash = f'{proof}{last_proof}'.encode()
        this_proof_hash = __import__('hashlib').sha256(proof_hash).hexdigest()
        self.assertEqual(this_proof_hash[:4], '0000')
    
    def test_blockchain_validation_valid_chain(self):
        """Test validation of a valid blockchain"""
        # Mine two more blocks
        last_block = self.blockchain.last_block
        last_proof = last_block['proof']
        proof = self.blockchain.proof_of_work(last_proof)
        previous_hash = self.blockchain.hash(last_block)
        self.blockchain.new_block(proof, previous_hash)
        
        # Validate the chain
        self.assertTrue(self.blockchain.validate_chain())
    
    def test_block_hash_calculation(self):
        """Test that block hashes are calculated correctly"""
        block = self.blockchain.last_block
        calculated_hash = self.blockchain.hash(block)
        
        # Hash should be a valid SHA256 hex string
        self.assertEqual(len(calculated_hash), 64)
        self.assertIsInstance(calculated_hash, str)
    
    def test_multiple_transactions(self):
        """Test adding multiple transactions"""
        # Add multiple transactions
        self.blockchain.new_transaction_seller("Alice", "Bob", 10.0, 0.001)
        self.blockchain.new_transaction_seller("Charlie", "David", 20.0, 0.002)
        self.blockchain.new_transaction_seller("Eve", "Frank", 15.0, 0.0015)
        
        # Verify all transactions are pending
        self.assertEqual(len(self.blockchain.current_transactions), 3)
    
    def test_node_registration(self):
        """Test node registration"""
        self.blockchain.register_node("http://localhost:5000")
        self.blockchain.register_node("http://localhost:5001")
        
        # Verify nodes are registered
        self.assertIn("localhost:5000", self.blockchain.nodes)
        self.assertIn("localhost:5001", self.blockchain.nodes)
        self.assertEqual(len(self.blockchain.nodes), 2)


class TestAccountManager(unittest.TestCase):
    """Test suite for Account Manager module"""
    
    def setUp(self):
        """Set up test fixtures with a temporary database"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
    def tearDown(self):
        """Clean up test fixtures"""
        if hasattr(self, 'original_dir'):
            os.chdir(self.original_dir)
        if hasattr(self, 'test_dir'):
            try:
                shutil.rmtree(self.test_dir)
            except PermissionError:
                # Windows file handle timing issue - ignore cleanup errors
                pass
    
    def test_account_creation(self):
        """Test creating a new account"""
        account = account_manager.create_account("TestUser")
        
        # Verify account details
        self.assertIsNotNone(account)
        self.assertEqual(account['name'], "TestUser")
        self.assertIn('id', account)
        self.assertIn('public_key', account)
        self.assertEqual(account['balance'], 0.0)
        self.assertEqual(account['power_balance'], 0.0)
    
    def test_account_creation_duplicate(self):
        """Test that duplicate account creation fails"""
        account_manager.create_account("TestUser")
        
        # Attempting to create duplicate should raise ValueError
        with self.assertRaises(ValueError):
            account_manager.create_account("TestUser")
    
    def test_get_account(self):
        """Test retrieving an account"""
        created_account = account_manager.create_account("TestUser")
        retrieved_account = account_manager.get_account("TestUser")
        
        # Verify retrieved account matches created account
        self.assertIsNotNone(retrieved_account)
        self.assertEqual(retrieved_account['name'], "TestUser")
        self.assertEqual(retrieved_account['id'], created_account['id'])
        self.assertEqual(retrieved_account['balance'], 0.0)
        self.assertEqual(retrieved_account['power_balance'], 0.0)
    
    def test_get_nonexistent_account(self):
        """Test retrieving a nonexistent account"""
        account = account_manager.get_account("NonExistentUser")
        self.assertIsNone(account)
    
    def test_update_balance(self):
        """Test updating account balance"""
        account_manager.create_account("TestUser")
        
        # Add balance
        new_balance = account_manager.update_balance("TestUser", 10.0)
        self.assertEqual(new_balance, 10.0)
        
        # Verify account balance
        account = account_manager.get_account("TestUser")
        self.assertEqual(account['balance'], 10.0)
        
        # Subtract balance
        new_balance = account_manager.update_balance("TestUser", -5.0)
        self.assertEqual(new_balance, 5.0)
        
        # Verify updated balance
        account = account_manager.get_account("TestUser")
        self.assertEqual(account['balance'], 5.0)
    
    def test_update_balance_insufficient_funds(self):
        """Test that insufficient balance raises error"""
        account_manager.create_account("TestUser")
        
        # Attempt to withdraw more than available
        with self.assertRaises(ValueError):
            account_manager.update_balance("TestUser", -10.0)
    
    def test_update_power_balance(self):
        """Test updating power balance"""
        account_manager.create_account("TestUser")
        
        # Add power
        new_power = account_manager.update_power_balance("TestUser", 100.0)
        self.assertEqual(new_power, 100.0)
        
        # Verify power balance
        account = account_manager.get_account("TestUser")
        self.assertEqual(account['power_balance'], 100.0)
        
        # Subtract power
        new_power = account_manager.update_power_balance("TestUser", -30.0)
        self.assertEqual(new_power, 70.0)
        
        # Verify updated power
        account = account_manager.get_account("TestUser")
        self.assertEqual(account['power_balance'], 70.0)
    
    def test_update_power_balance_insufficient(self):
        """Test that insufficient power raises error"""
        account_manager.create_account("TestUser")
        
        # Attempt to transfer more power than available
        with self.assertRaises(ValueError):
            account_manager.update_power_balance("TestUser", -10.0)
    
    def test_get_all_accounts(self):
        """Test retrieving all accounts"""
        account_manager.create_account("Alice")
        account_manager.create_account("Bob")
        account_manager.create_account("Charlie")
        
        all_accounts = account_manager.get_all_accounts()
        
        # Verify all accounts are retrieved
        self.assertEqual(len(all_accounts), 3)
        names = [account['name'] for account in all_accounts]
        self.assertIn("Alice", names)
        self.assertIn("Bob", names)
        self.assertIn("Charlie", names)


class TestTransactionFlow(unittest.TestCase):
    """Integration tests for complete transaction flow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create tables manually
        create_test_tables()
        
        # Now initialize blockchain
        self.blockchain = Blockchain(reset_chain=True)
        
    def tearDown(self):
        """Clean up test fixtures"""
        if hasattr(self, 'blockchain'):
            self.blockchain.conn.close()
        if hasattr(self, 'original_dir'):
            os.chdir(self.original_dir)
        if hasattr(self, 'test_dir'):
            try:
                shutil.rmtree(self.test_dir)
            except PermissionError:
                # Windows file handle timing issue - ignore cleanup errors
                pass
    
    def test_complete_transaction_flow(self):
        """Test the complete flow of creating accounts, trading, and mining"""
        # Create accounts
        alice = account_manager.create_account("Alice")
        bob = account_manager.create_account("Bob")
        
        # Fund accounts
        account_manager.update_balance("Alice", 10.0)
        account_manager.update_power_balance("Alice", 100.0)
        account_manager.update_balance("Bob", 10.0)  # Give Bob funds to buy power
        
        # Perform transaction
        power_amount = 50.0
        price = 0.001
        
        # Update balances
        account_manager.update_balance("Bob", -power_amount * price)
        account_manager.update_balance("Alice", power_amount * price)
        account_manager.update_power_balance("Alice", -power_amount)
        account_manager.update_power_balance("Bob", power_amount)
        
        # Add transaction to blockchain
        self.blockchain.new_transaction_seller("Alice", "Bob", power_amount, price)
        
        # Verify transaction in pending
        self.assertEqual(len(self.blockchain.current_transactions), 1)
        
        # Mine block
        last_block = self.blockchain.last_block
        proof = self.blockchain.proof_of_work(last_block['proof'])
        previous_hash = self.blockchain.hash(last_block)
        new_block = self.blockchain.new_block(proof, previous_hash)
        
        # Verify block contains transaction
        self.assertEqual(len(new_block['transactions']), 1)
        self.assertEqual(new_block['transactions'][0]['Seller'], "Alice")
        self.assertEqual(new_block['transactions'][0]['Buyer'], "Bob")
        
        # Verify blockchain is valid
        self.assertTrue(self.blockchain.validate_chain())


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestBlockchain))
    suite.addTests(loader.loadTestsFromTestCase(TestAccountManager))
    suite.addTests(loader.loadTestsFromTestCase(TestTransactionFlow))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)

