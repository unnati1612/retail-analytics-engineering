{{ config(
    severity = 'warn'
) }}

SELECT
    o.order_id,
    o.order_status,
    o.purchased_at

FROM {{ ref('fct_orders') }} o

WHERE o.order_status = 'delivered'
  AND o.payment_count IS NULL