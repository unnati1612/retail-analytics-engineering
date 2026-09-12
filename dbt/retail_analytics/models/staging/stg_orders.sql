WITH historical AS (

    SELECT
        order_id,
        customer_id,
        order_status,
        order_purchase_timestamp,
        order_approved_at,
        order_delivered_carrier_date,
        order_delivered_customer_date,
        order_estimated_delivery_date,

        TIMESTAMP('1970-01-01 00:00:00') AS _source_timestamp,
        0 AS _source_priority

    FROM {{ source('retail_raw', 'orders') }}

),

api_ingest AS (

    SELECT
        order_id,
        customer_id,
        order_status,
        order_purchase_timestamp,
        order_approved_at,
        order_delivered_carrier_date,
        order_delivered_customer_date,
        order_estimated_delivery_date,

        _ingested_at AS _source_timestamp,
        1 AS _source_priority

    FROM {{ source('retail_raw', '_ingest_orders') }}

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
        PARTITION BY order_id
        ORDER BY
            _source_priority DESC,
            _source_timestamp DESC
    ) = 1

),

cleaned AS (

    SELECT
        TRIM(order_id) AS order_id,
        TRIM(customer_id) AS customer_id,
        LOWER(TRIM(order_status)) AS order_status,

        TIMESTAMP(order_purchase_timestamp) AS purchased_at,
        TIMESTAMP(order_approved_at) AS approved_at,
        TIMESTAMP(order_delivered_carrier_date) AS delivered_to_carrier_at,
        TIMESTAMP(order_delivered_customer_date) AS delivered_to_customer_at,
        TIMESTAMP(order_estimated_delivery_date) AS estimated_delivery_at

    FROM deduplicated

)

SELECT *
FROM cleaned