"""Module for managing dataset information and metadata"""

# Example dataset information - in a real implementation, this could come from a database
DATASETS = {
    "customer_data": {
        "description": "Customer demographic and transaction data",
        "variables": [
            "customer_id", "age", "gender", "income", "location", 
            "purchase_history", "purchase_amount", "purchase_date"
        ],
        "size": "1.2M records",
        "last_updated": "2025-03-15"
    },
    "product_data": {
        "description": "Product catalog with specifications and reviews",
        "variables": [
            "product_id", "name", "category", "price", "cost", 
            "supplier", "stock_level", "review_score", "review_count"
        ],
        "size": "50K records",
        "last_updated": "2025-04-01"
    },
    "marketing_campaigns": {
        "description": "Marketing campaign performance data",
        "variables": [
            "campaign_id", "channel", "start_date", "end_date", 
            "budget", "spend", "impressions", "clicks", "conversions",
            "roi", "target_audience"
        ],
        "size": "500 campaigns",
        "last_updated": "2025-03-28"
    }
}

def list_datasets() -> str:
    """Return a formatted list of all available datasets"""
    result = []
    
    for name, info in DATASETS.items():
        result.append(f"- {name}: {info['description']}")
        
    return "\n".join(result)

def get_dataset_info(dataset_name: str) -> str:
    """Get detailed information about a specific dataset"""
    if dataset_name.lower() not in DATASETS:
        return f"Dataset '{dataset_name}' not found in the system."
    
    dataset = DATASETS[dataset_name.lower()]
    
    info = [
        f"Dataset: {dataset_name}",
        f"Description: {dataset['description']}",
        f"Size: {dataset['size']}",
        f"Last Updated: {dataset['last_updated']}",
        "\nVariables:",
    ]
    
    for var in dataset['variables']:
        info.append(f"- {var}")
    
    return "\n".join(info)

def get_variables(dataset_name: str) -> list:
    """Return the list of variables for a specific dataset"""
    if dataset_name.lower() not in DATASETS:
        return []
    
    return DATASETS[dataset_name.lower()]['variables']
