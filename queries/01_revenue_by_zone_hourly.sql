SELECT
    PULocationID,
    EXTRACT(HOUR FROM tpep_pickup_datetime) AS pickup_hour,
    SUM(fare_amount) AS total_revenue,
    COUNT(*) AS trip_count
FROM `YOUR_PROJECT_ID.YOUR_DATASET.trips`
GROUP BY PULocationID, pickup_hour
ORDER BY total_revenue DESC
LIMIT 10;
