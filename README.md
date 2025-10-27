# P2P Blockchain-Based Energy Market Proof of Concept

A decentralized peer-to-peer energy trading platform built with blockchain technology, allowing users to trade energy (kWh) using cryptocurrency (ETH) in a secure, transparent, and automated marketplace.

## 🌟 Features

### Core Functionality
- **Blockchain-Based Trading**: Secure, immutable transactions recorded on a distributed ledger
- **Dual Balance System**: Manage both ETH (cryptocurrency) and Power (kWh) balances for each account
- **Automated Matching**: Buyer-seller transaction matching with automatic price averaging
- **Proof-of-Work Consensus**: Mining mechanism ensuring network security and transaction validation
- **Cryptographic Security**: RSA key pairs for each account ensuring secure transactions
- **Web Interface**: Modern, intuitive UI for interacting with the blockchain

### Account Management
- Create accounts with unique names and cryptographic keys
- Add/deposit ETH balance for purchasing energy
- Add/generate Power balance for selling energy
- View all accounts and their balances
- Transfer power between accounts

### Transaction System
- Role-based transactions (Buyer/Seller)
- Automatic buyer-seller matching
- Price negotiation through averaged pricing
- Real-time balance updates
- Transaction history logging

### Blockchain Features
- Genesis block creation
- Block mining with proof-of-work algorithm
- Hash-based chain validation
- Persistent storage in SQLite database
- Transaction logging and audit trail
- Chain integrity verification

## 🏗️ Architecture

### Components

**Blockchain.py** - Core blockchain implementation
- Block structure and validation
- Proof-of-work mining algorithm
- Hash generation and chain verification
- Database persistence and loading
- Transaction management

**account_manager.py** - Account and balance management
- RSA key pair generation
- Account creation and retrieval
- ETH balance management (add/withdraw)
- Power balance management (add/transfer)
- Database integration

**main.py** - Flask web server and API
- RESTful API endpoints
- Modern web interface (HTML/CSS/JavaScript)
- Transaction processing
- Block mining interface
- Account management UI

### Database Schema

**Accounts Table**
- `id` (TEXT PRIMARY KEY): Unique account identifier
- `name` (TEXT UNIQUE): Account name
- `public_key` (TEXT): RSA public key
- `private_key` (TEXT): RSA private key (encrypted)
- `balance` (REAL): ETH balance
- `power_balance` (REAL): Energy balance in kWh
- `created_at` (TIMESTAMP): Account creation timestamp

**Blockchain Table**
- `block_id` (INTEGER PRIMARY KEY): Database ID
- `block_index` (INTEGER): Block index in chain
- `timestamp` (TEXT): Block creation time
- `proof` (INTEGER): Proof-of-work value
- `previous_hash` (TEXT): Hash of previous block
- `block_hash` (TEXT): Current block hash

**Transactions Table**
- `transaction_id` (INTEGER PRIMARY KEY): Database ID
- `block_id` (INTEGER): Associated block
- `Seller` (TEXT): Seller account name
- `Buyer` (TEXT): Buyer account name
- `Power` (REAL): Amount of energy in kWh
- `Price` (REAL): Price per kWh in ETH
- `transaction_timestamp` (TEXT): Transaction timestamp

**BlockchainLogs Table**
- `log_id` (INTEGER PRIMARY KEY): Database ID
- `timestamp` (TEXT): Operation timestamp
- `operation_type` (TEXT): Type of operation
- `details` (TEXT): JSON-formatted operation details

## 📦 Installation

### Prerequisites
- Python 3.7+
- pip package manager

### Setup Steps

1. **Clone the repository**
```bash
git clone https://github.com/Sinalkz/P2P-Blockchain-Based-Energy-Market.git
cd P2P-Blockchain-Based-Energy-Market
```

2. **Create a virtual environment** (recommended)
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
cd src
python main.py
```

5. **Access the web interface**
Open your browser and navigate to: `http://localhost:5000`

### Command-Line Options

**Reset the blockchain** (start fresh):
```bash
python main.py --reset
```

**Clear all tables** (keep structure):
```bash
python main.py --clear
```

## 🚀 Usage Guide

### 1. Create Accounts
- Navigate to "Create Account" section
- Enter a unique account name
- Click "Create Account"
- Your account receives a unique ID and public key

### 2. Fund Your Account
- Go to "Account Balance Management" → "Add Balance"
- Enter your account name
- Specify the ETH amount to add
- Your ETH balance increases

### 3. Generate/Sell Power
- Go to "Power Balance Management" → "Add Power"
- Enter your account name
- Specify the amount of energy (kWh) to add
- Your power balance increases

### 4. Execute Energy Transaction
- Go to "Add Transaction"
- Enter sender (your account)
- Enter receiver (trading partner)
- Specify power amount (kWh)
- Set price per kWh (ETH/kWh)
- Select your role (Buyer or Seller)
- The system automatically:
  - Validates balances
  - Matches buyer with seller
  - Updates ETH and power balances
  - Records the transaction

