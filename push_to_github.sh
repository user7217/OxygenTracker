#!/bin/bash

# Quick push script for future updates
# Use this script whenever you want to push changes to GitHub

echo "🔄 Pushing updates to GitHub..."

# Add all changes
git add .

# Check if there are any changes to commit
if git diff --cached --quiet; then
    echo "ℹ️  No changes to commit."
    exit 0
fi

# Get commit message from user or use default
if [ -z "$1" ]; then
    COMMIT_MSG="Update oxygen cylinder tracker - $(date '+%Y-%m-%d %H:%M')"
else
    COMMIT_MSG="$1"
fi

echo "💾 Committing with message: $COMMIT_MSG"
git commit -m "$COMMIT_MSG"

# Push to GitHub
echo "🚀 Pushing to GitHub..."
git push origin main

echo "✅ Successfully pushed to GitHub repository: github.com/user7217/OxygenTracker"