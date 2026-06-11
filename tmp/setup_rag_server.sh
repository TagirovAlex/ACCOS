#!/bin/bash
set -e
echo "=== Create vector extension ==="
su - postgres -c "psql -d accos -c 'CREATE EXTENSION IF NOT EXISTS vector;'"
echo "=== Verify ==="
psql -U accos -d accos -c "SELECT name, installed_version FROM pg_available_extensions WHERE name='vector';"
echo "=== Install Tesseract ==="
apt-get install -y -qq tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng
echo "=== Verify Tesseract ==="
tesseract --list-langs
echo "=== Done ==="
