WITH order_items AS (

    SELECT
        order_id,
        product_id,
        seller_id,
        price,
        freight_value
    FROM {{ ref('stg_order_items') }}

),

product_sales AS (

    SELECT
        product_id,

        COUNT(*) AS units_sold,

        COUNT(DISTINCT order_id) AS order_count,

        SUM(price) AS total_revenue,

        SUM(freight_value) AS total_freight,

        AVG(price) AS average_item_price

    FROM order_items

    GROUP BY product_id

)

SELECT *
FROM product_sales