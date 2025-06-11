#!/usr/bin/env python3
"""
Check Knowledge Hub Database Schema
===================================

This script retrieves the database schema to understand available properties.
"""

import os
import requests
import json

def main():
    # Configuration
    KNOWLEDGE_HUB_DB_ID = '20bec31c-9de2-814e-80db-d13d0c27d869'

        # Try to read from .env file
        try:
            with open('.env', 'r') as f:
                for line in f:
                        break
        except:
            pass

        return

    headers = {
        'Content-Type': 'application/json',
        'Notion-Version': '2022-06-28'
    }

    try:
        # Get database schema
        response = requests.get(
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f'Error getting database schema: {response.status_code}')
            print(f'Response: {response.text}')
            return
        
        data = response.json()
        properties = data.get('properties', {})
        
        print('📊 Knowledge Hub Database Properties:')
        print('=' * 50)
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get('type', 'unknown')
            print(f'{prop_name}: {prop_type}')

    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()