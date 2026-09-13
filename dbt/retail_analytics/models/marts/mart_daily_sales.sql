WITH daily AS (

    SELECT
        DATE(purchased_at) AS sales_date,

        COUNT(DISTINCT order_id) AS total_orders,

        COUNT(DISTINCT customer_unique_id) AS unique_customers,

        SUM(item_value) AS total_sales,

        SUM(freight_value) AS total_freight,

        SUM(payment_value) AS recorded_payment_value,

        AVG(item_value) AS average_order_value,

        AVG(delivery_days) AS average_delivery_days,

        COUNTIF(delivered_late) AS late_deliveries,

        COUNTIF(
            order_status = 'delivered'
        ) AS delivered_orders,

        COUNTIF(
            payment_count IS NOT NULL
        ) AS orders_with_payment

    FROM {{ ref('fct_orders') }}

    WHERE purchased_at IS NOT NULL

    GROUP BY
        DATE(purchased_at)

)

SELECT
    sales_date,
    total_orders,
    unique_customers,
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
    ) AS payment_coverage_rate

FROM daily