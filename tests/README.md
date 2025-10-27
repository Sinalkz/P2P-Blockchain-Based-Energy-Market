# Tests

This directory contains test suites for the P2P Blockchain-Based Energy Market system.

## Test Files

### test_blockchain.py
Unit tests for the core blockchain functionality:
- Genesis block creation
- Block mining and validation
- Transaction handling
- Proof-of-work algorithm
- Blockchain validation
- Node registration

### test_integration.py
Integration tests for complete workflows:
- Full trading scenarios with multiple participants
- End-to-end transaction flows
- Blockchain consistency checks
- Balance persistence

## Running Tests

### Run All Tests
```bash
python -m unittest discover tests -v
```

### Run Specific Test File
```bash
python tests/test_blockchain.py
python tests/test_integration.py
```

### Run Specific Test Class
```bash
python -m unittest tests.test_blockchain.TestBlockchain -v
python -m unittest tests.test_integration.TestIntegration -v
```

### Run Specific Test Method
```bash
python -m unittest tests.test_blockchain.TestBlockchain.test_genesis_block_creation -v
```

## Test Coverage

The tests cover:

1. **Blockchain Core**
   - ✅ Genesis block creation
   - ✅ Block mining with proof-of-work
   - ✅ Transaction addition and processing
   - ✅ Blockchain validation
   - ✅ Hash calculation
   - ✅ Node registration

2. **Account Management**
   - ✅ Account creation and retrieval
   - ✅ ETH balance management
   - ✅ Power balance management
   - ✅ Balance validation
   - ✅ Duplicate account prevention

3. **Transaction Flow**
   - ✅ Complete trading scenarios
   - ✅ Multi-participant transactions
   - ✅ Balance persistence
   - ✅ Transaction recording

4. **Integration**
   - ✅ End-to-end workflows
   - ✅ Blockchain consistency
   - ✅ Multiple block mining
   - ✅ Chain validation

## Requirements

Tests require the following dependencies (already in `requirements.txt`):
- Python 3.7+
- unittest (built-in)
- All project dependencies

## Notes

- Tests use temporary databases for isolation
- Each test creates a fresh blockchain instance
- Tests clean up after themselves automatically

