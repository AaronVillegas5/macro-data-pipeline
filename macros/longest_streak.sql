-- Ex: longest_daily_streak('precipitation_mm', '=', '0')
{% macro longest_streak(column_name, operator, target_value) %}

    WITH filtered_days AS (
        SELECT
            location_id,
            observation_date,
            AVG({{ column_name }}) AS {{ column_name }}
        FROM {{ ref('stg_weather_observations') }}
        GROUP BY
            location_id,
            observation_date
        HAVING {{ column_name }} {{ operator }} {{ target_value }}
    ),
    row_nums AS (
        SELECT
            *,
            ROW_NUMBER() OVER (PARTITION BY location_id ORDER BY observation_date) AS row_num
        FROM filtered_days
    ),
    streak_group AS (
        SELECT  
            *,
            DATE_SUB(observation_date, INTERVAL row_num DAY) AS grp
        FROM row_nums
    ),
    streak_count AS (
        SELECT 
            location_id,
            grp,
            COUNT(*) AS streak_length
        FROM streak_group
        GROUP BY
            location_id,
            grp
    )
    SELECT
        s.location_id,
        l.name,
        COALESCE(MAX(streak_length),0) AS longest_streak
    FROM streak_count s
    LEFT JOIN {{ ref('stg_locations')}} l
        ON l.id = s.location_id
    GROUP BY 
        s.location_id,
        l.name
    ORDER BY 
        s.location_id

{% endmacro %}
