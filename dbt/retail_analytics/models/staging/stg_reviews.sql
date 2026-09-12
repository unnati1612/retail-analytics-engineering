WITH historical AS (

    SELECT
        review_id,
        order_id,
        review_score,
        review_comment_title,
        review_comment_message,
        review_creation_date,
        review_answer_timestamp,

        TIMESTAMP('1970-01-01 00:00:00') AS _source_timestamp,
        0 AS _source_priority

    FROM {{ source('retail_raw', 'reviews') }}

),

api_ingest AS (

    SELECT
        review_id,
        order_id,
        review_score,
        review_comment_title,
        review_comment_message,
        review_creation_date,
        review_answer_timestamp,

        _ingested_at AS _source_timestamp,
        1 AS _source_priority

    FROM {{ source('retail_raw', '_ingest_reviews') }}

),

combined AS (

    SELECT * FROM historical

    UNION ALL

    SELECT * FROM api_ingest

),

deduplicated AS (

    SELECT *
    FROM combined

    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY review_id, order_id
        ORDER BY
            _source_priority DESC,
            _source_timestamp DESC
    ) = 1

)

SELECT
    TRIM(review_id) AS review_id,
    TRIM(order_id) AS order_id,
    SAFE_CAST(review_score AS INT64) AS review_score,
    TRIM(review_comment_title) AS review_comment_title,
    TRIM(review_comment_message) AS review_comment_message,
    TIMESTAMP(review_creation_date) AS review_created_at,
    TIMESTAMP(review_answer_timestamp) AS review_answered_at

FROM deduplicated