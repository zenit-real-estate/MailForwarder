#!/usr/bin/env python3
"""
Log viewer utility for MailForwarder application.
Allows viewing and filtering logs from different log files.
"""

import argparse
import os
from datetime import datetime, timedelta
from pathlib import Path

def view_log_file(log_file, lines=50, filter_text=None, level=None):
    """View contents of a log file with optional filtering."""
    if not os.path.exists(log_file):
        print(f"Log file not found: {log_file}")
        return
    
    print(f"\n{'='*80}")
    print(f"Viewing: {log_file}")
    print(f"{'='*80}")
    
    with open(log_file, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
    
    # Apply filters
    filtered_lines = []
    for line in all_lines:
        include_line = True
        
        if filter_text and filter_text.lower() not in line.lower():
            include_line = False
            
        if level and level.upper() not in line:
            include_line = False
            
        if include_line:
            filtered_lines.append(line)
    
    # Show last N lines
    if lines > 0:
        filtered_lines = filtered_lines[-lines:]
    
    if not filtered_lines:
        print("No log entries found matching the criteria.")
        return
    
    for line in filtered_lines:
        print(line.rstrip())

def main():
    parser = argparse.ArgumentParser(description='View MailForwarder application logs')
    parser.add_argument('--file', choices=['app', 'errors', 'activity', 'all'], 
                       default='app', help='Log file to view')
    parser.add_argument('--lines', type=int, default=50, 
                       help='Number of lines to show (0 for all)')
    parser.add_argument('--filter', type=str, 
                       help='Filter lines containing this text')
    parser.add_argument('--level', choices=['INFO', 'WARNING', 'ERROR', 'DEBUG'], 
                       help='Filter by log level')
    parser.add_argument('--since', type=str, 
                       help='Show logs since this time (format: YYYY-MM-DD HH:MM:SS)')
    
    args = parser.parse_args()
    
    log_dir = Path("logs")
    if not log_dir.exists():
        print("Logs directory not found. Run the application first to generate logs.")
        return
    
    files_to_view = []
    if args.file == 'all':
        files_to_view = ['app.log', 'errors.log', 'activity.log']
    else:
        files_to_view = [f"{args.file}.log"]
    
    for log_file in files_to_view:
        file_path = log_dir / log_file
        if file_path.exists():
            view_log_file(file_path, args.lines, args.filter, args.level)
        else:
            print(f"Log file not found: {file_path}")

if __name__ == "__main__":
    main() 