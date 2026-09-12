WITH source AS (

    SELECT *
    FROM {{ source('retail_raw', 'geolocation') }}

),

cleaned AS (

    SELECT
        TRIM(CAST(geolocation_zip_code_prefix AS STRING)) AS geolocation_zip_code_prefix,
        TRIM(geolocation_city) AS geolocation_city,
        LOWER(TRIM(geolocation_state)) AS geolocation_state,
        SAFE_CAST(geolocation_lat AS FLOAT64) AS latitude,
        SAFE_CAST(geolocation_lng AS FLOAT64) AS longitude

    FROM source

)

SELECT *
FROM cleaned