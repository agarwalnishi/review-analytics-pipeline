"""Registry of data sources. Add a new dataset here; nothing else needs to change.

Each source lists:
- categories: which slices of the dataset to pull
- files: one URL template per kind of file ({category} gets filled in)
"""

SOURCES = {
    "amazon_reviews_2023": {
        "description": "Public e-commerce reviews dataset (McAuley Lab, UC San Diego)",
        "categories": ["All_Beauty", "Appliances"],
        "files": {
            "reviews": "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/review_categories/{category}.jsonl.gz",
            "products": "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/meta_categories/meta_{category}.jsonl.gz",
        },
    },
    # Example of how a second source would plug in:
    # "my_other_source": {
    #     "description": "...",
    #     "categories": ["electronics"],
    #     "files": {
    #         "reviews": "https://example.com/{category}/reviews.jsonl.gz",
    #         "products": "https://example.com/{category}/products.jsonl.gz",
    #     },
    # },
}