#!/usr/bin/env python3
"""
Token Helper Utilities

Helper functions for loading and using API tokens.
"""

import json
import sys
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def load_tokens():
    """Load tokens from api_tokens.json file"""
    try:
        # Try to load from project root
        token_path = project_root / "api_tokens.json"
        if token_path.exists():
            with open(token_path, "r") as f:
                return json.load(f)
                
        # Try to load from the script directory
        token_path = Path(__file__).parent.parent / "api_tokens.json"
        if token_path.exists():
            with open(token_path, "r") as f:
                return json.load(f)
                
        # Use hardcoded tokens as fallback
        return {
            "A": {
                "read_token": "read_A_65_token_2025",
                "write_token": "write_A_65_token_2025"
            },
            "B": {
                "read_token": "read_B_66_token_2025",
                "write_token": "write_B_66_token_2025"
            },
            "C": {
                "read_token": "read_C_67_token_2025",
                "write_token": "write_C_67_token_2025"
            },
            "D": {
                "read_token": "read_D_68_token_2025",
                "write_token": "write_D_68_token_2025"
            },
            "E": {
                "read_token": "read_E_69_token_2025",
                "write_token": "write_E_69_token_2025"
            },
            "F": {
                "read_token": "read_F_70_token_2025",
                "write_token": "write_F_70_token_2025"
            },
            "G": {
                "read_token": "read_G_71_token_2025",
                "write_token": "write_G_71_token_2025"
            },
            "H": {
                "read_token": "read_H_72_token_2025",
                "write_token": "write_H_72_token_2025"
            },
            "I": {
                "read_token": "read_I_73_token_2025",
                "write_token": "write_I_73_token_2025"
            },
            "J": {
                "read_token": "read_J_74_token_2025",
                "write_token": "write_J_74_token_2025"
            },
            "admin": {
                "admin_token": "admin_A_65_admin_token_2025"
            }
        }
    except Exception as e:
        print(f"Error loading tokens: {e}")
        sys.exit(1)

def get_token(customer_code, token_type="read"):
    """Get a token for the specified customer and type"""
    tokens = load_tokens()
    
    if customer_code not in tokens:
        raise ValueError(f"No tokens found for customer {customer_code}")
        
    if token_type == "read":
        if "read_token" not in tokens[customer_code]:
            raise ValueError(f"No read token found for customer {customer_code}")
        return tokens[customer_code]["read_token"]
    elif token_type == "write":
        if "write_token" not in tokens[customer_code]:
            raise ValueError(f"No write token found for customer {customer_code}")
        return tokens[customer_code]["write_token"]
    elif token_type == "admin" and customer_code == "admin":
        return tokens["admin"]["admin_token"]
    else:
        raise ValueError(f"Invalid token type {token_type}")

def get_token_header(customer_code, token_type="read"):
    """Get authorization headers for the specified customer and token type"""
    token = get_token(customer_code, token_type)
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }