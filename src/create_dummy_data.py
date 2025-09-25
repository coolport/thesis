import json
import pandas as pd
import os

# Define file paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE_PATH = os.path.join(PROJECT_ROOT, 'data', 'profiles', 'standard_24h_profile.json')
OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'data', 'dummy_hourly_data.csv')

def create_dummy_data():
    """Uses the 24h profile to generate a realistic hourly traffic CSV."""
    # Load the profile
    try:
        with open(PROFILE_PATH, 'r') as f:
            profile = json.load(f)
    except FileNotFoundError:
        print(f"Error: Profile not found at {PROFILE_PATH}")
        return

    # Create dummy data based on a fictional total daily volume
    FICTIONAL_TOTAL_DAILY_VOLUME = 50000
    hourly_volumes = [p * FICTIONAL_TOTAL_DAILY_VOLUME for p in profile]

    # Create a pandas DataFrame with 'ds' and 'y' columns
    dates = pd.to_datetime(pd.date_range(start='2025-01-01', periods=24, freq='h'))
    dummy_df = pd.DataFrame({
        'ds': dates,
        'y': hourly_volumes
    })

    # Save to CSV
    dummy_df.to_csv(OUTPUT_PATH, index=False)
    print(f'Successfully created dummy data at {OUTPUT_PATH}')

if __name__ == '__main__':
    create_dummy_data()