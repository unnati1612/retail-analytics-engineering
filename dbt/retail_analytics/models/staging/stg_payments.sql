WITH historical AS (

    SELECT
        order_id,
        payment_sequential,
        payment_type,
        payment_installments,
        payment_value,

        TIMESTAMP('1970-01-01 00:00:00') AS _source_timestamp,
        0 AS _source_priority

    FROM {{ source('retail_raw', 'payments') }}

),

api_ingest AS (

    SELECT
        order_id,
        payment_sequential,
        payment_type,
        payment_installments,
        payment_value,

        _ingested_at AS _source_timestamp,
        1 AS _source_priority

    FROM {{ source('retail_raw', '_ingest_payments') }}

),

combined AS (

    SELECT * FROM historical

    UNION ALL

    SELECT * FROM api_ingest

),

deduplicated AS (

    SELECT *
    FROM combined

    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY order_id, payment_sequential
        ORDER BY
            _source_priority DESC,
            _source_timestamp DESC
    ) = 1

)

SELECT
    TRIM(order_id) AS order_id,
    SAFE_CAST(payment_sequential AS INT64) AS payment_sequential,
    LOWER(TRIM(payment_type)) AS payment_type,
    SAFE_CAST(payment_installments AS INT64) AS payment_installments,
    SAFE_CAST(payment_value AS NUMERIC) AS payment_value

FROM deduplicated