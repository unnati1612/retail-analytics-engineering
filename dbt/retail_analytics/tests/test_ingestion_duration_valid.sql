SELECT
    batch_id,
    entity,
    started_at,
    completed_at,
    duration_seconds

FROM {{ ref('mart_ingestion_monitoring') }}

WHERE completed_at < started_at
   OR duration_seconds < 0