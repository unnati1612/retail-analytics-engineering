from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any
from uuid import uuid4

from google.cloud import bigquery


class BigQueryLoader:
    """
    BigQuery Sandbox-compatible append-only ingestion loader.

    IMPORTANT: This loader is designed for BigQuery Sandbox, which does NOT support DML
    operations (MERGE, UPDATE, DELETE). This implementation:
    
    1. ONLY appends to _ingest_<entity> tables.
    2. NEVER modifies retail_raw.<entity> tables (preserves historical Olist data).
    3. Adds metadata to every ingested row for auditability and deduplication downstream.
    4. Is safe to retry without creating duplicates (via _record_hash).
    
    Deduplication happens in dbt, not in Python/BigQuery.
    """

    def __init__(
        self,
        project_id: str,
        dataset: str,
    ):
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id
        self.dataset = dataset

    def _table_id(self, table: str) -> str:
        return f"{self.project_id}.{self.dataset}.{table}"

    def _compute_record_hash(self, key_values: list[str | int]) -> str:
        """
        Compute a deterministic SHA-256 hash from business key components.
        
        This hash identifies the logical record, independent of ingestion metadata.
        Same business key always produces same hash (idempotency).
        
        Args:
            key_values: Ordered list of business key components (as strings).
        
        Returns:
            Hex-encoded SHA-256 hash.
        """
        key_str = "|".join(str(v) for v in key_values)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def append_batch(
        self,
        rows: list[dict[str, Any]],
        ingest_table: str,
        key_columns: list[str],
        batch_id: str | None = None,
    ) -> str:
        """
        Append a batch of records to an _ingest_<entity> table with metadata.
        
        This is the ONLY BigQuery operation performed by the ingestion layer.
        Uses WRITE_APPEND to ensure append-only semantics (Sandbox-safe).
        
        Args:
            rows: List of record dicts to append.
            ingest_table: Ingest table name (e.g., '_ingest_customers').
            key_columns: Business key column names (used to compute _record_hash).
            batch_id: Optional batch identifier. Generated if not provided.
        
        Returns:
            The batch_id used for this load.
        
        Raises:
            Exception: If BigQuery load job fails.
        """
        if not rows:
            return batch_id or str(uuid4())

        if batch_id is None:
            batch_id = str(uuid4())

        ingest_table_id = self._table_id(ingest_table)
        now_utc = datetime.utcnow().isoformat() + "Z"

        # Enrich each row with metadata.
        enriched_rows = []
        for row in rows:
            # Compute record hash from business key.
            key_values = [row.get(col) for col in key_columns]
            record_hash = self._compute_record_hash(key_values)

            enriched_row = {
                **row,
                "_batch_id": batch_id,
                "_ingested_at": now_utc,
                "_record_hash": record_hash,
            }
            enriched_rows.append(enriched_row)

        # Load with WRITE_APPEND (Sandbox-safe, no DML).
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            autodetect=True,
        )

        job = self.client.load_table_from_json(
            enriched_rows,
            ingest_table_id,
            job_config=job_config,
        )

        job.result()

        return batch_id