#!/usr/bin/env python3
import sys
from pathlib import Path
import os
import uvicorn

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def start_api():
    """Start the FastAPI server"""
    
    print("🚀 Starting Temperature Monitoring API")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists(os.path.join(project_root, "database", "connection.py")):
        print("❌ Please run from project root directory")
        return False
    
    # Test database connection
    try:
        from database.connection import test_connection
        if not test_connection():
            print("❌ Database connection failed")
            return False
        print("✅ Database connection verified")
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    
    # Print token information
    try:
        token_file = os.path.join(project_root, "api_tokens.json")
        if os.path.exists(token_file):
            import json
            with open(token_file, 'r') as f:
                tokens = json.load(f)
            
            print("\n🔑 API Tokens available:")
            for customer, customer_tokens in tokens.items():
                if customer == "admin":
                    print(f"  Admin Token: {customer_tokens.get('admin_token', 'N/A')}")
                else:
                    print(f"  Customer {customer}:")
                    print(f"    Read Token: {customer_tokens.get('read_token', 'N/A')}")
                    print(f"    Write Token: {customer_tokens.get('write_token', 'N/A')}")
    except Exception as e:
        print(f"⚠️ Could not read token file: {e}")
    
    # Start the server
    print("\n🌐 Starting API server...")
    print("📍 API will be available at: http://localhost:8000")
    print("📚 API Documentation at: http://localhost:8000/docs")
    print("🔄 Press Ctrl+C to stop\n")
    
    try:
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except ImportError:
        print("❌ uvicorn not installed. Run: pip install uvicorn")
        return False
    except KeyboardInterrupt:
        print("\n🛑 API server stopped")
        return True
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return False

if __name__ == "__main__":
    success = start_api()
    sys.exit(0 if success else 1)