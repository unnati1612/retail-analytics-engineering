WITH customer_orders AS (

    SELECT
        customer_unique_id,
        order_id,
        purchased_at,
        order_status,
        payment_value

    FROM {{ ref('int_customer_orders') }}

),

delivered_orders AS (

    SELECT
        customer_unique_id,
        order_id,
        purchased_at,
        payment_value

    FROM customer_orders

    WHERE order_status = 'delivered'

),

rfm_base AS (

    SELECT
        customer_unique_id,

        MAX(purchased_at) AS last_purchase_at,

        COUNT(DISTINCT order_id) AS frequency,

        SUM(COALESCE(payment_value, 0)) AS monetary

    FROM delivered_orders

    GROUP BY customer_unique_id

),

analysis_date AS (

    SELECT
        MAX(purchased_at) AS analysis_date
    FROM delivered_orders

),

rfm_metrics AS (

    SELECT
        r.customer_unique_id,

        DATE_DIFF(
            DATE(a.analysis_date),
            DATE(r.last_purchase_at),
            DAY
        ) AS recency,

        r.frequency,
        r.monetary,

        r.last_purchase_at,

        a.analysis_date

    FROM rfm_base r

    CROSS JOIN analysis_date a

),

rfm_scores AS (

    SELECT
        *,

        NTILE(5) OVER (
            ORDER BY recency DESC
        ) AS recency_score,

        NTILE(5) OVER (
            ORDER BY frequency
        ) AS frequency_score,

        NTILE(5) OVER (
            ORDER BY monetary
        ) AS monetary_score

    FROM rfm_metrics

),

final AS (

    SELECT
        customer_unique_id,

        last_purchase_at,
        analysis_date,

        recency,
        frequency,
        monetary,

        recency_score,
        frequency_score,
        monetary_score,

        CONCAT(
            CAST(recency_score AS STRING),
            CAST(frequency_score AS STRING),
            CAST(monetary_score AS STRING)
        ) AS rfm_score,

        CASE

            WHEN recency_score >= 4
                 AND frequency_score >= 4
                 AND monetary_score >= 4
            THEN 'Champions'

            WHEN recency_score >= 3
                 AND frequency_score >= 4
                 AND monetary_score >= 3
            THEN 'Loyal Customers'

            WHEN recency_score >= 4
                 AND frequency_score <= 2
            THEN 'New Customers'

            WHEN recency_score <= 2
                 AND frequency_score >= 3
            THEN 'At Risk'

            WHEN recency_score <= 2
                 AND frequency_score <= 2
            THEN 'Hibernating'

            ELSE 'Potential Loyalists'

        END AS customer_segment

    FROM rfm_scores

)

SELECT *
FROM final