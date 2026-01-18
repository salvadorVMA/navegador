### Utility functions for environment setup and database configuration, model calls, and token management

from dotenv import load_dotenv
import os

from chromadb import PersistentClient                            
from chromadb.config import Settings, DEFAULT_TENANT, DEFAULT_DATABASE 
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from openai import OpenAI

import tiktoken
import re

from performance_optimization import cached_llm_call, DatabaseManager, performance_monitor


embedding_fun_openai = OpenAIEmbeddingFunction(api_key=os.environ.get('OPENAI_API_KEY'), model_name="text-embedding-ada-002")    


def environment_setup(embedding_fun_openai, DB_PERSIST_DIR = "./db_f1", DB_NAME = "enc_dbf1"):
    """
    Set up the environment variables and configurations for the application.
    This function loads the environment variables from a .env file.
    """

    print("*****************************************************")
    print("Setting up environment...")

    ## Load environment variables
    load_dotenv()

    client = OpenAI()

    client.embeddings.create(
    model='text-embedding-3-large', 
    input="The food was delicious and the waiter...",
    encoding_format="float"
    )


    ## ChromaDB client setup
    client = PersistentClient(
        path     = DB_PERSIST_DIR,
        settings = Settings(allow_reset=True),   # allow resetting on-disk state
        tenant   = DEFAULT_TENANT,
        database = DEFAULT_DATABASE,
    ) 

    print("Collections:", [c.name for c in client.list_collections()])  

    db_f1 = client.get_or_create_collection(
        name               = DB_NAME,
        embedding_function = embedding_fun_openai
    )

    print(f"peek a db_f1:\n{db_f1.peek()}\n")

    print("Environment setup complete.")
    print("*****************************************************")

    return client, db_f1

# contador de tokens y batcher 


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    # Utility function to calculate the number of tokens in a string.
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

# Update the token count calculation in batch_documents to use num_tokens_from_string
# 8192 is the token limit for the model
def batch_documents(docs, ids, max_tokens=8192, encoding_name="cl100k_base"):
    # This function batches documents and their IDs while respecting the token limit.
    # It ensures that each batch does not exceed the maximum token limit,
    # which is crucial for efficient processing with the LLM.
    batches = []
    current_batch_docs = []
    current_batch_ids = []
    current_token_count = 0

    for doc, doc_id in zip(docs, ids):
        doc_token_count = num_tokens_from_string(doc, encoding_name)  # Use the token counting function
        
        # print(f"Document ID: {doc_id}, Token Count: {doc_token_count}")
        
        if current_token_count + doc_token_count > max_tokens:
            # Save the current batch and start a new one
            batches.append((current_batch_docs, current_batch_ids))
            current_batch_docs = []
            current_batch_ids = []
            current_token_count = 0

        # Add the document to the current batch
        current_batch_docs.append(doc)
        current_batch_ids.append(doc_id)
        current_token_count += doc_token_count

    # Add the last batch if it has any documents
    if current_batch_docs:
        batches.append((current_batch_docs, current_batch_ids))

    return batches

# llamdas a LLM y limpieza de salida a json
# NOW WITH CACHING ENABLED via @cached_llm_call decorator (imported from performance_optimization)
@cached_llm_call
def get_answer(prompt, system_prompt=None, model='gpt-4o-mini-2024-07-18', temperature=0.9):
    # This function sends the prompt to the LLM and retrieves the response.
    # Caching is automatically applied - identical prompts will return cached results
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user",   "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content


def clean_llm_json_output(content):
    # Remove code block markers and any leading/trailing text
    content = content.strip()
    # Remove code block markers
    content = re.sub(r"^```json", "", content, flags=re.IGNORECASE).strip()
    content = re.sub(r"^```", "", content, flags=re.IGNORECASE).strip()
    content = re.sub(r"```$", "", content, flags=re.IGNORECASE).strip()
    # Remove any leading text before the first {
    idx = content.find('{')
    if idx > 0:
        content = content[idx:]
    # Remove trailing text after last }
    idx2 = content.rfind('}')
    if idx2 > 0:
        content = content[:idx2+1]
    return content

# Import performance optimization components
from performance_optimization import cached_llm_call, DatabaseManager, performance_monitor

# Apply caching decorator to get_answer function
@cached_llm_call
def get_answer_optimized(prompt, system_prompt=None, model='gpt-4o-mini-2024-07-18', temperature=0.9):
    """Optimized version of get_answer with caching."""
    # Record the LLM call for monitoring
    performance_monitor.record_llm_call(cached=False)  # Will be overridden by cache if hit
    
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user",   "content": prompt})
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content


def environment_setup_optimized(embedding_fun_openai, DB_PERSIST_DIR="./db_f1", DB_NAME="enc_dbf1"):
    """Optimized environment setup using singleton pattern."""
    db_manager = DatabaseManager()
    return db_manager.get_client()


# Batch processing wrapper
def batch_llm_calls(requests: list, llm_function=None) -> list:
    """Process multiple LLM requests in parallel."""
    from performance_optimization import LLMBatchProcessor
    
    if llm_function is None:
        llm_function = get_answer_optimized
    
    processor = LLMBatchProcessor(max_workers=3)
    return processor.process_batch(requests, llm_function)

