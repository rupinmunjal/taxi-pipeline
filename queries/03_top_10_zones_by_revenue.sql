WITH all_zone_activity AS (
    SELECT PULocationID AS zone_id, total_amount, 'pickup' AS event_type
    FROM `YOUR_PROJECT_ID.YOUR_DATASET.trips`
    WHERE PULocationID IS NOT NULL

    UNION ALL

    SELECT DOLocationID AS zone_id, total_amount, 'dropoff' AS event_type
    FROM `YOUR_PROJECT_ID.YOUR_DATASET.trips`
    WHERE DOLocationID IS NOT NULL
)

SELECT
    zone_id,
    SUM(total_amount) AS revenue,
    COUNT(*) AS total_events,
    COUNTIF(event_type = 'pickup') AS pickup_count,
    COUNTIF(event_type = 'dropoff') AS dropoff_count
FROM all_zone_activity
GROUP BY zone_id
ORDER BY revenue DESC
LIMIT 10;
