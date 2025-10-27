import json
import hashlib
import sqlite3
from datetime import datetime
from uuid import uuid4
from urllib.parse import urlparse
from flask import Flask, jsonify, request, render_template_string
import logging
import requests
import random
import string
import argparse
from reset_db import reset_database, clear_tables

# Import our modules
import account_manager
from Blockchain import Blockchain
from Blockchain import log_change

# Ensure database is migrated
account_manager.migrate_database()

# Create Flask app
app = Flask(__name__)

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--reset', action='store_true', help='Reset the blockchain and database')
parser.add_argument('--clear', action='store_true', help='Clear all tables but keep database structure')
args = parser.parse_args()

# Initialize blockchain
if args.reset:
    if reset_database():
        print("Database reset successful. Starting fresh blockchain...")
        blockchain = Blockchain(reset_chain=True)
    else:
        print("Failed to reset database. Exiting...")
        exit(1)
elif args.clear:
    if clear_tables():
        print("Tables cleared successfully. Starting fresh blockchain...")
        blockchain = Blockchain(reset_chain=True)
    else:
        print("Failed to clear tables. Exiting...")
        exit(1)
else:
    blockchain = Blockchain()

# HTML template for the interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>P2P Energy Trading Blockchain</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-start: #0f2027;
            --bg-mid: #203a43;
            --bg-end: #2c5364;
            --card-bg: rgba(255, 255, 255, 0.08);
            --card-border: rgba(255, 255, 255, 0.16);
            --text-primary: #e8f1f2;
            --text-muted: #b8c4c7;
            --primary: #58d68d;
            --primary-strong: #2ecc71;
            --accent: #00c2ff;
            --danger: #ff6b6b;
            --warning: #ffd166;
            --shadow: 0 10px 30px rgba(0,0,0,0.35);
            --radius: 14px;
        }

        * { box-sizing: border-box; }

        body {
            font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
            margin: 0;
            padding: 40px 20px;
            color: var(--text-primary);
            background: radial-gradient(1200px 600px at 10% 10%, rgba(0, 194, 255, 0.12), transparent 60%),
                        radial-gradient(1000px 500px at 90% 20%, rgba(88, 214, 141, 0.12), transparent 60%),
                        linear-gradient(135deg, var(--bg-start), var(--bg-mid) 45%, var(--bg-end));
            min-height: 100vh;
        }

        .container { max-width: 980px; margin: 0 auto; }

        h1 {
            text-align: center;
            margin: 0 0 30px 0;
            letter-spacing: 0.3px;
            font-weight: 700;
            font-size: 30px;
            background: linear-gradient(90deg, var(--primary), var(--accent));
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        h2 {
            margin: 0 0 18px 0;
            color: var(--text-primary);
            font-size: 18px;
            letter-spacing: 0.2px;
        }

        .section {
            margin: 22px 0;
            padding: 22px;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: var(--radius);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            box-shadow: var(--shadow);
        }

        .form-group { margin: 14px 0 16px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: var(--text-muted); font-size: 13px; }

        input, select {
            width: 100%;
            padding: 12px 14px;
            border: 1px solid rgba(255,255,255,0.18);
            border-radius: 10px;
            background: rgba(255,255,255,0.06);
            color: var(--text-primary);
            font-size: 14px;
            outline: none;
            transition: border-color .2s ease, box-shadow .2s ease, transform .05s ease;
        }
        input::placeholder { color: rgba(232,241,242,0.55); }
        select { appearance: none; background-image: linear-gradient(45deg, transparent 50%, var(--text-muted) 50%), linear-gradient(135deg, var(--text-muted) 50%, transparent 50%); background-position: calc(100% - 20px) calc(1em + 2px), calc(100% - 15px) calc(1em + 2px); background-size: 5px 5px, 5px 5px; background-repeat: no-repeat; }
        input:focus, select:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(0,194,255,0.2); }

        button {
            padding: 12px 20px;
            background: linear-gradient(135deg, var(--primary), var(--primary-strong));
            color: #0b1d22;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.3px;
            transition: transform .06s ease, filter .2s ease, box-shadow .2s ease;
            box-shadow: 0 8px 20px rgba(46, 204, 113, 0.25);
        }
        button:hover { filter: brightness(1.05); box-shadow: 0 10px 24px rgba(46, 204, 113, 0.28); }
        button:active { transform: translateY(1px); }

        .result { margin-top: 16px; padding: 14px; background: rgba(255,255,255,0.05); border-radius: 10px; border: 1px solid rgba(255,255,255,0.12); }
        pre { white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, "Courier New", monospace; }

        .success-message { color: #0e3b22; padding: 12px; background: linear-gradient(135deg, rgba(88,214,141,0.22), rgba(46,204,113,0.22)); border-radius: 10px; margin: 10px 0; border: 1px solid rgba(88,214,141,0.4); }
        .error-message { color: #3f0e0e; padding: 12px; background: linear-gradient(135deg, rgba(255,107,107,0.2), rgba(255,139,139,0.2)); border-radius: 10px; margin: 10px 0; border: 1px solid rgba(255,107,107,0.4); }

        .accounts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
            gap: 18px;
            padding: 10px 0 4px;
        }
        .account-card {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.14);
            border-radius: 12px;
            padding: 18px;
            box-shadow: var(--shadow);
            transition: transform 0.12s ease, border-color .2s ease, background .2s ease;
        }
        .account-card:hover { transform: translateY(-2px); border-color: rgba(0,194,255,0.35); background: rgba(255,255,255,0.08); }
        .account-details { margin-top: 12px; }

        .balance-info { background: rgba(0, 194, 255, 0.08); padding: 12px; border-radius: 10px; margin: 10px 0; border-left: 3px solid var(--accent); border: 1px solid rgba(0,194,255,0.25); }
        .balance-info p { margin: 6px 0; font-size: 13.5px; }
        .balance-info strong { color: var(--text-primary); }

        .blockchain-view { display: flex; flex-direction: column; gap: 16px; padding: 10px 0; }
        .block-card { background: rgba(255,255,255,0.06); border-radius: 12px; padding: 18px; box-shadow: var(--shadow); border: 1px solid rgba(255,255,255,0.14); border-left: 4px solid var(--primary); }
        .transactions { margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.12); }
        .transaction { background: rgba(255,255,255,0.06); padding: 12px; margin: 10px 0; border-radius: 10px; border-left: 3px solid var(--primary); border: 1px solid rgba(255,255,255,0.12); }

        .balance-management, .power-management { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-top: 12px; }
        .balance-card, .power-card { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.14); border-radius: 12px; padding: 18px; box-shadow: var(--shadow); }
        .balance-card h3, .power-card h3 { color: var(--text-primary); margin-bottom: 12px; font-size: 16px; }
        .power-info, .balance-change { background: rgba(255,255,255,0.06); padding: 12px; border-radius: 10px; margin-top: 8px; border: 1px solid rgba(255,255,255,0.12); }
        .balance-change { border-left: 3px solid var(--primary); }
        .balance-change p { margin: 6px 0; font-size: 13.5px; }
        .transaction-info { margin-top: 18px; }
        .transaction-info h4 { color: var(--text-muted); margin: 12px 0 10px; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.4px; }

        @media (max-width: 820px) {
            body { padding: 22px 14px; }
            .balance-management, .power-management { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>P2P Energy Trading Blockchain</h1>
        
        <div class="section">
            <h2>Create Account</h2>
            <form id="accountForm" onsubmit="submitAccount(event)">
                <div class="form-group">
                    <label for="accountName">Account Name:</label>
                    <input type="text" id="accountName" required placeholder="Enter account name">
                </div>
                <button type="submit">Create Account</button>
            </form>
            <div id="accountResult" class="result"></div>
        </div>

        <div class="section">
            <h2>View Accounts</h2>
            <button onclick="viewAccounts()">View All Accounts</button>
            <div id="accountsResult" class="result"></div>
        </div>

        <div class="section">
            <h2>Add Transaction</h2>
            <form id="transactionForm" onsubmit="submitTransaction(event)">
                <div class="form-group">
                    <label for="sender">Sender:</label>
                    <input type="text" id="sender" required placeholder="Enter sender account name">
                </div>
                <div class="form-group">
                    <label for="receiver">Receiver:</label>
                    <input type="text" id="receiver" required placeholder="Enter receiver account name">
                </div>
                <div class="form-group">
                    <label for="power">Power Amount (kWh):</label>
                    <input type="number" id="power" required placeholder="Enter power amount">
                </div>
                <div class="form-group">
                    <label for="price">Price (ETH/kWh):</label>
                    <input type="number" step="0.000001" id="price" required placeholder="Enter price per kWh">
                </div>
                <div class="form-group">
                    <label for="role">Role:</label>
                    <select id="role" required>
                        <option value="seller">Seller</option>
                        <option value="buyer">Buyer</option>
                    </select>
                </div>
                <button type="submit">Add Transaction</button>
            </form>
            <div id="transactionResult" class="result"></div>
        </div>

        <div class="section">
            <h2>Mine Block</h2>
            <button onclick="mineBlock()">Mine New Block</button>
            <div id="mineResult" class="result"></div>
        </div>

        <div class="section">
            <h2>View Blockchain</h2>
            <button onclick="viewChain()">View Chain</button>
            <div id="chainResult" class="result"></div>
        </div>

        <div class="section">
            <h2>Account Balance Management</h2>
            <div class="balance-management">
                <div class="balance-card">
                    <h3>Add Balance</h3>
                    <form id="addBalanceForm" onsubmit="addBalance(event)">
                        <div class="form-group">
                            <label for="addAccountName">Account Name:</label>
                            <input type="text" id="addAccountName" required placeholder="Enter account name">
                        </div>
                        <div class="form-group">
                            <label for="addAmount">Amount (ETH):</label>
                            <input type="number" step="0.000001" id="addAmount" required placeholder="Enter amount to add">
                        </div>
                        <button type="submit">Add Balance</button>
                    </form>
                    <div id="addBalanceResult" class="result"></div>
                </div>

                <div class="balance-card">
                    <h3>Withdraw Balance</h3>
                    <form id="withdrawBalanceForm" onsubmit="withdrawBalance(event)">
                        <div class="form-group">
                            <label for="withdrawAccountName">Account Name:</label>
                            <input type="text" id="withdrawAccountName" required placeholder="Enter account name">
                        </div>
                        <div class="form-group">
                            <label for="withdrawAmount">Amount (ETH):</label>
                            <input type="number" step="0.000001" id="withdrawAmount" required placeholder="Enter amount to withdraw">
                        </div>
                        <button type="submit">Withdraw Balance</button>
                    </form>
                    <div id="withdrawBalanceResult" class="result"></div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Power Balance Management</h2>
            <div class="power-management">
                <div class="power-card">
                    <h3>Add Power</h3>
                    <form id="addPowerForm" onsubmit="addPower(event)">
                        <div class="form-group">
                            <label for="addPowerAccountName">Account Name:</label>
                            <input type="text" id="addPowerAccountName" required placeholder="Enter account name">
                        </div>
                        <div class="form-group">
                            <label for="addPowerAmount">Amount (kWh):</label>
                            <input type="number" step="0.001" id="addPowerAmount" required placeholder="Enter power amount to add">
                        </div>
                        <button type="submit">Add Power</button>
                    </form>
                    <div id="addPowerResult" class="result"></div>
                </div>

                <div class="power-card">
                    <h3>Transfer Power</h3>
                    <form id="transferPowerForm" onsubmit="transferPower(event)">
                        <div class="form-group">
                            <label for="powerSender">Sender:</label>
                            <input type="text" id="powerSender" required placeholder="Enter sender account name">
                        </div>
                        <div class="form-group">
                            <label for="powerReceiver">Receiver:</label>
                            <input type="text" id="powerReceiver" required placeholder="Enter receiver account name">
                        </div>
                        <div class="form-group">
                            <label for="transferPowerAmount">Amount (kWh):</label>
                            <input type="number" step="0.001" id="transferPowerAmount" required placeholder="Enter power amount to transfer">
                        </div>
                        <button type="submit">Transfer Power</button>
                    </form>
                    <div id="transferPowerResult" class="result"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function submitAccount(event) {
            event.preventDefault();
            const name = document.getElementById('accountName').value;
            try {
                const response = await fetch('/add_account', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name })
                });
                const data = await response.json();
                if (response.ok) {
                    document.getElementById('accountResult').innerHTML = `
                        <div class="success-message">
                            <h3>Account Created Successfully!</h3>
                            <p>Account ID: ${data.account_id}</p>
                            <p>Public Key: ${data.public_key}</p>
                        </div>`;
                } else {
                    document.getElementById('accountResult').innerHTML = `
                        <div class="error-message">
                            <h3>Error Creating Account</h3>
                            <p>${data.error}</p>
                        </div>`;
                }
            } catch (error) {
                document.getElementById('accountResult').innerHTML = `
                    <div class="error-message">
                        <h3>Error</h3>
                        <p>${error}</p>
                    </div>`;
            }
        }

        async function submitTransaction(event) {
            event.preventDefault();
            const transaction = {
                sender: document.getElementById('sender').value,
                receiver: document.getElementById('receiver').value,
                power: parseFloat(document.getElementById('power').value),
                price: parseFloat(document.getElementById('price').value),
                role: document.getElementById('role').value
            };
            try {
                const response = await fetch('/add_transaction', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(transaction)
                });
                const data = await response.json();
                if (response.ok) {
                    document.getElementById('transactionResult').innerHTML = `
                        <div class="success-message">
                            <h3>Transaction Added Successfully!</h3>
                            <div class="transaction-info">
                                <h4>Transaction Details:</h4>
                                <p><strong>Total Cost:</strong> ${data.total_cost} ETH</p>
                                <p><strong>Power Amount:</strong> ${data.power_amount} kWh</p>
                                
                                <h4>Sender (${data.sender.name}):</h4>
                                <div class="balance-change">
                                    <p><strong>ETH Balance:</strong> ${data.sender.initial_balances.eth_balance} ETH → ${data.sender.final_balances.eth_balance} ETH</p>
                                    <p><strong>Power Balance:</strong> ${data.sender.initial_balances.power_balance} kWh → ${data.sender.final_balances.power_balance} kWh</p>
                                </div>
                                
                                <h4>Receiver (${data.receiver.name}):</h4>
                                <div class="balance-change">
                                    <p><strong>ETH Balance:</strong> ${data.receiver.initial_balances.eth_balance} ETH → ${data.receiver.final_balances.eth_balance} ETH</p>
                                    <p><strong>Power Balance:</strong> ${data.receiver.initial_balances.power_balance} kWh → ${data.receiver.final_balances.power_balance} kWh</p>
                                </div>
                            </div>
                        </div>`;
                } else {
                    document.getElementById('transactionResult').innerHTML = `
                        <div class="error-message">
                            <h3>Transaction Failed</h3>
                            <p>${data.error}</p>
                        </div>`;
                }
            } catch (error) {
                document.getElementById('transactionResult').innerHTML = `
                    <div class="error-message">
                        <h3>Error</h3>
                        <p>${error}</p>
                    </div>`;
            }
        }

        async function mineBlock() {
            try {
                const response = await fetch('/mine');
                const data = await response.json();
                if (response.ok) {
                    document.getElementById('mineResult').innerHTML = `
                        <div class="success-message">
                            <h3>Block Mined Successfully!</h3>
                            <p>Block Index: ${data.index}</p>
                            <p>Block Hash: ${data.block_hash}</p>
                            <p>Previous Hash: ${data.previous_hash}</p>
                            <p>Number of Transactions: ${data.transactions.length}</p>
                        </div>`;
                } else {
                    document.getElementById('mineResult').innerHTML = `
                        <div class="error-message">
                            <h3>Mining Failed</h3>
                            <p>${data.error}</p>
                        </div>`;
                }
            } catch (error) {
                document.getElementById('mineResult').innerHTML = `
                    <div class="error-message">
                        <h3>Error</h3>
                        <p>${error}</p>
                    </div>`;
            }
        }

        async function viewAccounts() {
            try {
                const response = await fetch('/accounts');
                const data = await response.json();
                if (response.ok) {
                    const accountsHtml = data.accounts.map(account => `
                        <div class="account-card">
                            <h3>${account.name}</h3>
                            <div class="account-details">
                                <p><strong>ID:</strong> ${account.id}</p>
                                <div class="balance-info">
                                    <p><strong>ETH Balance:</strong> ${account.balance} ETH</p>
                                    <p><strong>Power Balance:</strong> ${account.power_balance} kWh</p>
                                </div>
                                <p><strong>Created:</strong> ${new Date(account.created_at).toLocaleString()}</p>
                            </div>
                        </div>
                    `).join('');
                    document.getElementById('accountsResult').innerHTML = `
                        <div class="accounts-grid">
                            ${accountsHtml}
                        </div>
                    `;
                } else {
                    document.getElementById('accountsResult').innerHTML = `
                        <div class="error-message">
                            <h3>Error Loading Accounts</h3>
                            <p>${data.error}</p>
                        </div>`;
                }
            } catch (error) {
                document.getElementById('accountsResult').innerHTML = `
                    <div class="error-message">
                        <h3>Error</h3>
                        <p>${error}</p>
                    </div>`;
            }
        }

        async function viewChain() {
            try {
                const response = await fetch('/chain');
                const data = await response.json();
                if (response.ok) {
                    const chainHtml = data.chain.map(block => `
                        <div class="block-card">
                            <h3>Block #${block.index}</h3>
                            <p><strong>Timestamp:</strong> ${new Date(block.timestamp).toLocaleString()}</p>
                            <p><strong>Hash:</strong> ${block.block_hash}</p>
                            <p><strong>Previous Hash:</strong> ${block.previous_hash}</p>
                            <div class="transactions">
                                <h4>Transactions:</h4>
                                ${block.transactions.map(tx => `
                                    <div class="transaction">
                                        <p><strong>From:</strong> ${tx.Seller}</p>
                                        <p><strong>To:</strong> ${tx.Buyer}</p>
                                        <p><strong>Amount:</strong> ${tx.Power} kWh</p>
                                        <p><strong>Price:</strong> ${tx.Price} ETH/kWh</p>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `).join('');
                    document.getElementById('chainResult').innerHTML = `
                        <div class="blockchain-view">
                            ${chainHtml}
                        </div>
                    `;
                } else {
                    document.getElementById('chainResult').innerHTML = `
                        <div class="error-message">
                            <h3>Error Loading Blockchain</h3>
                            <p>${data.error}</p>
                        </div>`;
                }
            } catch (error) {
                document.getElementById('chainResult').innerHTML = `
                    <div class="error-message">
                        <h3>Error</h3>
                        <p>${error}</p>
                    </div>`;
            }
        }

        async function addBalance(event) {
            event.preventDefault();
            const accountName = document.getElementById('addAccountName').value;
            const amount = parseFloat(document.getElementById('addAmount').value);
            
            try {
                const response = await fetch('/add_balance', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ account_name: accountName, amount: amount })
                });
                const data = await response.json();
                
                if (response.ok) {
                    document.getElementById('addBalanceResult').innerHTML = `
                        <div class="success-message">
                            <h3>Balance Added Successfully!</h3>
                            <div class="balance-info">
                                <p><strong>Account:</strong> ${data.account_name}</p>
                                <p><strong>Amount Added:</strong> ${data.amount_added} ETH</p>
                                <p><strong>New Balance:</strong> ${data.new_balance} ETH</p>
                            </div>
                        </div>`;
                } else {
                    document.getElementById('addBalanceResult').innerHTML = `
                        <div class="error-message">
                            <h3>Failed to Add Balance</h3>
                            <p>${data.error}</p>
                        </div>`;
                }
            } catch (error) {
                document.getElementById('addBalanceResult').innerHTML = `
                    <div class="error-message">
                        <h3>Error</h3>
                        <p>${error}</p>
                    </div>`;
            }
        }

        async function withdrawBalance(event) {
            event.preventDefault();
            const accountName = document.getElementById('withdrawAccountName').value;
            const amount = parseFloat(document.getElementById('withdrawAmount').value);
            
            try {
                const response = await fetch('/withdraw_balance', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ account_name: accountName, amount: amount })
                });
                const data = await response.json();
                
                if (response.ok) {
                    document.getElementById('withdrawBalanceResult').innerHTML = `
                        <div class="success-message">
                            <h3>Withdrawal Successful!</h3>
                            <div class="balance-info">
                                <p><strong>Account:</strong> ${data.account_name}</p>
                                <p><strong>Amount Withdrawn:</strong> ${data.amount_withdrawn} ETH</p>
                                <p><strong>New Balance:</strong> ${data.new_balance} ETH</p>
                            </div>
                        </div>`;
                } else {
                    document.getElementById('withdrawBalanceResult').innerHTML = `
                        <div class="error-message">
                            <h3>Withdrawal Failed</h3>
                            <p>${data.error}</p>
                        </div>`;
                }
            } catch (error) {
                document.getElementById('withdrawBalanceResult').innerHTML = `
                    <div class="error-message">
                        <h3>Error</h3>
                        <p>${error}</p>
                    </div>`;
            }
        }

        async function addPower(event) {
            event.preventDefault();
            const accountName = document.getElementById('addPowerAccountName').value;
            const amount = parseFloat(document.getElementById('addPowerAmount').value);
            
            try {
                const response = await fetch('/add_power', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ account_name: accountName, amount: amount })
                });
                const data = await response.json();
                
                if (response.ok) {
                    document.getElementById('addPowerResult').innerHTML = `
                        <div class="success-message">
                            <h3>Power Added Successfully!</h3>
                            <div class="power-info">
                                <p><strong>Account:</strong> ${data.account_name}</p>
                                <p><strong>Amount Added:</strong> ${data.amount_added} kWh</p>
                                <p><strong>New Power Balance:</strong> ${data.new_power_balance} kWh</p>
                            </div>
                        </div>`;
                } else {
                    document.getElementById('addPowerResult').innerHTML = `
                        <div class="error-message">
                            <h3>Failed to Add Power</h3>
                            <p>${data.error}</p>
                        </div>`;
                }
            } catch (error) {
                document.getElementById('addPowerResult').innerHTML = `
                    <div class="error-message">
                        <h3>Error</h3>
                        <p>${error}</p>
                    </div>`;
            }
        }

        async function transferPower(event) {
            event.preventDefault();
            const sender = document.getElementById('powerSender').value;
            const receiver = document.getElementById('powerReceiver').value;
            const amount = parseFloat(document.getElementById('transferPowerAmount').value);
            
            try {
                const response = await fetch('/transfer_power', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sender: sender, receiver: receiver, amount: amount })
                });
                const data = await response.json();
                
                if (response.ok) {
                    document.getElementById('transferPowerResult').innerHTML = `
                        <div class="success-message">
                            <h3>Power Transfer Successful!</h3>
                            <div class="power-info">
                                <p><strong>From:</strong> ${data.sender}</p>
                                <p><strong>To:</strong> ${data.receiver}</p>
                                <p><strong>Amount Transferred:</strong> ${data.amount_transferred} kWh</p>
                                <p><strong>Sender New Balance:</strong> ${data.sender_new_balance} kWh</p>
                                <p><strong>Receiver New Balance:</strong> ${data.receiver_new_balance} kWh</p>
                            </div>
                        </div>`;
                } else {
                    document.getElementById('transferPowerResult').innerHTML = `
                        <div class="error-message">
                            <h3>Transfer Failed</h3>
                            <p>${data.error}</p>
                        </div>`;
                }
            } catch (error) {
                document.getElementById('transferPowerResult').innerHTML = `
                    <div class="error-message">
                        <h3>Error</h3>
                        <p>${error}</p>
                    </div>`;
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

# API Endpoints
@app.route('/add_account', methods=['POST'])
def add_account():
    try:
        data = request.json
        required_fields = ['name']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400
        
        name = data['name'].strip()
        new_account = account_manager.create_account(name)
        
        if new_account is None:
            raise ValueError("Failed to create account")
        
        log_change("Account Created", {"account_id": new_account['id'], "name": name})
        
        return jsonify({
            "message": "Account created successfully",
            "account_id": new_account['id'],
            "public_key": new_account['public_key']
        }), 201
    
    except Exception as e:
        logging.error(f"Error creating account: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/mine')
def mine():
    try:
        last_block = blockchain.last_block
        last_proof = last_block['proof']
        proof = blockchain.proof_of_work(last_proof)
        
        previous_hash = blockchain.hash(last_block)
        block = blockchain.new_block(proof, previous_hash)
        
        response = {
            'message': 'New block created',
            'index': block['index'],
            'transactions': block['transactions'],
            'proof': block['proof'],
            'previous_hash': block['previous_hash'],
            'block_hash': block['block_hash']
        }
        return jsonify(response), 200
    except Exception as e:
        logging.error(f"Error mining block: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/accounts')
def get_accounts():
    try:
        accounts = account_manager.get_all_accounts()
        return jsonify({"accounts": accounts}), 200
    except Exception as e:
        logging.error(f"Error getting accounts: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    try:
        print("DEBUG: Starting add_transaction route")
        values = request.json
        print(f"DEBUG: Received values: {values}")
        print(f"DEBUG: Values type: {type(values)}")
        
        required = ["sender", "receiver", "power", "price", "role"]
        if not all(k in values for k in required):
            return jsonify({"error": "Missing values"}), 400
        
        # Convert numeric values to float
        try:
            print(f"DEBUG: Converting power: {values['power']} ({type(values['power'])})")
            print(f"DEBUG: Converting price: {values['price']} ({type(values['price'])})")
            
            power_amount = float(values["power"])
            price_per_kwh = float(values["price"])
            total_cost = power_amount * price_per_kwh
            
            print(f"DEBUG: Converted values - power: {power_amount}, price: {price_per_kwh}, total: {total_cost}")
        except (ValueError, TypeError) as e:
            print(f"ERROR: Failed to convert numeric values: {str(e)}")
            print(f"ERROR: Power value: {values.get('power')} ({type(values.get('power'))})")
            print(f"ERROR: Price value: {values.get('price')} ({type(values.get('price'))})")
            return jsonify({"error": "Invalid numeric values for power or price"}), 400
        
        # Get initial balances
        print(f"DEBUG: Getting sender account: {values['sender']}")
        sender_account = account_manager.get_account(values["sender"])
        print(f"DEBUG: Sender account: {sender_account}")
        
        print(f"DEBUG: Getting receiver account: {values['receiver']}")
        receiver_account = account_manager.get_account(values["receiver"])
        print(f"DEBUG: Receiver account: {receiver_account}")
        
        if not sender_account:
            return jsonify({"error": f"Sender account '{values['sender']}' does not exist"}), 400
        if not receiver_account:
            return jsonify({"error": f"Receiver account '{values['receiver']}' does not exist"}), 400
        
        # Store initial balances
        initial_balances = {
            "sender": {
                "eth_balance": sender_account["balance"],
                "power_balance": sender_account["power_balance"]
            },
            "receiver": {
                "eth_balance": receiver_account["balance"],
                "power_balance": receiver_account["power_balance"]
            }
        }
        
        # Get balances - they should already be float from get_account
        print(f"DEBUG: Getting balances")
        print(f"DEBUG: Sender balance: {sender_account['balance']} ({type(sender_account['balance'])})")
        print(f"DEBUG: Sender power balance: {sender_account['power_balance']} ({type(sender_account['power_balance'])})")
        
        sender_eth_balance = sender_account["balance"]
        sender_power_balance = sender_account["power_balance"]
        receiver_eth_balance = receiver_account["balance"]
        receiver_power_balance = receiver_account["power_balance"]
        
        # Determine actual buyer and seller based on role
        if values["role"] == "seller":
            seller_name = values["sender"]
            buyer_name = values["receiver"]
            seller_power_bal = sender_power_balance
            buyer_eth_bal = receiver_eth_balance
        else:  # role == "buyer"
            buyer_name = values["sender"]
            seller_name = values["receiver"]
            seller_power_bal = receiver_power_balance
            buyer_eth_bal = sender_eth_balance

        # Check buyer has enough ETH
        if buyer_eth_bal < total_cost:
            return jsonify({"error": f"Insufficient ETH balance for buyer {buyer_name}"}), 400

        # Check seller has enough power
        if seller_power_bal < power_amount:
            return jsonify({"error": f"Insufficient power balance for seller {seller_name}"}), 400
            
        try:
            print("DEBUG: Updating balances")
            # Update ETH balances: buyer pays seller
            account_manager.update_balance(buyer_name, -total_cost)
            account_manager.update_balance(seller_name, total_cost)

            # Update power balances: seller transfers power to buyer
            account_manager.update_power_balance(seller_name, -power_amount)
            account_manager.update_power_balance(buyer_name, power_amount)
                
        except ValueError as e:
            print(f"ERROR: Failed to update balances: {str(e)}")
            return jsonify({"error": str(e)}), 400
        
        # Add transaction to blockchain
        print("DEBUG: Adding transaction to blockchain")
        blockchain.new_transaction_seller(seller_name, buyer_name, power_amount, price_per_kwh)
            
        # Get updated account balances
        print("DEBUG: Getting updated balances")
        updated_sender = account_manager.get_account(values["sender"])
        updated_receiver = account_manager.get_account(values["receiver"])
            
        return jsonify({
            "message": "Transaction will be processed",
            "total_cost": total_cost,
            "power_amount": power_amount,
            "sender": {
                "name": values["sender"],
                "initial_balances": {
                    "eth_balance": initial_balances["sender"]["eth_balance"],
                    "power_balance": initial_balances["sender"]["power_balance"]
                },
                "final_balances": {
                    "eth_balance": updated_sender["balance"],
                    "power_balance": updated_sender["power_balance"]
                }
            },
            "receiver": {
                "name": values["receiver"],
                "initial_balances": {
                    "eth_balance": initial_balances["receiver"]["eth_balance"],
                    "power_balance": initial_balances["receiver"]["power_balance"]
                },
                "final_balances": {
                    "eth_balance": updated_receiver["balance"],
                    "power_balance": updated_receiver["power_balance"]
                }
            }
        }), 201
        
    except Exception as e:
        print(f"ERROR in add_transaction: {str(e)}")
        print(f"ERROR type: {type(e).__name__}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        logging.error(f"Error adding transaction: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/chain')
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_node():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)
        
    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes)
    }
    return jsonify(response), 201

@app.route('/nodes/resolve')
def consensus():
    replaced = blockchain.resolve_conflicts()
    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'new_chain': blockchain.chain
        }
    return jsonify(response), 200

@app.route('/add_balance', methods=['POST'])
def add_balance():
    try:
        values = request.json
        required = ["account_name", "amount"]
        if not all(k in values for k in required):
            return jsonify({"error": "Missing values"}), 400
        
        amount = float(values["amount"])
        if amount <= 0:
            return jsonify({"error": "Amount must be greater than 0"}), 400
            
        # Check if account exists
        account = account_manager.get_account(values["account_name"])
        if not account:
            return jsonify({"error": f"Account '{values['account_name']}' does not exist"}), 400
            
        # Update balance
        new_balance = account_manager.update_balance(values["account_name"], amount)
        
        return jsonify({
            "message": "Balance added successfully",
            "account_name": values["account_name"],
            "amount_added": amount,
            "new_balance": new_balance
        }), 200
        
    except Exception as e:
        logging.error(f"Error adding balance: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/withdraw_balance', methods=['POST'])
def withdraw_balance():
    try:
        values = request.json
        required = ["account_name", "amount"]
        if not all(k in values for k in required):
            return jsonify({"error": "Missing values"}), 400
        
        amount = float(values["amount"])
        if amount <= 0:
            return jsonify({"error": "Amount must be greater than 0"}), 400
            
        # Check if account exists
        account = account_manager.get_account(values["account_name"])
        if not account:
            return jsonify({"error": f"Account '{values['account_name']}' does not exist"}), 400
            
        # Check if sufficient balance
        if account["balance"] < amount:
            return jsonify({"error": f"Insufficient balance for withdrawal"}), 400
            
        # Update balance
        new_balance = account_manager.update_balance(values["account_name"], -amount)
        
        return jsonify({
            "message": "Withdrawal successful",
            "account_name": values["account_name"],
            "amount_withdrawn": amount,
            "new_balance": new_balance
        }), 200
        
    except Exception as e:
        logging.error(f"Error withdrawing balance: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/add_power', methods=['POST'])
def add_power():
    try:
        values = request.json
        required = ["account_name", "amount"]
        if not all(k in values for k in required):
            return jsonify({"error": "Missing values"}), 400
        
        amount = float(values["amount"])
        if amount <= 0:
            return jsonify({"error": "Amount must be greater than 0"}), 400
            
        # Check if account exists
        account = account_manager.get_account(values["account_name"])
        if not account:
            return jsonify({"error": f"Account '{values['account_name']}' does not exist"}), 400
            
        # Update power balance
        new_power_balance = account_manager.update_power_balance(values["account_name"], amount)
        
        return jsonify({
            "message": "Power added successfully",
            "account_name": values["account_name"],
            "amount_added": amount,
            "new_power_balance": new_power_balance
        }), 200
        
    except Exception as e:
        logging.error(f"Error adding power: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/transfer_power', methods=['POST'])
def transfer_power():
    try:
        values = request.json
        required = ["sender", "receiver", "amount"]
        if not all(k in values for k in required):
            return jsonify({"error": "Missing values"}), 400
        
        amount = float(values["amount"])
        if amount <= 0:
            return jsonify({"error": "Amount must be greater than 0"}), 400
            
        # Check if both accounts exist
        sender_account = account_manager.get_account(values["sender"])
        receiver_account = account_manager.get_account(values["receiver"])
        
        if not sender_account:
            return jsonify({"error": f"Sender account '{values['sender']}' does not exist"}), 400
        if not receiver_account:
            return jsonify({"error": f"Receiver account '{values['receiver']}' does not exist"}), 400
            
        # Check if sender has sufficient power
        if sender_account["power_balance"] < amount:
            return jsonify({"error": f"Insufficient power balance for transfer"}), 400
            
        # Update power balances
        new_sender_balance = account_manager.update_power_balance(values["sender"], -amount)
        new_receiver_balance = account_manager.update_power_balance(values["receiver"], amount)
        
        return jsonify({
            "message": "Power transfer successful",
            "sender": values["sender"],
            "receiver": values["receiver"],
            "amount_transferred": amount,
            "sender_new_balance": new_sender_balance,
            "receiver_new_balance": new_receiver_balance
        }), 200
        
    except Exception as e:
        logging.error(f"Error transferring power: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=5000)