
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""data_processing.py: Contains scripts for Phase 0 of the pipeline.

This script will:
- Read the raw MMDA traffic data CSV.
- Generate the standard_24h_profile.json representing hourly traffic distribution.
- Generate the standard_turning_profile.json representing turning movement ratios.
"""

import csv
import json
import numpy as np
import os

# Define file paths
# Correctly resolve the absolute path for the project root
# Assuming this script is in /home/aidan/thesis/src
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_CSV = os.path.join(PROJECT_ROOT, 'foi_transcript.csv')
OUTPUT_TURNING_PROFILE = os.path.join(PROJECT_ROOT, 'data', 'profiles', 'standard_turning_profile.json')
OUTPUT_HOURLY_PROFILE = os.path.join(PROJECT_ROOT, 'data', 'profiles', 'standard_24h_profile.json')

def parse_traffic_data(file_path):
    """
    Parses the specially formatted traffic data CSV.
    
    Args:
        file_path (str): The absolute path to the foi_transcript.csv file.

    Returns:
        dict: A dictionary containing the data for 'total', 'am_peak', and 'pm_peak'.
    """
    data = {'total': [], 'am_peak': [], 'pm_peak': []}
    current_section = None

    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or not row[0]:
                continue
            
            header = row[0].lower()
            if 'total volume' in header:
                current_section = 'total'
                next(reader)  # Skip header line
                continue
            elif 'peak am' in header:
                current_section = 'am_peak'
                next(reader)  # Skip header line
                continue
            elif 'peak pm' in header:
                current_section = 'pm_peak'
                next(reader)  # Skip header line
                continue

            if current_section and 'total' not in row[0].lower():
                try:
                    data[current_section].append({
                        'lane': row[0],
                        'total': int(row[11])
                    })
                except (ValueError, IndexError):
                    # Ignore rows that don't have a valid total in the 12th column
                    continue
    return data

def generate_turning_profile(total_data):
    """
    Generates the standard turning profile from the total traffic data.
    
    Args:
        total_data (list): A list of dictionaries with 'lane' and 'total' keys.
    """
    # N, S, E, W approaches and their movements
    movements = {
        'S': {'straight': 0, 'left': 0, 'right': 0}, # N, W, E
        'N': {'straight': 0, 'left': 0, 'right': 0}, # S, E, W
        'E': {'straight': 0, 'left': 0, 'right': 0}, # W, N, S
        'W': {'straight': 0, 'left': 0, 'right': 0}  # E, S, N
    }

    for item in total_data:
        lane_name = item['lane'].lower()
        volume = item['total']
        
        if 'south' in lane_name and 'north' in lane_name:
            movements['S']['straight'] += volume
        elif 'south' in lane_name and 'west' in lane_name:
            movements['S']['left'] += volume
        elif 'south' in lane_name and 'east' in lane_name:
            movements['S']['right'] += volume
        
        elif 'north' in lane_name and 'south' in lane_name:
            movements['N']['straight'] += volume
        elif 'north' in lane_name and 'east' in lane_name:
            movements['N']['left'] += volume
        elif 'north' in lane_name and 'west' in lane_name:
            movements['N']['right'] += volume

        elif 'east' in lane_name and 'west' in lane_name:
            movements['E']['straight'] += volume
        elif 'east' in lane_name and 'north' in lane_name:
            movements['E']['right'] += volume # Note: East to North is a right turn
        # No East to South in data, so it remains 0

        elif 'west' in lane_name and 'east' in lane_name:
            movements['W']['straight'] += volume
        elif 'west' in lane_name and 'south' in lane_name:
            movements['W']['left'] += volume
        # No West to North in data, so it remains 0

    # Normalize to percentages
    profile = {}
    for origin, turns in movements.items():
        total_origin_vol = sum(turns.values())
        profile[origin] = {
            turn: round(vol / total_origin_vol, 4) if total_origin_vol > 0 else 0
            for turn, vol in turns.items()
        }

    with open(OUTPUT_TURNING_PROFILE, 'w') as f:
        json.dump(profile, f, indent=4)
    print(f"Successfully generated {OUTPUT_TURNING_PROFILE}")

def generate_hourly_profile(parsed_data):
    """
    Generates a 24-hour traffic distribution profile using interpolation and extrapolation.
    
    Args:
        parsed_data (dict): The full parsed data from the CSV.
    """
    am_peak_vol = sum(item['total'] for item in parsed_data['am_peak'])
    pm_peak_vol = sum(item['total'] for item in parsed_data['pm_peak'])
    
    # Create a 24-hour array to hold volumes
    hourly_vols = np.zeros(24)
    
    # 1. Anchor to peak hours
    hourly_vols[7] = am_peak_vol  # 07:00-08:00
    hourly_vols[17] = pm_peak_vol # 17:00-18:00

    # 2. Interpolate mid-day lull (8:00 to 16:00)
    # We use the known start (AM peak) and end (PM peak) points
    xp = [7, 17]
    fp = [am_peak_vol, pm_peak_vol]
    x_interp = list(range(8, 17))
    hourly_vols[8:17] = np.interp(x_interp, xp, fp)

    # 3. Set baselines for morning and evening from data
    # A simple baseline can be the average of the two peaks
    avg_peak = (am_peak_vol + pm_peak_vol) / 2
    hourly_vols[6] = avg_peak * 0.8  # 6am, ramp up
    hourly_vols[18] = pm_peak_vol * 0.9 # 6pm, start of ramp down
    hourly_vols[19] = pm_peak_vol * 0.7 # 7pm, continue ramp down

    # 4. Extrapolate overnight behavior (20:00 to 05:00)
    overnight_min_vol = avg_peak * 0.1 # Assume 10% of avg peak traffic at night
    # Interpolate from 19:00 down to 03:00
    xp_night1 = [19, 24+3] # 27 is 3am
    fp_night1 = [hourly_vols[19], overnight_min_vol]
    x_night1 = list(range(20, 24+3))
    interp_vals1 = np.interp(x_night1, xp_night1, fp_night1)
    hourly_vols[20:24] = interp_vals1[0:4]
    hourly_vols[0:3] = interp_vals1[4:7]
    
    # Interpolate from 03:00 up to 06:00
    xp_night2 = [3, 6]
    fp_night2 = [overnight_min_vol, hourly_vols[6]]
    x_night2 = [4, 5]
    hourly_vols[3:6] = np.interp(list(range(3,6)), xp_night2, fp_night2)


    # 5. Normalize to get percentages
    total_24h_vol = sum(hourly_vols)
    hourly_profile = [round(v / total_24h_vol, 6) for v in hourly_vols]

    with open(OUTPUT_HOURLY_PROFILE, 'w') as f:
        json.dump(hourly_profile, f, indent=4)
    print(f"Successfully generated {OUTPUT_HOURLY_PROFILE}")


def main():
    """Main function to run the data processing."""
    print("Starting Phase 0: Data Processing and Calibration...")
    if not os.path.exists(INPUT_CSV):
        print(f"ERROR: Input file not found at {INPUT_CSV}")
        return

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(OUTPUT_TURNING_PROFILE), exist_ok=True)

    parsed_data = parse_traffic_data(INPUT_CSV)
    
    if not parsed_data['total']:
        print("ERROR: Could not parse total volume data from CSV. Check file format.")
        return

    generate_turning_profile(parsed_data['total'])
    
    if not parsed_data['am_peak'] or not parsed_data['pm_peak']:
        print("ERROR: Could not parse AM or PM peak data. Cannot generate hourly profile.")
        return
        
    generate_hourly_profile(parsed_data)
    print("Phase 0 completed successfully.")


if __name__ == '__main__':
    main()
