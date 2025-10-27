import account_manager
from Blockchain import Blockchain

# Create a test account
print("Creating test account...")
account = account_manager.create_account("TestUser")
print(f"Account created with ID: {account['id']}")

# Initialize blockchain
print("\nInitializing blockchain...")
blockchain = Blockchain()

# Add a test transaction
print("\nAdding test transaction...")
blockchain.new_transaction_seller(
    Seller="TestUser",
    Buyer="OtherUser",
    Power=100,
    Price=50
)

# Mine a new block
print("\nMining new block...")
last_block = blockchain.last_block
last_proof = last_block['proof']
proof = blockchain.proof_of_work(last_proof)
block = blockchain.new_block(proof)

print("\nBlockchain status:")
print(f"Number of blocks: {len(blockchain.chain)}")
print(f"Latest block: {block}")