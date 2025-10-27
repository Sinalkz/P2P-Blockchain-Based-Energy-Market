import requests
import json

BASE_URL = "http://localhost:5000"

def print_response(response):
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
    print("-" * 50)

def main():
    # 1. Create two accounts
    print("Creating accounts...")
    alice = requests.post(f"{BASE_URL}/add_account", json={"name": "Alice"})
    print_response(alice)
    
    bob = requests.post(f"{BASE_URL}/add_account", json={"name": "Bob"})
    print_response(bob)

    # 2. Add a transaction
    print("\nAdding a transaction...")
    transaction = {
        "sender": "Alice",
        "receiver": "Bob",
        "power": 100,
        "price": 50,
        "role": "seller"
    }
    tx_response = requests.post(f"{BASE_URL}/add_transaction", json=transaction)
    print_response(tx_response)

    # 3. Mine a new block
    print("\nMining a new block...")
    mine_response = requests.get(f"{BASE_URL}/mine")
    print_response(mine_response)

    # 4. View the blockchain
    print("\nViewing the blockchain...")
    chain_response = requests.get(f"{BASE_URL}/chain")
    print_response(chain_response)

if __name__ == "__main__":
    main() 