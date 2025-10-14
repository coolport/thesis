import pandas as pd
import json
import os

def build_turning_profile():
    """
    Parses the clean, separated total volume CSV to calculate the true turning
    ratios for each approach, creating a verifiable standard_turning_profile.json.

    Methodology:
    1.  Reads the clean data from `data/volume_total.csv`.
    2.  Filters out underpass traffic to focus on surface-level movements.
    3.  For each lane description, it programmatically extracts the 'origin' and 'destination'.
    4.  For each cardinal direction (North, South, East, West), it calculates the
        total volume originating from that approach.
    5.  It then calculates the volume for each turning movement (straight, left, right)
        originating from that approach by checking the extracted destination.
    6.  The percentages for each turn are calculated and saved to a JSON file.
    """
    print("--- Building verifiable standard turning profile ---")

    try:
        df = pd.read_csv('data/volume_total.csv')
    except FileNotFoundError:
        print("Error: `data/volume_total.csv` not found. Please ensure it has been created.")
        return

    # --- 1. Filter out underpass traffic ---
    df_surface = df[~df['LANE'].str.contains('_Underpass', na=False)].copy()

    # --- 2. Engineer Origin/Destination columns for robust parsing ---
    def get_origin(lane_str):
        # e.g., "1 South_Westbound" -> "South"
        parts = lane_str.split()
        if len(parts) > 1:
            return parts[1].split('_')[0]
        return None

    def get_destination(lane_str):
        # e.g., "1 South_Westbound" -> "Westbound"
        parts = lane_str.split('_')
        if len(parts) > 1:
            # Handles cases like "South_Southbound_Uturn" -> "Southbound"
            return parts[1]
        return None

    df_surface['origin'] = df_surface['LANE'].apply(get_origin)
    df_surface['destination'] = df_surface['LANE'].apply(get_destination)

    # --- 3. Define movements and calculate ratios ---
    # Maps cardinal directions to turn types based on intersection layout.
    movements = {
        'N': {'origin_str': 'North', 'straight': 'Southbound', 'left': 'Eastbound', 'right': 'Westbound'},
        'S': {'origin_str': 'South', 'straight': 'Northbound', 'left': 'Westbound', 'right': 'Eastbound'},
        'E': {'origin_str': 'East', 'straight': 'Westbound', 'left': 'Northbound', 'right': 'Southbound'},
        'W': {'origin_str': 'West', 'straight': 'Eastbound', 'left': 'Southbound', 'right': 'Northbound'}
    }

    turning_profile = {}

    for approach, turns in movements.items():
        origin_str = turns['origin_str']
        
        # Get all traffic originating from this approach using the new 'origin' column
        df_approach = df_surface[df_surface['origin'] == origin_str]
        total_approach_volume = df_approach['TOTAL'].sum()

        if total_approach_volume == 0:
            turning_profile[approach] = {"straight": 0.0, "left": 0.0, "right": 0.0}
            continue

        # Calculate volume for each turn type using the new 'destination' column
        vol_straight = df_approach[df_approach['destination'] == turns['straight']]['TOTAL'].sum()
        vol_left = df_approach[df_approach['destination'] == turns['left']]['TOTAL'].sum()
        vol_right = df_approach[df_approach['destination'] == turns['right']]['TOTAL'].sum()

        # Calculate percentages
        pct_straight = vol_straight / total_approach_volume
        pct_left = vol_left / total_approach_volume
        pct_right = vol_right / total_approach_volume
        
        turning_profile[approach] = {
            "straight": round(pct_straight, 4),
            "left": round(pct_left, 4),
            "right": round(pct_right, 4)
        }

    # --- 4. Save the final JSON file ---
    output_dir = 'data/profiles'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'standard_turning_profile.json')

    with open(output_path, 'w') as f:
        json.dump(turning_profile, f, indent=4)

    print(f"Successfully built and saved turning profile to {output_path}")
    print(json.dumps(turning_profile, indent=4))

if __name__ == '__main__':
    build_turning_profile()