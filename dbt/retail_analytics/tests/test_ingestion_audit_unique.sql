SELECT
    batch_id,
    entity,
    COUNT(*) AS record_count

FROM {{ ref('mart_ingestion_monitoring') }}

GROUP BY
    batch_id,
    entity

HAVING COUNT(*) > 1