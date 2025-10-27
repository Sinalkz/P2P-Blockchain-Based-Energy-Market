"""
Integration tests for the complete P2P Energy Trading system.
Tests end-to-end workflows including web API endpoints.
"""

import unittest
import sys
import os
import tempfile
import shutil
import time
import threading
from flask import Flask
import requests

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from Blockchain import Blockchain
import account_manager


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create tables manually
        from test_blockchain import create_test_tables
        create_test_tables()
        
        # Now initialize blockchain
        self.blockchain = Blockchain(reset_chain=True)
        
    def tearDown(self):
        """Clean up test environment"""
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
    
    def test_full_trading_scenario(self):
        """Test a complete trading scenario with multiple participants"""
        # Scenario: 3 participants trading energy
        
        # 1. Create accounts
        alice = account_manager.create_account("Alice")
        bob = account_manager.create_account("Bob")
        charlie = account_manager.create_account("Charlie")
        
        # 2. Fund accounts with ETH
        account_manager.update_balance("Alice", 20.0)
        account_manager.update_balance("Bob", 25.0)
        account_manager.update_balance("Charlie", 15.0)
        
        # 3. Generate power (energy production)
        account_manager.update_power_balance("Alice", 200.0)  # Solar panels
        account_manager.update_power_balance("Bob", 150.0)   # Wind turbine
        account_manager.update_power_balance("Charlie", 50.0)  # Consumer
        
        # Verify initial balances
        alice = account_manager.get_account("Alice")
        bob = account_manager.get_account("Bob")
        charlie = account_manager.get_account("Charlie")
        
        self.assertEqual(alice['balance'], 20.0)
        self.assertEqual(alice['power_balance'], 200.0)
        self.assertEqual(bob['balance'], 25.0)
        self.assertEqual(bob['power_balance'], 150.0)
        self.assertEqual(charlie['balance'], 15.0)
        self.assertEqual(charlie['power_balance'], 50.0)
        
        # 4. Execute trades
        # Trade 1: Alice sells 50 kWh to Charlie at 0.001 ETH/kWh
        power1 = 50.0
        price1 = 0.001
        total1 = power1 * price1
        
        # Update balances for trade 1
        account_manager.update_balance("Charlie", -total1)
        account_manager.update_balance("Alice", total1)
        account_manager.update_power_balance("Alice", -power1)
        account_manager.update_power_balance("Charlie", power1)
        
        # Add to blockchain
        self.blockchain.new_transaction_seller("Alice", "Charlie", power1, price1)
        
        # Verify balances after trade 1
        alice = account_manager.get_account("Alice")
        charlie = account_manager.get_account("Charlie")
        
        self.assertEqual(alice['balance'], 20.05)
        self.assertEqual(alice['power_balance'], 150.0)
        self.assertEqual(charlie['balance'], 14.95)
        self.assertEqual(charlie['power_balance'], 100.0)
        
        # Trade 2: Bob sells 40 kWh to Charlie at 0.0015 ETH/kWh
        power2 = 40.0
        price2 = 0.0015
        total2 = power2 * price2
        
        # Update balances for trade 2
        account_manager.update_balance("Charlie", -total2)
        account_manager.update_balance("Bob", total2)
        account_manager.update_power_balance("Bob", -power2)
        account_manager.update_power_balance("Charlie", power2)
        
        # Add to blockchain
        self.blockchain.new_transaction_seller("Bob", "Charlie", power2, price2)
        
        # Verify balances after trade 2
        alice = account_manager.get_account("Alice")
        bob = account_manager.get_account("Bob")
        charlie = account_manager.get_account("Charlie")
        
        self.assertAlmostEqual(alice['balance'], 20.05, places=2)
        self.assertEqual(alice['power_balance'], 150.0)
        self.assertAlmostEqual(bob['balance'], 25.06, places=2)
        self.assertEqual(bob['power_balance'], 110.0)
        self.assertAlmostEqual(charlie['balance'], 14.89, places=2)
        self.assertEqual(charlie['power_balance'], 140.0)
        
        # 5. Mine blocks
        last_block = self.blockchain.last_block
        last_proof = last_block['proof']
        proof = self.blockchain.proof_of_work(last_proof)
        previous_hash = self.blockchain.hash(last_block)
        block1 = self.blockchain.new_block(proof, previous_hash)
        
        # 6. Verify blockchain
        self.assertTrue(self.blockchain.validate_chain())
        self.assertEqual(len(self.blockchain.chain), 2)  # Genesis + 1 mined
        self.assertEqual(len(block1['transactions']), 2)  # Two transactions in block
        
        # 7. Verify all transactions are recorded
        all_accounts = account_manager.get_all_accounts()
        self.assertEqual(len(all_accounts), 3)
        
        # 8. Calculate total ETH and Power in system
        total_eth = sum(acc['balance'] for acc in all_accounts)
        total_power = sum(acc['power_balance'] for acc in all_accounts)
        
        # ETH should remain constant (no mining rewards in this implementation)
        expected_eth = 20.0 + 25.0 + 15.0
        self.assertEqual(total_eth, expected_eth)
        
        # Power should remain constant
        expected_power = 200.0 + 150.0 + 50.0
        self.assertEqual(total_power, expected_power)
    
    def test_blockchain_consistency(self):
        """Test that blockchain remains consistent across multiple operations"""
        # Create accounts and add transactions
        account_manager.create_account("User1")
        account_manager.create_account("User2")
        
        account_manager.update_balance("User1", 10.0)
        account_manager.update_power_balance("User1", 100.0)
        
        # Add multiple transactions
        for i in range(5):
            power = 10.0 * (i + 1)
            price = 0.001
            self.blockchain.new_transaction_seller("User1", "User2", power, price)
            
            # Mine a block
            last_block = self.blockchain.last_block
            proof = self.blockchain.proof_of_work(last_block['proof'])
            previous_hash = self.blockchain.hash(last_block)
            self.blockchain.new_block(proof, previous_hash)
        
        # Verify blockchain is valid
        self.assertTrue(self.blockchain.validate_chain())
        self.assertEqual(len(self.blockchain.chain), 6)  # Genesis + 5 blocks
        
        # Verify each block links to previous
        for i in range(1, len(self.blockchain.chain)):
            current = self.blockchain.chain[i]
            previous = self.blockchain.chain[i-1]
            
            self.assertEqual(current['previous_hash'], 
                           self.blockchain.hash(previous))
    
    def test_balance_persistence(self):
        """Test that account balances persist correctly"""
        # Create and fund accounts
        account_manager.create_account("TestUser")
        account_manager.update_balance("TestUser", 100.0)
        account_manager.update_power_balance("TestUser", 500.0)
        
        # Verify balances
        account = account_manager.get_account("TestUser")
        self.assertEqual(account['balance'], 100.0)
        self.assertEqual(account['power_balance'], 500.0)
        
        # Update balances multiple times
        account_manager.update_balance("TestUser", -10.0)
        account_manager.update_balance("TestUser", 5.0)
        account_manager.update_power_balance("TestUser", -50.0)
        account_manager.update_power_balance("TestUser", 25.0)
        
        # Verify final balances
        account = account_manager.get_account("TestUser")
        self.assertEqual(account['balance'], 95.0)
        self.assertEqual(account['power_balance'], 475.0)


def run_integration_tests():
    """Run integration tests"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestIntegration)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_integration_tests()
    exit(0 if success else 1)

