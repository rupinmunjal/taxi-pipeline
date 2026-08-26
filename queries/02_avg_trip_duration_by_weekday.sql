SELECT
    FORMAT_DATE('%A', pickup_date) AS weekday_name,
    AVG(trip_duration) AS avg_trip_duration
FROM `YOUR_PROJECT_ID.YOUR_DATASET.trips`
GROUP BY weekday_name
ORDER BY avg_trip_duration DESC
LIMIT 7;
