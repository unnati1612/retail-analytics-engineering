WITH historical AS (

    SELECT
        CAST(customer_id AS STRING) AS customer_id,
        CAST(customer_unique_id AS STRING) AS customer_unique_id,
        CAST(customer_zip_code_prefix AS STRING) AS customer_zip_code_prefix,
        CAST(customer_city AS STRING) AS customer_city,
        CAST(customer_state AS STRING) AS customer_state,

        TIMESTAMP('1970-01-01 00:00:00') AS _source_timestamp,
        0 AS _source_priority

    FROM {{ source('retail_raw', 'customers') }}

),

api_ingest AS (

    SELECT
        CAST(customer_id AS STRING) AS customer_id,
        CAST(customer_unique_id AS STRING) AS customer_unique_id,
        CAST(customer_zip_code_prefix AS STRING) AS customer_zip_code_prefix,
        CAST(customer_city AS STRING) AS customer_city,
        CAST(customer_state AS STRING) AS customer_state,

        COALESCE(
            SAFE_CAST(updated_at AS TIMESTAMP),
            _ingested_at
        ) AS _source_timestamp,

        1 AS _source_priority

    FROM {{ source('retail_raw', '_ingest_customers') }}

),

combined AS (

    SELECT *
    FROM historical

    UNION ALL

    SELECT *
    FROM api_ingest

),

deduplicated AS (

    SELECT *
    FROM combined

    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY
            _source_priority DESC,
            _source_timestamp DESC
    ) = 1

),

cleaned AS (

    SELECT
        TRIM(customer_id) AS customer_id,
        TRIM(customer_unique_id) AS customer_unique_id,
        TRIM(customer_zip_code_prefix) AS customer_zip_code_prefix,
        TRIM(customer_city) AS customer_city,
        LOWER(TRIM(customer_state)) AS customer_state

    FROM deduplicated

)

SELECT *
FROM cleaned