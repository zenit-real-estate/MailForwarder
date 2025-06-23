# MailForwarder

An automated email forwarding system for real estate property inquiries. The system monitors incoming emails from various real estate platforms, extracts property codes, and forwards inquiries to the appropriate real estate agents.

## Features

- **Automated Email Monitoring**: Continuously monitors Gmail inbox for new property inquiries
- **Smart Email Classification**: Automatically identifies the source platform (Homegate, Idealista, etc.)
- **Property Code Extraction**: Extracts Miogest property codes from email subjects
- **Intelligent Forwarding**: Routes emails to the correct agents based on property assignments
- **Request Tracking**: Maintains a database of property inquiries and request counts
- **Comprehensive Logging**: Detailed logging system for monitoring and debugging

## Logging System

The application includes a comprehensive logging system that tracks all operations and provides detailed insights into the application's behavior.

### Log Files

The application creates three main log files in the `logs/` directory:

1. **`app.log`** - Main application log with all INFO level messages
2. **`errors.log`** - Error-specific log with detailed error information and stack traces
3. **`activity.log`** - Activity log tracking email processing and forwarding events

### Log Rotation

- **Main Log**: 10MB max size, keeps 5 backup files
- **Error Log**: 5MB max size, keeps 3 backup files
- **Activity Log**: 10MB max size, keeps 5 backup files
- **Automatic Cleanup**: Old log files (>30 days) are automatically cleaned up

### Log Levels

- **INFO**: General application events and successful operations
- **WARNING**: Non-critical issues that should be monitored
- **ERROR**: Critical errors with full stack traces
- **DEBUG**: Detailed debugging information

### Viewing Logs

Use the included log viewer utility:

```bash
# View main application log (last 50 lines)
python view_logs.py

# View all logs
python view_logs.py --file all

# View only errors
python view_logs.py --file errors

# Filter logs by text
python view_logs.py --filter "email forwarded"

# Filter by log level
python view_logs.py --level ERROR

# Show more lines
python view_logs.py --lines 100
```

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create Environment File**:
   Create a `.env` file with your credentials:
   ```
   EMAIL_PASSWORD=your_gmail_app_password_here
   MIOGEST_USERNAME=your_miogest_username
   MIOGEST_PASSWORD=your_miogest_password
   ```

3. **Gmail Setup**:
   - Enable 2-Step Verification in your Google Account
   - Generate an App Password for "Mail"
   - Enable IMAP in Gmail settings

## Usage

### Running the Application

```bash
python app.py
```

The application will:
1. Start logging system and create log files
2. Connect to Gmail IMAP server
3. Begin monitoring for new emails
4. Process and forward emails automatically
5. Log all activities and errors

### Stopping the Application

Use `Ctrl+C` for graceful shutdown. The application will:
- Complete current operations
- Save any pending database changes
- Clean up old log files
- Log shutdown information

### Monitoring and Debugging

1. **Real-time Monitoring**: Check the console output for immediate feedback
2. **Log Analysis**: Use the log viewer to analyze application behavior
3. **Error Tracking**: Monitor `errors.log` for critical issues
4. **Performance Monitoring**: Check activity logs for performance metrics

## Logged Events

The system logs the following events:

### Application Lifecycle
- Application startup and shutdown
- Connection attempts and results
- Graceful shutdown handling

### Email Processing
- Email reception and parsing
- Miogest code extraction
- Source classification
- Forwarding attempts and results

### Database Operations
- Data loading and saving
- Request count updates
- New object additions

### Error Handling
- Connection failures
- Email processing errors
- Database operation failures
- Unexpected exceptions

### Performance Metrics
- Email processing duration
- Forwarding operation timing
- Database operation performance

## Configuration

### Log Directory
Logs are stored in the `logs/` directory by default. You can modify this in `logger.py`.

### Log Rotation
Adjust log file sizes and backup counts in the `MailForwarderLogger` class.

### Log Cleanup
The application automatically cleans up logs older than 30 days. Modify this in the cleanup function.

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check your Gmail credentials and IMAP settings
2. **Log File Issues**: Ensure the `logs/` directory is writable
3. **Performance Issues**: Monitor activity logs for slow operations
4. **Email Processing Failures**: Check error logs for specific failure reasons

### Debug Mode

To enable debug logging, modify the logger configuration in `logger.py`:

```python
self.main_logger.setLevel(logging.DEBUG)
```

## Security Notes

- Never log sensitive information (passwords, tokens)
- Log files may contain email addresses and property codes
- Ensure log files are properly secured in production environments
- Regularly review and clean up old log files

## Maintenance

### Regular Tasks
- Monitor log file sizes
- Review error logs for recurring issues
- Clean up old log files if needed
- Backup important log data

### Performance Optimization
- Monitor performance metrics in activity logs
- Adjust log rotation settings based on usage
- Consider log aggregation for high-volume deployments

### How to run
#### Prerequisites
Python: version 3.13.3

#### Run with
python app.py

