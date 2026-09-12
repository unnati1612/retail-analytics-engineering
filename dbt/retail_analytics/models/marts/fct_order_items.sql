WITH order_items AS (

    SELECT
        order_id,
        order_item_id,
        product_id,
        seller_id,
        shipping_limit_at,
        price,
        freight_value

    FROM {{ ref('stg_order_items') }}

),

orders AS (

    SELECT
        order_id,
        customer_id,
        customer_unique_id,
        order_status,
        purchased_at

    FROM {{ ref('int_orders_enriched') }}

),

final AS (

    SELECT
        oi.order_id,
        oi.order_item_id,

        o.customer_id,
        o.customer_unique_id,

        oi.product_id,
        oi.seller_id,

        oi.shipping_limit_at,

        o.order_status,
        o.purchased_at,

        oi.price,
        oi.freight_value,

        oi.price + oi.freight_value AS item_total_value

    FROM order_items AS oi

    LEFT JOIN orders AS o
        ON oi.order_id = o.order_id

)

SELECT *
FROM final