WITH sellers AS (

    SELECT
        seller_id,
        seller_zip_code_prefix,
        seller_city,
        seller_state

    FROM {{ ref('stg_sellers') }}

),

performance AS (

    SELECT
        seller_id,
        units_sold,
        order_count,
        product_count,
        total_revenue,
        total_freight,
        average_item_price,
        average_delivery_days,
        late_orders,
        total_orders,
        average_review_score,
        review_count

    FROM {{ ref('int_seller_performance') }}

),

final AS (

    SELECT
        s.seller_id,

        s.seller_zip_code_prefix,
        s.seller_city,
        s.seller_state,

        COALESCE(p.units_sold, 0) AS units_sold,
        COALESCE(p.order_count, 0) AS order_count,
        COALESCE(p.product_count, 0) AS product_count,

        COALESCE(p.total_revenue, 0) AS total_revenue,
        COALESCE(p.total_freight, 0) AS total_freight,

        p.average_item_price,

        p.average_delivery_days,

        COALESCE(p.late_orders, 0) AS late_orders,
        COALESCE(p.total_orders, 0) AS total_orders,

        p.average_review_score,
        COALESCE(p.review_count, 0) AS review_count,

        CASE
            WHEN p.total_orders > 0
            THEN SAFE_DIVIDE(p.late_orders, p.total_orders)
            ELSE NULL
        END AS late_order_rate

    FROM sellers AS s

    LEFT JOIN performance AS p
        ON s.seller_id = p.seller_id

)

SELECT *
FROM final