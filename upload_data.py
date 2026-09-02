import pandas as pd
from huggingface_hub import HfApi

REPO = "Abdullah81506/house-price-tool-data"
FILES = ["listings_cleaned.parquet", "listing_deviations.parquet"]

api = HfApi()
for f in FILES:
    api.upload_file(path_or_fileobj=f, path_in_repo=f,
                    repo_id=REPO, repo_type="dataset")
    print(f"{f}  ({len(pd.read_parquet(f)):,} rows)")