### 5. Mine a Block
- After adding transactions, click "Mine Block"
- The system validates the proof-of-work
- Creates a new block with pending transactions
- Transactions are permanently recorded

### 6. View Blockchain
- Click "View Blockchain" to see:
  - All blocks in the chain
  - Block hashes and timestamps
  - Transactions within each block
  - Chain integrity

## 🔧 API Endpoints

### Account Management
- `POST /add_account` - Create a new account
  ```json
  {"name": "alice"}
  ```

- `GET /accounts` - Get all accounts

- `POST /add_balance` - Add ETH to account
  ```json
  {"account_name": "alice", "amount": 10.5}
  ```

- `POST /withdraw_balance` - Withdraw ETH from account
  ```json
  {"account_name": "alice", "amount": 2.0}
  ```

- `POST /add_power` - Add energy to account
  ```json
  {"account_name": "alice", "amount": 100.0}
  ```

- `POST /transfer_power` - Transfer energy between accounts
  ```json
  {"sender": "alice", "receiver": "bob", "amount": 50.0}
  ```

### Transaction Management
- `POST /add_transaction` - Create a new transaction
  ```json
  {
    "sender": "alice",
    "receiver": "bob",
    "power": 50.0,
    "price": 0.001,
    "role": "seller"
  }
  ```

- `GET /mine` - Mine a new block

- `GET /chain` - Get the full blockchain

### Network Management
- `POST /nodes/register` - Register a new node
  ```json
  {"nodes": ["http://192.168.0.5:5000"]}
  ```

- `GET /nodes/resolve` - Resolve chain conflicts

## 🔐 Security Features

- **RSA Cryptographic Keys**: Each account has a unique public-private key pair
- **Proof-of-Work**: Blocks require computational work to mine
- **Hash Chaining**: Each block is cryptographically linked to the previous one
- **Transaction Validation**: Automatic balance verification before transactions
- **Immutable Ledger**: Once recorded, transactions cannot be modified
- **Private Key Storage**: Keys stored securely in the database

## 📊 Workflow Example

```
1. Alice creates account → Gets RSA keys
2. Alice adds 10 ETH to her balance
3. Alice adds 100 kWh of power
4. Bob creates account
5. Bob adds 10 ETH to his balance
6. Alice initiates transaction: Sell 50 kWh at 0.002 ETH/kWh (Role: Seller)
7. Bob initiates transaction: Buy 50 kWh at 0.001 ETH/kWh (Role: Buyer)
8. System matches transactions (average price: 0.0015 ETH/kWh)
9. Updates balances:
   - Alice: ETH += 0.075, Power -= 50
   - Bob: ETH -= 0.075, Power += 50
10. Mine block → Transaction recorded in blockchain
11. View blockchain → See immutable transaction history
```

## 🛠️ Development

### Project Structure
```
blockchain/
├── src/
│   ├── main.py              # Flask server and web interface
│   ├── Blockchain.py         # Core blockchain implementation
│   ├── account_manager.py    # Account and balance management
│   ├── reset_db.py          # Database reset utilities
│   ├── setup.py             # Database setup
│   ├── view_db.py           # Database viewing utility
│   ├── test_interaction.py  # API endpoint tests
│   └── demo.ipynb          # Interactive demo notebook
├── tests/                   # Test suite
│   ├── test_blockchain.py   # Unit tests (Blockchain, Accounts)
│   ├── test_integration.py  # Integration tests
│   └── README.md            # Testing documentation
├── requirements.txt         # Python dependencies
├── LICENSE                  # License file
└── README.md               # This file
```

### Testing

**Run all tests:**
```bash
python -m unittest discover tests -v
```

**Run specific test suites:**
```bash
# Unit tests (Blockchain, Account Management)
python tests/test_blockchain.py

# Integration tests (Complete workflows)
python tests/test_integration.py
```

**Run specific test classes:**
```bash
python -m unittest tests.test_blockchain.TestBlockchain -v
python -m unittest tests.test_integration.TestIntegration -v
```

See `tests/README.md` for detailed testing documentation.

### Database Management

**Reset entire database:**
```bash
python reset_db.py
```

**View database contents:**
```bash
python view_db.py
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

**Sina Khozoei**
- GitHub: [@Sinalkz](https://github.com/Sinalkz)

## 🙏 Acknowledgments

- Built with Python, Flask, and SQLite
- Cryptography powered by the `cryptography` library
- Modern web interface with vanilla JavaScript

## 📚 Research Context

This project implements a peer-to-peer energy trading market using blockchain technology for a master's thesis on decentralized energy markets. The system demonstrates:

- Decentralized energy trading without intermediaries
- Automated market matching mechanisms
- Cryptographic security for energy transactions
- Transparent and immutable transaction records
- Scalable blockchain architecture for energy systems

---

For questions or support, please open an issue on GitHub.