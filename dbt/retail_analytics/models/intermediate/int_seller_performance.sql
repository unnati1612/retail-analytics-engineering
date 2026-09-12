WITH seller_items AS (

    SELECT
        seller_id,
        order_id,
        product_id,
        price,
        freight_value
    FROM {{ ref('stg_order_items') }}

),

seller_sales AS (

    SELECT
        seller_id,

        COUNT(*) AS units_sold,

        COUNT(DISTINCT order_id) AS order_count,

        COUNT(DISTINCT product_id) AS product_count,

        SUM(price) AS total_revenue,

        SUM(freight_value) AS total_freight,

        AVG(price) AS average_item_price

    FROM seller_items

    GROUP BY seller_id

),

seller_orders AS (

    SELECT
        oi.seller_id,
        o.order_id,
        o.purchased_at,
        o.delivered_to_customer_at,
        o.delivery_days,
        o.delivered_late

    FROM {{ ref('stg_order_items') }} oi

    INNER JOIN {{ ref('int_orders_enriched') }} o
        ON oi.order_id = o.order_id

    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY oi.seller_id, o.order_id
        ORDER BY o.purchased_at
    ) = 1

),

seller_delivery AS (

    SELECT
        seller_id,

        AVG(delivery_days) AS average_delivery_days,

        COUNTIF(delivered_late) AS late_orders,

        COUNT(*) AS total_orders

    FROM seller_orders

    GROUP BY seller_id

),

seller_reviews AS (

    SELECT
        oi.seller_id,
        r.order_id,
        r.review_score

    FROM {{ ref('stg_order_items') }} oi

    INNER JOIN {{ ref('stg_reviews') }} r
        ON oi.order_id = r.order_id

    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY oi.seller_id, r.order_id, r.review_id
        ORDER BY r.review_created_at
    ) = 1

),

seller_review_metrics AS (

    SELECT
        seller_id,

        AVG(review_score) AS average_review_score,

        COUNT(*) AS review_count

    FROM seller_reviews

    GROUP BY seller_id

),

final AS (

    SELECT
        s.seller_id,

        s.units_sold,
        s.order_count,
        s.product_count,

        s.total_revenue,
        s.total_freight,
        s.average_item_price,

        d.average_delivery_days,
        d.late_orders,
        d.total_orders,

        r.average_review_score,
        r.review_count

    FROM seller_sales s

    LEFT JOIN seller_delivery d
        ON s.seller_id = d.seller_id

    LEFT JOIN seller_review_metrics r
        ON s.seller_id = r.seller_id

)

SELECT *
FROM final