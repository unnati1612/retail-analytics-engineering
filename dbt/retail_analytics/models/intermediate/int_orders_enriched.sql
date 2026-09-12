WITH orders AS (

    SELECT
        order_id,
        customer_id,
        order_status,
        purchased_at,
        approved_at,
        delivered_to_carrier_at,
        delivered_to_customer_at,
        estimated_delivery_at
    FROM {{ ref('stg_orders') }}

),

customers AS (

    SELECT
        customer_id,
        customer_unique_id,
        customer_city,
        customer_state
    FROM {{ ref('stg_customers') }}

),

order_items AS (

    SELECT
        order_id,
        COUNT(*) AS item_count,
        SUM(price) AS item_value,
        SUM(freight_value) AS freight_value
    FROM {{ ref('stg_order_items') }}
    GROUP BY order_id

),

payments AS (

    SELECT
        order_id,
        SUM(payment_value) AS payment_value,
        COUNT(*) AS payment_count
    FROM {{ ref('stg_payments') }}
    GROUP BY order_id

),

enriched AS (

    SELECT
        o.order_id,
        o.customer_id,
        c.customer_unique_id,
        c.customer_city,
        c.customer_state,

        o.order_status,

        o.purchased_at,
        o.approved_at,
        o.delivered_to_carrier_at,
        o.delivered_to_customer_at,
        o.estimated_delivery_at,

        DATE_DIFF(
            DATE(o.delivered_to_customer_at),
            DATE(o.purchased_at),
            DAY
        ) AS delivery_days,

        DATE_DIFF(
            DATE(o.estimated_delivery_at),
            DATE(o.purchased_at),
            DAY
        ) AS estimated_delivery_days,

        CASE
            WHEN delivered_to_customer_at IS NOT NULL
                 AND estimated_delivery_at IS NOT NULL
            THEN delivered_to_customer_at > estimated_delivery_at
            ELSE NULL
        END AS delivered_late,

        oi.item_count,
        oi.item_value,
        oi.freight_value,

        p.payment_value,
        p.payment_count

    FROM orders o

    LEFT JOIN customers c
        ON o.customer_id = c.customer_id

    LEFT JOIN order_items oi
        ON o.order_id = oi.order_id

    LEFT JOIN payments p
        ON o.order_id = p.order_id

)

SELECT *
FROM enriched