import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

class MailForwarderLogger:
    """
    Centralized logging system for the MailForwarder application.
    Handles log rotation, different log levels, and file management.
    """
    
    def __init__(self, log_dir="logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create formatters
        self.detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        self.simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Setup loggers
        self.setup_main_logger()
        self.setup_error_logger()
        self.setup_activity_logger()
        
    def setup_main_logger(self):
        """Setup the main application logger."""
        self.main_logger = logging.getLogger('mailforwarder.main')
        self.main_logger.setLevel(logging.INFO)
        
        # Main log file with rotation (10MB max, keep 5 backup files)
        main_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        main_handler.setLevel(logging.INFO)
        main_handler.setFormatter(self.detailed_formatter)
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.simple_formatter)
        
        self.main_logger.addHandler(main_handler)
        self.main_logger.addHandler(console_handler)
        
    def setup_error_logger(self):
        """Setup the error logger for critical errors and exceptions."""
        self.error_logger = logging.getLogger('mailforwarder.errors')
        self.error_logger.setLevel(logging.ERROR)
        
        # Error log file with rotation
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'errors.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self.detailed_formatter)
        
        self.error_logger.addHandler(error_handler)
        
    def setup_activity_logger(self):
        """Setup the activity logger for email processing events."""
        self.activity_logger = logging.getLogger('mailforwarder.activity')
        self.activity_logger.setLevel(logging.INFO)
        
        # Activity log file with rotation
        activity_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'activity.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        activity_handler.setLevel(logging.INFO)
        activity_handler.setFormatter(self.detailed_formatter)
        
        self.activity_logger.addHandler(activity_handler)
        
    def log_startup(self):
        """Log application startup."""
        self.main_logger.info("=" * 60)
        self.main_logger.info("MailForwarder Application Starting")
        self.main_logger.info(f"Log directory: {self.log_dir.absolute()}")
        self.main_logger.info("=" * 60)
        
    def log_shutdown(self, reason="Normal shutdown"):
        """Log application shutdown."""
        self.main_logger.info("=" * 60)
        self.main_logger.info(f"MailForwarder Application Shutting Down - Reason: {reason}")
        self.main_logger.info("=" * 60)
        
    def log_connection_attempt(self, server_type, server_address):
        """Log connection attempts to mail servers."""
        self.main_logger.info(f"Attempting to connect to {server_type} server: {server_address}")
        
    def log_connection_success(self, server_type, server_address):
        """Log successful connections to mail servers."""
        self.main_logger.info(f"Successfully connected to {server_type} server: {server_address}")
        
    def log_connection_failure(self, server_type, server_address, error):
        """Log connection failures to mail servers."""
        self.error_logger.error(f"Failed to connect to {server_type} server: {server_address} - Error: {error}")
        
    def log_email_received(self, email_id, sender, subject):
        """Log when an email is received."""
        self.activity_logger.info(f"Email received - ID: {email_id}, From: {sender}, Subject: {subject}")
        
    def log_email_processed(self, email_id, miogest_code, recipients):
        """Log when an email is successfully processed and forwarded."""
        self.activity_logger.info(
            f"Email processed successfully - ID: {email_id}, "
            f"Miogest Code: {miogest_code}, Recipients: {recipients}"
        )
        
    def log_email_forwarded(self, email_id, recipients, success=True):
        """Log email forwarding attempts."""
        if success:
            self.activity_logger.info(f"Email forwarded successfully - ID: {email_id}, To: {recipients}")
        else:
            self.error_logger.error(f"Failed to forward email - ID: {email_id}, To: {recipients}")
            
    def log_miogest_code_extracted(self, email_id, miogest_code):
        """Log when a Miogest code is extracted from an email."""
        self.activity_logger.info(f"Miogest code extracted - Email ID: {email_id}, Code: {miogest_code}")
        
    def log_miogest_code_not_found(self, email_id, subject):
        """Log when no Miogest code is found in an email."""
        self.activity_logger.warning(f"No Miogest code found - Email ID: {email_id}, Subject: {subject}")
        
    def log_source_classified(self, email_id, source, label):
        """Log when an email source is classified."""
        self.activity_logger.info(f"Email source classified - ID: {email_id}, Source: {source}, Label: {label}")
        
    def log_database_update(self, miogest_code, old_count, new_count):
        """Log database updates."""
        self.activity_logger.info(f"Database updated - Code: {miogest_code}, Requests: {old_count} -> {new_count}")
        
    def log_idle_mode(self, enabled=True):
        """Log IMAP IDLE mode status."""
        if enabled:
            self.main_logger.info("IMAP IDLE mode enabled - Waiting for new emails...")
        else:
            self.main_logger.info("IMAP IDLE mode disabled")
            
    def log_error(self, error, context=""):
        """Log general errors with context."""
        self.error_logger.error(f"Error occurred - Context: {context}, Error: {error}", exc_info=True)
        
    def log_warning(self, message, context=""):
        """Log warnings."""
        self.main_logger.warning(f"Warning - Context: {context}, Message: {message}")
        
    def log_debug(self, message, context=""):
        """Log debug information."""
        self.main_logger.debug(f"Debug - Context: {context}, Message: {message}")
        
    def log_performance(self, operation, duration_ms):
        """Log performance metrics."""
        self.activity_logger.info(f"Performance - Operation: {operation}, Duration: {duration_ms}ms")
        
    def cleanup_old_logs(self, days_to_keep=30):
        """Clean up old log files."""
        try:
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            for log_file in self.log_dir.glob("*.log.*"):
                if log_file.stat().st_mtime < cutoff_date:
                    log_file.unlink()
                    self.main_logger.info(f"Cleaned up old log file: {log_file}")
        except Exception as e:
            self.error_logger.error(f"Error during log cleanup: {e}")

# Global logger instance
logger = MailForwarderLogger() 