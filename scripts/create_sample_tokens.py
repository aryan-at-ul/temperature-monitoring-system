# scripts/create_sample_tokens.py
#!/usr/bin/env python3
import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def create_simple_tokens():
    """Create simple tokens for testing with proper JSONB handling"""
    
    print("🔑 Creating Simple API Tokens for Testing")
    print("=" * 45)
    
    # Test database connection
    from database.connection import test_connection, DatabaseConnection
    if not test_connection():
        print("❌ Database connection failed")
        return False
    
    try:
        db = DatabaseConnection()
       
        customers = db.execute_query("SELECT customer_code, id FROM customers WHERE is_active = TRUE ORDER BY customer_code")
        
        if not customers:
            print("❌ No active customers found in database")
            return False
        
        tokens = {}
        
        print(f"Found {len(customers)} customers")
        
        for customer in customers:
            customer_id = customer['customer_code']
            customer_db_id = customer['id']
            
            try:
            
                read_token = f"read_{customer_id}_{''.join([str(ord(c)) for c in customer_id])}_token_2025"
                write_token = f"write_{customer_id}_{''.join([str(ord(c)) for c in customer_id])}_token_2025"
                
           
                import hashlib
                read_hash = hashlib.sha256(read_token.encode()).hexdigest()
                write_hash = hashlib.sha256(write_token.encode()).hexdigest()
                
        
                db.execute_command("""
                    INSERT INTO customer_tokens 
                    (customer_id, token_hash, token_name, permissions, is_active)
                    VALUES (%s, %s, %s, %s::jsonb, %s)
                    ON CONFLICT (token_hash) DO NOTHING
                """, (customer_db_id, read_hash, f"Read token for {customer_id}", 
                     json.dumps(["read"]), True))
                
                
                db.execute_command("""
                    INSERT INTO customer_tokens 
                    (customer_id, token_hash, token_name, permissions, is_active)
                    VALUES (%s, %s, %s, %s::jsonb, %s)
                    ON CONFLICT (token_hash) DO NOTHING
                """, (customer_db_id, write_hash, f"Write token for {customer_id}", 
                     json.dumps(["read", "write"]), True))
                
                tokens[customer_id] = {
                    "read_token": read_token,
                    "write_token": write_token
                }
                
                print(f"✅ Created tokens for Customer {customer_id}")
                
            except Exception as e:
                print(f"❌ Failed to create tokens for Customer {customer_id}: {e}")
                # Rollback the transaction and continue
                db.connection.rollback()
        
    
        if 'A' in tokens:
            try:
                admin_token = f"admin_A_{''.join([str(ord(c)) for c in 'A'])}_admin_token_2025"
                admin_hash = hashlib.sha256(admin_token.encode()).hexdigest()
                
         
                customer_a_id = next(c['id'] for c in customers if c['customer_code'] == 'A')
                
                db.execute_command("""
                    INSERT INTO customer_tokens 
                    (customer_id, token_hash, token_name, permissions, is_active)
                    VALUES (%s, %s, %s, %s::jsonb, %s)
                    ON CONFLICT (token_hash) DO NOTHING
                """, (customer_a_id, admin_hash, "Admin token", 
                     json.dumps(["admin"]), True))
                
                tokens["admin"] = {"admin_token": admin_token}
                print("✅ Created admin token (using Customer A)")
                
            except Exception as e:
                print(f"❌ Failed to create admin token: {e}")
                db.connection.rollback()
        
  
        with open("api_tokens.json", "w") as f:
            json.dump(tokens, f, indent=2)
        
        print(f"\n📁 Tokens saved to: api_tokens.json")
        print(f"📋 Created tokens for {len([k for k in tokens.keys() if k != 'admin'])} customers + admin")
 
        if tokens:
            first_customer = next((k for k in tokens.keys() if k != "admin"), None)
            if first_customer:
                sample_token = tokens[first_customer]["read_token"]
                print(f"\n🔗 Example API calls:")
                print(f"# Test health (no auth needed)")
                print(f"curl http://localhost:8000/api/v1/health")
                print(f"\n# Test customer endpoint")
                print(f"curl -H 'Authorization: Bearer {sample_token}' http://localhost:8000/api/v1/customers/me")
                print(f"\n# Test temperature readings")
                print(f"curl -H 'Authorization: Bearer {sample_token}' 'http://localhost:8000/api/v1/temperatures?limit=5'")
                
                if "admin" in tokens:
                    admin_token = tokens["admin"]["admin_token"]
                    print(f"\n# Test admin endpoint")
                    print(f"curl -H 'Authorization: Bearer {admin_token}' http://localhost:8000/api/v1/admin/customers")
        
        token_count = db.execute_query("SELECT COUNT(*) as count FROM customer_tokens WHERE is_active = TRUE")[0]['count']
        print(f"\n✅ Verification: {token_count} active tokens in database")
        
        db.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Token creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_simple_tokens()
    sys.exit(0 if success else 1)