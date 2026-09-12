from google.cloud import bigquery

client = bigquery.Client()

dataset_id = f"{client.project}.retail_staging"

dataset = bigquery.Dataset(dataset_id)
dataset.location = "US"

client.create_dataset(
    dataset,
    exists_ok=True
)

print(f"Created: {dataset_id}")