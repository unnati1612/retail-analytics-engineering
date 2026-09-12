WITH customer_orders AS (

    SELECT *
    FROM {{ ref('int_customer_orders') }}

),

customer_summary AS (

    SELECT
        customer_unique_id,

        ARRAY_AGG(
            customer_city
            IGNORE NULLS
            ORDER BY purchased_at
            LIMIT 1
        )[SAFE_OFFSET(0)] AS customer_city,

        ARRAY_AGG(
            customer_state
            IGNORE NULLS
            ORDER BY purchased_at
            LIMIT 1
        )[SAFE_OFFSET(0)] AS customer_state,

        MIN(purchased_at) AS first_order_at,

        MAX(purchased_at) AS last_order_at,

        COUNT(DISTINCT order_id) AS total_orders,

        SUM(COALESCE(item_count, 0)) AS total_items,

        SUM(COALESCE(payment_value, 0)) AS total_spend,

        AVG(payment_value) AS average_order_value,

        COUNTIF(order_status = 'delivered') AS delivered_orders,

        COUNTIF(order_status = 'canceled') AS cancelled_orders,

        COUNTIF(delivered_late = TRUE) AS late_orders

    FROM customer_orders

    GROUP BY customer_unique_id

),

final AS (

    SELECT
        customer_unique_id,

        customer_city,
        customer_state,

        first_order_at,
        last_order_at,

        total_orders,
        total_items,
        total_spend,
        average_order_value,

        delivered_orders,
        cancelled_orders,
        late_orders

    FROM customer_summary

)

SELECT *
FROM final