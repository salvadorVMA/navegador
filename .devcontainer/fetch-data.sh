#!/bin/bash
# Fetch private data from navegador-data repo
# This script runs during Codespace setup (postCreateCommand)

set -e

DATA_REPO="salvadorVMA/navegador_data"
DATA_FILE="encuestas_data.tar.gz"
DEST_DIR="encuestas"
CHROMA_ARCHIVE="chromadb_data.tar.gz"
CHROMA_DIR="db_f1"

echo "Fetching survey data from private repo: $DATA_REPO"

# Create destination directory
mkdir -p "$DEST_DIR"

# Download survey data using GitHub API with automatic GITHUB_TOKEN (available in Codespaces)
curl -L \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.raw" \
  "https://api.github.com/repos/$DATA_REPO/contents/$DATA_FILE" \
  -o "$DATA_FILE"

# Extract
echo "Extracting survey data..."
tar -xzvf "$DATA_FILE" -C "$DEST_DIR/"

# Cleanup
rm "$DATA_FILE"

echo "Survey data fetched successfully!"
ls -la "$DEST_DIR/"

# ──────────────────────────────────────────────
# ChromaDB setup: try pre-built archive first,
# then fall back to populate script (needs OPENAI_API_KEY).
# ──────────────────────────────────────────────
echo ""
echo "Setting up ChromaDB (enc_dbf1)..."

# Check if DB is already populated (e.g. volume-mounted or previous run)
if python3 -c "
import chromadb
from chromadb import PersistentClient
client = PersistentClient(path='$CHROMA_DIR')
c = client.get_or_create_collection('enc_dbf1')
print(c.count())
" 2>/dev/null | grep -qv '^0$'; then
    echo "ChromaDB already populated — skipping setup."
else
    # Try fetching pre-built archive from navegador_data
    echo "Attempting to fetch pre-built ChromaDB archive..."
    if curl -f -L \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.raw" \
        "https://api.github.com/repos/$DATA_REPO/contents/$CHROMA_ARCHIVE" \
        -o "$CHROMA_ARCHIVE" 2>/dev/null; then

        echo "Restoring ChromaDB from archive..."
        mkdir -p "$CHROMA_DIR"
        tar -xzf "$CHROMA_ARCHIVE"
        rm "$CHROMA_ARCHIVE"
        echo "ChromaDB restored from archive."
    else
        # Fall back: populate from scratch via OpenAI embeddings
        echo "Pre-built archive not found. Running populate_chromadb.py..."
        echo "(This requires OPENAI_API_KEY and takes ~40 minutes)"
        if [ -n "$OPENAI_API_KEY" ]; then
            python3 scripts/setup/populate_chromadb.py
        else
            echo "WARNING: OPENAI_API_KEY not set. ChromaDB will be empty."
            echo "Run 'python scripts/setup/populate_chromadb.py' manually after setting OPENAI_API_KEY."
        fi
    fi
fi
