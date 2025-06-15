#!/usr/bin/env python3

import sys
import logging
from datetime import datetime
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MessageProvider:
    def get_message(self) -> str:
        try:
            return "Hello World from Primary Provider"
        except Exception as e:
            logger.error(f"Primary provider failed: {str(e)}")
            raise

class BackupMessageProvider:
    def get_message(self) -> str:
        try:
            return "Hello World from Backup Provider"
        except Exception as e:
            logger.error(f"Backup provider failed: {str(e)}")
            raise

def get_message_with_failover() -> Optional[str]:
    providers = [MessageProvider(), BackupMessageProvider()]
    
    for provider in providers:
        try:
            message = provider.get_message()
            logger.info(f"Successfully got message from {provider.__class__.__name__}")
            return message
        except Exception as e:
            logger.warning(f"Provider {provider.__class__.__name__} failed, trying next...")
            continue
    
    logger.error("All providers failed")
    return None

def main():
    try:
        message = get_message_with_failover()
        if message:
            print(f"\nResult: {message}")
            logger.info("Message delivered successfully")
            return 0
        else:
            logger.error("Failed to get message from any provider")
            return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())