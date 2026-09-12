WITH orders AS (

    SELECT *
    FROM {{ ref('int_orders_enriched') }}

),

final AS (

    SELECT
        order_id,
        customer_id,
        customer_unique_id,

        customer_city,
        customer_state,

        order_status,

        purchased_at,
        approved_at,
        delivered_to_carrier_at,
        delivered_to_customer_at,
        estimated_delivery_at,

        delivery_days,
        estimated_delivery_days,
        delivered_late,

        COALESCE(item_count, 0) AS item_count,
        COALESCE(item_value, 0) AS item_value,
        COALESCE(freight_value, 0) AS freight_value,
        payment_value,
        payment_count,
        

        CASE
            WHEN payment_value IS NOT NULL
                 AND item_value IS NOT NULL
            THEN payment_value - item_value
            ELSE NULL
        END AS payment_item_value_difference

    FROM orders

)

SELECT *
FROM final