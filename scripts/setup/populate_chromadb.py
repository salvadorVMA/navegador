"""
Populate ChromaDB (enc_dbf1) from los_mex_dict.json.

Reads pre-generated llm_results (summary + implication) from the JSON,
embeds them with text-embedding-ada-002, and upserts into db_f1.

Run from /workspaces/navegador:
    python scripts/setup/populate_chromadb.py
"""

import json
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import tqdm
import tiktoken
import chromadb
from chromadb import PersistentClient
from chromadb.config import Settings, DEFAULT_TENANT, DEFAULT_DATABASE
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

load_dotenv()

JSON_PATH    = Path("/workspaces/navegador/encuestas/los_mex_dict.json")
DB_PERSIST   = "./db_f1"
DB_NAME      = "enc_dbf1"
BATCH_TOKENS = 8192
ENCODING     = "cl100k_base"


def num_tokens(text: str) -> int:
    enc = tiktoken.get_encoding(ENCODING)
    return len(enc.encode(text))


def make_batches(docs, ids, metadatas, max_tokens=BATCH_TOKENS):
    batches = []
    cur_docs, cur_ids, cur_metas, cur_tok = [], [], [], 0
    for doc, did, meta in zip(docs, ids, metadatas):
        t = num_tokens(doc)
        if cur_tok + t > max_tokens and cur_docs:
            batches.append((cur_docs, cur_ids, cur_metas))
            cur_docs, cur_ids, cur_metas, cur_tok = [], [], [], 0
        cur_docs.append(doc)
        cur_ids.append(did)
        cur_metas.append(meta)
        cur_tok += t
    if cur_docs:
        batches.append((cur_docs, cur_ids, cur_metas))
    return batches


def main():
    print("Loading los_mex_dict.json ...")
    with open(JSON_PATH) as f:
        d = json.load(f)

    pregs_dict   = d["pregs_dict"]
    llm_results  = d["llm_results"]

    print(f"  {len(pregs_dict)} variables in pregs_dict")
    print(f"  {len(llm_results)} entries in llm_results")

    # Build 3-facet documents
    docs, ids, metadatas = [], [], []
    skipped = 0

    for qid, q_text in pregs_dict.items():
        entry = llm_results.get(qid, "")
        if entry == "" or entry == "incorrect" or not isinstance(entry, dict):
            skipped += 1
            continue

        summary    = str(entry.get("summary", "")).strip()
        implication = str(entry.get("implication", "")).strip()
        question   = str(q_text).strip()

        for facet, text in [
            ("question",     question),
            ("summary",      summary),
            ("implications", implication),
        ]:
            if text:
                docs.append(text)
                ids.append(f"{qid}__{facet}")
                metadatas.append({"qid": qid, "type": facet})

    print(f"  {skipped} variables skipped (no llm_results)")
    print(f"  {len(docs)} documents to embed ({len(docs)//3} variables × 3 facets)")

    # Connect to ChromaDB
    embedding_fn = OpenAIEmbeddingFunction(
        api_key=os.environ["OPENAI_API_KEY"],
        model_name="text-embedding-ada-002",
    )

    client = PersistentClient(
        path=DB_PERSIST,
        settings=Settings(allow_reset=True),
        tenant=DEFAULT_TENANT,
        database=DEFAULT_DATABASE,
    )
    db_f1 = client.get_or_create_collection(
        name=DB_NAME,
        embedding_function=embedding_fn,
    )

    existing = db_f1.count()
    print(f"\nCollection '{DB_NAME}' currently has {existing} documents.")

    # Filter out already-loaded ids to support resume
    if existing > 0:
        existing_ids = set(db_f1.get()["ids"])
        before = len(docs)
        docs, ids, metadatas = zip(
            *[(d, i, m) for d, i, m in zip(docs, ids, metadatas) if i not in existing_ids]
        ) if any(i not in existing_ids for i in ids) else ([], [], [])
        docs, ids, metadatas = list(docs), list(ids), list(metadatas)
        print(f"  {before - len(docs)} already in DB, {len(docs)} remaining to add.")

    if not docs:
        print("Nothing to add. DB is already fully populated.")
        print(f"Total vectors: {db_f1.count()}")
        return

    batches = make_batches(docs, ids, metadatas)
    print(f"\nEmbedding and loading {len(docs)} docs in {len(batches)} batches ...")

    for batch_docs, batch_ids, batch_metas in tqdm.tqdm(batches, desc="Batches"):
        embeddings = []
        for doc in tqdm.tqdm(batch_docs, desc="  Embedding", leave=False):
            emb = embedding_fn([doc])[0]
            embeddings.append(emb)

        db_f1.upsert(
            documents=batch_docs,
            ids=batch_ids,
            metadatas=batch_metas,
            embeddings=embeddings,
        )

    print(f"\nDone. Total vectors in DB: {db_f1.count()}")


if __name__ == "__main__":
    main()
