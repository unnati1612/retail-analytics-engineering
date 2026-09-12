SELECT
    batch_id,
    entity,
    records_fetched,
    records_loaded

FROM {{ ref('mart_ingestion_monitoring') }}

WHERE records_fetched < 0
   OR records_loaded < 0
   OR records_loaded > records_fetched