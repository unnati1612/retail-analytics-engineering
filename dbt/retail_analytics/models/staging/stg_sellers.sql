WITH historical AS (

    SELECT
        seller_id,
        seller_zip_code_prefix,
        seller_city,
        seller_state,

        TIMESTAMP('1970-01-01 00:00:00') AS _source_timestamp,
        0 AS _source_priority

    FROM {{ source('retail_raw', 'sellers') }}

),

api_ingest AS (

    SELECT
        seller_id,
        seller_zip_code_prefix,
        seller_city,
        seller_state,

        _ingested_at AS _source_timestamp,
        1 AS _source_priority

    FROM {{ source('retail_raw', '_ingest_sellers') }}

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
        PARTITION BY seller_id
        ORDER BY
            _source_priority DESC,
            _source_timestamp DESC
    ) = 1

)

SELECT
    TRIM(seller_id) AS seller_id,
    CAST(seller_zip_code_prefix AS STRING) AS seller_zip_code_prefix,
    TRIM(seller_city) AS seller_city,
    LOWER(TRIM(seller_state)) AS seller_state

FROM deduplicated