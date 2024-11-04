#!/bin/bash

# Script to clean up outdated data from specified directories.

# Directories to clean up
DATA_DIRECTORIES=(
    "/data/storage1"
    "/data/storage2"
    "/data/storage3"
)

# Number of days before data is considered outdated
RETENTION_DAYS=30

# Log file for cleanup operations
LOG_FILE="/var/log/data_cleanup.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

log_message "Starting cleanup process."

# Loop through each directory and remove files older than RETENTION_DAYS
for DIR in "${DATA_DIRECTORIES[@]}"; do
    if [ -d "$DIR" ]; then
        log_message "Cleaning up directory: $DIR"
        
        # Find and remove files older than RETENTION_DAYS
        find "$DIR" -type f -mtime +"$RETENTION_DAYS" -exec rm -f {} \;

        if [ $? -eq 0 ]; then
            log_message "Successfully cleaned up files older than $RETENTION_DAYS days in $DIR"
        else
            log_message "Error cleaning up $DIR"
        fi
    else
        log_message "Directory $DIR does not exist."
    fi
done

log_message "Cleanup process completed."