WITH products AS (

    SELECT
        product_id,
        product_category_name,
        product_name_length,
        product_description_length,
        product_photos_qty,
        product_weight_g,
        product_length_cm,
        product_height_cm,
        product_width_cm

    FROM {{ ref('stg_products') }}

),

sales AS (

    SELECT
        product_id,
        units_sold,
        order_count,
        total_revenue,
        total_freight,
        average_item_price

    FROM {{ ref('int_product_sales') }}

),

final AS (

    SELECT
        p.product_id,

        COALESCE(
            NULLIF(TRIM(p.product_category_name), ''),
            'unknown'
        ) AS product_category_name,

        p.product_name_length,
        p.product_description_length,
        p.product_photos_qty,

        p.product_weight_g,
        p.product_length_cm,
        p.product_height_cm,
        p.product_width_cm,

        COALESCE(s.units_sold, 0) AS units_sold,
        COALESCE(s.order_count, 0) AS order_count,
        COALESCE(s.total_revenue, 0) AS total_revenue,
        COALESCE(s.total_freight, 0) AS total_freight,
        COALESCE(s.average_item_price, 0) AS average_item_price

    FROM products AS p

    LEFT JOIN sales AS s
        ON p.product_id = s.product_id

)

SELECT *
FROM final