WITH orders AS (

    SELECT
        order_id,
        customer_id,
        customer_unique_id,
        customer_city,
        customer_state,
        order_status,
        purchased_at,
        delivered_to_customer_at,
        delivery_days,
        estimated_delivery_days,
        delivered_late,
        item_count,
        item_value,
        freight_value,
        payment_value,

    FROM {{ ref('int_orders_enriched') }}

),

customer_orders AS (

    SELECT
        customer_unique_id,
        customer_id,

        order_id,
        order_status,

        customer_city,
        customer_state,

        purchased_at,
        delivered_to_customer_at,

        delivery_days,
        estimated_delivery_days,

        item_count,
        item_value,
        freight_value,
        payment_value,

        delivered_late

    FROM orders

)

SELECT *
FROM customer_orders