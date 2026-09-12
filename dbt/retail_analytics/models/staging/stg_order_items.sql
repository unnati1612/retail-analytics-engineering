WITH historical AS (

    SELECT
        order_id,
        order_item_id,
        product_id,
        seller_id,
        shipping_limit_date,
        price,
        freight_value,

        TIMESTAMP('1970-01-01 00:00:00') AS _source_timestamp,
        0 AS _source_priority

    FROM {{ source('retail_raw', 'order_items') }}

),

api_ingest AS (

    SELECT
        order_id,
        order_item_id,
        product_id,
        seller_id,
        shipping_limit_date,
        price,
        freight_value,

        _ingested_at AS _source_timestamp,
        1 AS _source_priority

    FROM {{ source('retail_raw', '_ingest_order_items') }}

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
        PARTITION BY order_id, order_item_id
        ORDER BY
            _source_priority DESC,
            _source_timestamp DESC
    ) = 1

)

SELECT
    TRIM(order_id) AS order_id,
    SAFE_CAST(order_item_id AS INT64) AS order_item_id,
    TRIM(product_id) AS product_id,
    TRIM(seller_id) AS seller_id,
    TIMESTAMP(shipping_limit_date) AS shipping_limit_at,
    SAFE_CAST(price AS NUMERIC) AS price,
    SAFE_CAST(freight_value AS NUMERIC) AS freight_value

FROM deduplicated