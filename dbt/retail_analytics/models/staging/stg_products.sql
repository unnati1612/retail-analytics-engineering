WITH historical AS (

    SELECT
        product_id,
        product_category_name,
        product_name_lenght,
        product_description_lenght,
        product_photos_qty,
        product_weight_g,
        product_length_cm,
        product_height_cm,
        product_width_cm,

        TIMESTAMP('1970-01-01 00:00:00') AS _source_timestamp,
        0 AS _source_priority

    FROM {{ source('retail_raw', 'products') }}

),

api_ingest AS (

    SELECT
        product_id,
        product_category_name,
        product_name_lenght,
        product_description_lenght,
        product_photos_qty,
        product_weight_g,
        product_length_cm,
        product_height_cm,
        product_width_cm,

        _ingested_at AS _source_timestamp,
        1 AS _source_priority

    FROM {{ source('retail_raw', '_ingest_products') }}

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
        PARTITION BY product_id
        ORDER BY
            _source_priority DESC,
            _source_timestamp DESC
    ) = 1

)

SELECT
    TRIM(product_id) AS product_id,
    SAFE_CAST(product_category_name AS STRING) AS product_category_name,
    SAFE_CAST(product_name_lenght AS INT64) AS product_name_length,
    SAFE_CAST(product_description_lenght AS INT64) AS product_description_length,
    SAFE_CAST(product_photos_qty AS INT64) AS product_photos_qty,
    SAFE_CAST(product_weight_g AS NUMERIC) AS product_weight_g,
    SAFE_CAST(product_length_cm AS NUMERIC) AS product_length_cm,
    SAFE_CAST(product_height_cm AS NUMERIC) AS product_height_cm,
    SAFE_CAST(product_width_cm AS NUMERIC) AS product_width_cm

FROM deduplicated