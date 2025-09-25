# Methodology for Generating Standard Traffic Profiles

This document details the process and justification for creating the `standard_24h_profile.json` and `standard_turning_profile.json` files from the provided `foi_transcript.csv`.

## 1. The Data Gap

The source CSV file provides traffic data for three periods:
1.  **Total Volume**: A 14-hour total from 06:00 to 20:00.
2.  **AM Peak Volume**: The specific total for the 07:00-08:00 hour.
3.  **PM Peak Volume**: The specific total for the 17:00-18:00 hour.

A complete, hour-by-hour breakdown is not available. To create a 24-hour profile for our simulation models, we must fill these gaps using a principled estimation approach.

## 2. Generating the 24-Hour Hourly Distribution Profile

Our method creates a synthetic but realistic 24-hour traffic curve by recreating the bi-modal ("M" shaped) distribution characteristic of daily urban traffic. This approach is grounded in established traffic engineering patterns.

### The Process

1.  **Anchor to Peak Hours**: The process is anchored by the two most critical data points we possess: the AM and PM peak hour volumes. These are treated as known, ground-truth values.

2.  **Establish a Baseline**: A baseline "off-peak" hourly volume is calculated from the total 14-hour volume, after subtracting the two known peak hour volumes. This average represents traffic during the less busy parts of the day.

3.  **Interpolate Mid-day Lull**: For the hours between the AM and PM peaks (08:00 - 16:00), we use linear interpolation. This creates a smooth, realistic dip and recovery, modeling the natural decrease in traffic after the morning commute and the gradual build-up towards the evening rush.

4.  **Extrapolate Overnight Behavior**: Urban traffic does not cease overnight. We model this by:
    *   Gradually decreasing the traffic volume from the post-peak hours (18:00-20:00) down to a calculated minimum value around 03:00-04:00. This minimum is a small fraction of the daily average, representing essential overnight travel (e.g., logistics, essential workers).
    *   Ramping the volume back up from this minimum to meet the 06:00 baseline, modeling the start of the early morning commute.

5.  **Normalization**: The final 24-hour hourly volumes are normalized to percentages. The volume for each hour is divided by the total 24-hour volume, resulting in a profile where the sum of all 24 values is 1.0.

### Justification

This methodology is sound because it ensures the resulting profile is:
*   **Data-Driven**: It is directly anchored to the most significant real-world data points available (the peaks).
*   **Pattern-Realistic**: It programmatically reproduces the well-documented bi-modal daily traffic pattern, which is a fundamental concept in traffic analysis.
*   **Defensible**: It constitutes a form of reasoned estimation, a standard practice in data science and modeling when faced with incomplete datasets.

## 3. Generating the Standard Turning Profile

This process is more direct as the data for turning movements is fully available within the "TOTAL VOLUME" section of the CSV.

1.  **Data Parsing**: Each row's `LANE` description (e.g., "1 South_Westbound") is parsed to identify its origin approach (South) and its intended movement (a turn towards West).
2.  **Aggregation**: For each of the four main approaches (North, South, East, West), the total vehicle volumes for each type of movement (straight, left turn, right turn) are summed up.
3.  **Normalization**: The aggregated volumes for each approach are converted into percentages. For the "South" approach, the total "straight" traffic is divided by the total traffic originating from the South, and so on for "left" and "right".

This results in a profile that accurately reflects the turning movement distributions observed in the source data.
