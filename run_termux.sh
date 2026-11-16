#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "============================================================"
echo "  THUMBIFY — Starting on Android Termux"
echo "============================================================"

# Ensure Termux dependencies are installed
pkg install -y python libjpeg-turbo libcrypt clang

# Install python requirements
pip install -r requirements.txt

# Run the bot
echo "Starting bot..."
python -m app.main
