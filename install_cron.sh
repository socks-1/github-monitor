#!/bin/bash
# Install cron job for GitHub monitoring

# Get the absolute path to this directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create cron job that runs every 20 minutes
CRON_JOB="*/20 * * * * cd $SCRIPT_DIR && /usr/bin/python3 monitor_check.py >> $SCRIPT_DIR/monitor.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "monitor_check.py"; then
    echo "Cron job already exists. Updating..."
    # Remove old job and add new one
    (crontab -l 2>/dev/null | grep -v "monitor_check.py"; echo "$CRON_JOB") | crontab -
else
    echo "Adding new cron job..."
    # Add new job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
fi

echo "✓ Cron job installed successfully"
echo "Monitor will run every 20 minutes"
echo "Logs will be written to: $SCRIPT_DIR/monitor.log"
echo ""
echo "To view current crontab:"
echo "  crontab -l"
echo ""
echo "To remove the cron job:"
echo "  crontab -e  # then delete the monitor_check.py line"
