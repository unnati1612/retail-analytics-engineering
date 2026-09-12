from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from google.cloud import bigquery


AUDIT_TABLE = (
    "retail-analytics-engineering"
    ".retail_raw.ingestion_audit"
)


def write_audit_record(
    client: bigquery.Client,
    *,
    batch_id: str,
    entity: str,
    started_at: datetime,
    completed_at: datetime,
    records_fetched: int,
    records_loaded: int,
    watermark_before: Optional[str],
    watermark_after: Optional[str],
    status: str,
    error_message: Optional[str] = None,
) -> None:
    """
    Append one immutable ingestion audit record.

    Uses a BigQuery load job rather than UPDATE/MERGE so that
    it remains compatible with BigQuery Sandbox.
    """

    row = {
        "batch_id": batch_id,
        "entity": entity,
        "started_at": started_at.astimezone(timezone.utc).isoformat(),
        "completed_at": completed_at.astimezone(timezone.utc).isoformat(),
        "records_fetched": records_fetched,
        "records_loaded": records_loaded,
        "watermark_before": watermark_before,
        "watermark_after": watermark_after,
        "status": status,
        "error_message": error_message,
    }

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    job = client.load_table_from_json(
        [row],
        AUDIT_TABLE,
        job_config=job_config,
    )

    job.result()