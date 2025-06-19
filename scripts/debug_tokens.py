# scripts/debug_tokens.py
import hashlib
import sys
import os
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.connection import DatabaseConnection

def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()

def main():
    token = sys.argv[1] if len(sys.argv) > 1 else "read_B_66_token_2025"
    print(f"Token: {token}")
    token_hash = hash_token(token)
    print(f"Token hash: {token_hash}")

    # Check in database
    db = DatabaseConnection()
    query = "SELECT * FROM customer_tokens WHERE token_hash = %s"
    result = db.execute_query(query, (token_hash,))
    
    if result:
        print(f"✅ Token found in database: {result[0]}")
        
        # Check permissions format
        permissions = result[0].get('permissions')
        print(f"Permissions: {permissions}, Type: {type(permissions)}")
        
        # Check associated customer
        customer_id = result[0].get('customer_id')
        customer_query = "SELECT * FROM customers WHERE id = %s"
        customer = db.execute_query(customer_query, (customer_id,))
        
        if customer:
            print(f"✅ Customer found: {customer[0]}")
        else:
            print(f"❌ No customer found with ID: {customer_id}")
    else:
        print(f"❌ Token not found in database")
        
        # List some tokens from the database
        all_tokens = db.execute_query("SELECT id, token_hash, token_name FROM customer_tokens LIMIT 5")
        print(f"Sample tokens in database:")
        for i, token in enumerate(all_tokens):
            print(f"{i+1}. {token}")

if __name__ == "__main__":
    main()