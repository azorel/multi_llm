import logging
import os
from datetime import datetime
from typing import Optional

class SimpleLogger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SimpleLogger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.logger = logging.getLogger('simple_logger')
        self.logger.setLevel(logging.DEBUG)
        
        # Create logs directory if it doesn't exist
        self.logs_dir = 'logs'
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # File handler
        log_file = os.path.join(self.logs_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatters and add them to the handlers
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str, exc_info: Optional[Exception] = None) -> None:
        try:
            self.logger.debug(message, exc_info=exc_info)
        except Exception as e:
            print(f"Error logging debug message: {str(e)}")
    
    def info(self, message: str) -> None:
        try:
            self.logger.info(message)
        except Exception as e:
            print(f"Error logging info message: {str(e)}")
    
    def warning(self, message: str) -> None:
        try:
            self.logger.warning(message)
        except Exception as e:
            print(f"Error logging warning message: {str(e)}")
    
    def error(self, message: str, exc_info: Optional[Exception] = None) -> None:
        try:
            self.logger.error(message, exc_info=exc_info)
        except Exception as e:
            print(f"Error logging error message: {str(e)}")
    
    def critical(self, message: str, exc_info: Optional[Exception] = None) -> None:
        try:
            self.logger.critical(message, exc_info=exc_info)
        except Exception as e:
            print(f"Error logging critical message: {str(e)}")

# Example usage
if __name__ == "__main__":
    # Test the logger
    logger = SimpleLogger()
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    
    try:
        raise ValueError("Test exception")
    except Exception as e:
        logger.error("An error occurred", exc_info=e)
    
    logger.critical("This is a critical message")