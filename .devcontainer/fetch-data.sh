#!/bin/bash
# Fetch private data from navegador-data repo
# This script runs during Codespace setup (postCreateCommand)

set -e

DATA_REPO="salvadorVMA/navegador_data"
DATA_FILE="encuestas_data.tar.gz"
DEST_DIR="encuestas"

echo "Fetching data from private repo: $DATA_REPO"

# Create destination directory
mkdir -p "$DEST_DIR"

# Download using GitHub API with automatic GITHUB_TOKEN (available in Codespaces)
curl -L \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.raw" \
  "https://api.github.com/repos/$DATA_REPO/contents/$DATA_FILE" \
  -o "$DATA_FILE"

# Extract
echo "Extracting data..."
tar -xzvf "$DATA_FILE" -C "$DEST_DIR/"

# Cleanup
rm "$DATA_FILE"

echo "Data fetched successfully!"
ls -la "$DEST_DIR/"
