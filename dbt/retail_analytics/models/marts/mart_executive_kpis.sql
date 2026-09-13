WITH customer_orders AS (

    SELECT
        customer_unique_id,
        COUNT(DISTINCT order_id) AS order_count

    FROM {{ ref('fct_orders') }}

    WHERE customer_unique_id IS NOT NULL

    GROUP BY customer_unique_id

),

customer_metrics AS (

    SELECT
        COUNT(*) AS total_customers,

        COUNTIF(order_count > 1) AS repeat_customers

    FROM customer_orders

),

overall_metrics AS (

    SELECT

        COUNT(DISTINCT order_id) AS total_orders,

        COUNT(DISTINCT customer_unique_id)
            AS total_customers_with_orders,

        SUM(item_value) AS total_sales,

        SUM(freight_value) AS total_freight,

        SUM(payment_value) AS recorded_payment_value,

        AVG(item_value) AS average_order_value,

        AVG(delivery_days) AS average_delivery_days,

        COUNTIF(
            order_status = 'delivered'
            AND delivered_late = TRUE
        ) AS late_deliveries,

        COUNTIF(
            order_status = 'delivered'
        ) AS delivered_orders,

        COUNTIF(
            payment_count IS NOT NULL
        ) AS orders_with_payment

    FROM {{ ref('fct_orders') }}

)

SELECT

    total_orders,

    total_customers_with_orders,

    total_sales,

    total_freight,

    recorded_payment_value,

    average_order_value,

    average_delivery_days,

    late_deliveries,

    delivered_orders,

    orders_with_payment,

    SAFE_DIVIDE(
        orders_with_payment,
        total_orders
    ) AS payment_coverage_rate,

    SAFE_DIVIDE(
        late_deliveries,
        delivered_orders
    ) AS late_delivery_rate,

    customer_metrics.total_customers,

    customer_metrics.repeat_customers,

    SAFE_DIVIDE(
        customer_metrics.repeat_customers,
        customer_metrics.total_customers
    ) AS repeat_customer_rate

FROM overall_metrics

CROSS JOIN customer_metrics