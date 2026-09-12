CREATE TABLE IF NOT EXISTS `retail-analytics-engineering.retail_raw.ingestion_audit`
(
    batch_id STRING NOT NULL,
    entity STRING NOT NULL,

    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,

    records_fetched INT64,
    records_loaded INT64,

    watermark_before TIMESTAMP,
    watermark_after TIMESTAMP,

    status STRING NOT NULL,
    error_message STRING
);