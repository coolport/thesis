
import pandas as pd
import json
import os

def create_real_data():
    """
    Uses the clean, separated total volume CSV and the verifiable 
    standard_24h_profile.json to generate four unique, realistic,
    per-direction input files for the Prophet forecaster.
    """
    print("--- Creating final realistic data using standard profile and clean CSVs ---")
    
    try:
        # 1. Load the clean total volume data
        df_total = pd.read_csv('data/volume_total.csv')

        # 2. Load the verifiable 24-hour distribution profile
        profile_path = 'data/profiles/standard_24h_profile.json'
        with open(profile_path, 'r') as f:
            profile_data = json.load(f)
        # Convert list of dicts to a simple mapping of hour -> percentage
        distribution = {item['hour']: item['percentage'] for item in profile_data}

    except FileNotFoundError as e:
        print(f"Error: A required file was not found. {e}")
        return

    # 3. Calculate the total 14-hour surface-level volume for each approach
    # Filter out underpass traffic, but keep U-turns as requested.
    df_surface = df_total[~df_total['LANE'].str.contains('_Underpass', na=False)].copy()

    approach_totals = {}
    directions = ['North', 'South', 'East', 'West']
    for direction in directions:
        total_volume = df_surface[df_surface['LANE'].str.contains(direction, na=False)]['TOTAL'].sum()
        approach_totals[direction[0]] = total_volume

    # 4. Estimate 24h traffic and generate per-direction hourly data files
    # The transcript data is for 14 hours (6am-8pm). We use our profile to find the
    # percentage of traffic that occurs in this window to create an expansion factor.
    dist_14h = sum(distribution.get(h, 0) for h in range(6, 20))
    if dist_14h == 0:
        print("Error: Could not calculate 14-hour distribution from profile.")
        return

    for direction_initial, total_14h_volume in approach_totals.items():
        # Estimate the total 24h volume for this direction
        estimated_24h_volume = total_14h_volume / dist_14h

        # Apply the 24h distribution to the direction-specific estimated 24h volume
        hourly_data = []
        for hour in range(24):
            timestamp = f"2025-01-01 {hour:02d}:00:00"
            traffic_value = estimated_24h_volume * distribution.get(hour, 0)
            hourly_data.append({'ds': timestamp, 'y': traffic_value})
        
        df_new = pd.DataFrame(hourly_data)

        # Save the new file
        output_path = os.path.join('data', f'prophet_input_{direction_initial}.csv')
        df_new.to_csv(output_path, index=False)
        print(f"Successfully created {output_path}")

if __name__ == '__main__':
    create_real_data()
