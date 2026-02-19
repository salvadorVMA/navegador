#!/bin/bash
# Export the populated ChromaDB to a tar.gz archive for storage in navegador_data.
#
# Run AFTER populate_chromadb.py has finished:
#   bash scripts/setup/export_chromadb.sh
#
# Then push chromadb_data.tar.gz to the navegador_data repo so future Codespaces
# restore instantly without calling OpenAI.

set -e

CHROMA_DIR="db_f1"
ARCHIVE="chromadb_data.tar.gz"

# Verify the DB is populated
COUNT=$(python3 -c "
import chromadb
from chromadb import PersistentClient
client = PersistentClient(path='$CHROMA_DIR')
c = client.get_or_create_collection('enc_dbf1')
print(c.count())
")

if [ "$COUNT" -lt 1000 ]; then
    echo "ERROR: ChromaDB has only $COUNT documents — looks unpopulated. Aborting."
    exit 1
fi

echo "ChromaDB has $COUNT documents. Creating archive..."
tar -czf "$ARCHIVE" "$CHROMA_DIR"
SIZE=$(du -sh "$ARCHIVE" | cut -f1)
echo "Created $ARCHIVE ($SIZE)"
echo ""
echo "Next step: push this archive to navegador_data repo:"
echo "  gh release upload <tag> $ARCHIVE --repo salvadorVMA/navegador_data"
echo "  OR: copy to the repo and commit/push"
echo ""
echo "Once in navegador_data as 'chromadb_data.tar.gz', future Codespaces will"
echo "restore ChromaDB from it automatically (no OpenAI API calls needed)."
