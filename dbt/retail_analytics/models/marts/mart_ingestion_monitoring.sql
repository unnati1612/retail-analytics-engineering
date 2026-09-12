WITH audit AS (

    SELECT
        batch_id,
        entity,
        started_at,
        completed_at,
        records_fetched,
        records_loaded,
        watermark_before,
        watermark_after,
        status,
        error_message,

        TIMESTAMP_DIFF(
            completed_at,
            started_at,
            SECOND
        ) AS duration_seconds

    FROM {{ source('retail_raw', 'ingestion_audit') }}

)

SELECT
    batch_id,
    entity,
    started_at,
    completed_at,
    records_fetched,
    records_loaded,
    duration_seconds,
    watermark_before,
    watermark_after,
    status,
    error_message,

    CASE
        WHEN status = 'SUCCESS'
             AND records_loaded > 0
            THEN 'SUCCESS_WITH_DATA'

        WHEN status = 'SUCCESS'
             AND records_loaded = 0
            THEN 'SUCCESS_NO_NEW_DATA'

        WHEN status = 'FAILED'
            THEN 'FAILED'

        ELSE 'UNKNOWN'
    END AS ingestion_result

FROM audit