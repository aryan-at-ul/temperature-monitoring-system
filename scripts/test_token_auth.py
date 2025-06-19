# scripts/test_token_auth.py
import sys
import os
import asyncio
from pathlib import Path


project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi.security import HTTPAuthorizationCredentials
from api.auth.token_auth import get_current_customer

async def test_token():
    token = sys.argv[1] if len(sys.argv) > 1 else "read_B_66_token_2025"
    print(f"Testing token: {token}")
    

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    
    try:
        
        customer = await get_current_customer(credentials)
        print(f"✅ Authentication successful!")
        print(f"Customer: {customer}")
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_token())