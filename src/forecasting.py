
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""forecasting.py: The Prophet forecasting module.

This script takes a prepared time-series dataset (ds, y) and generates a 
minute-by-minute 24-hour forecast, saving it as a JSON demand curve.
"""

# TODO: tweak distribution. see the outputted demand curve to see imperfecitons 
# ex late night too heavy, early morning traffic ruhs hour is fine, pero di napapantayan ng 4 to 6/7pm rush hour, then weirdly goes up later into the night..

import pandas as pd
from prophet import Prophet
import json
import os
import argparse

def generate_forecast(input_path, output_path):
    """
    Fits a Prophet model to hourly data and generates a minute-by-minute forecast.

    Args:
        input_path (str): Path to the input CSV file. Must contain 'ds' and 'y' columns.
        output_path (str): Path to save the output JSON forecast file.
    """
    # 1. Load the data
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_path}")
        return

    if not all(col in df.columns for col in ['ds', 'y']):
        print("Error: Input CSV must contain 'ds' and 'y' columns.")
        return

    # 2. Initialize and fit the Prophet model
    # We enable daily seasonality as we are modeling a 24-hour cycle.
    # Weekly and yearly seasonality are disabled as they are not relevant.
    model = Prophet(daily_seasonality=True, weekly_seasonality=False, yearly_seasonality=False)
    model.fit(df)

    # 3. Create a future dataframe for the next 24 hours at 1-minute frequency
    future = model.make_future_dataframe(periods=24*60, freq='min')

    # 4. Generate the forecast
    forecast = model.predict(future)

    # Keep only the forecasted period (last 24 hours)
    forecast = forecast.tail(24*60)

    # 5. Process and save the output
    # We only need the timestamp (ds) and the forecasted value (yhat)
    output_data = forecast[['ds', 'yhat']]
    
    # Format the output to be a simple lookup table as discussed
    # 'time': 'HH:MM:SS', 'expected_demand': value
    output_data['time'] = output_data['ds'].dt.strftime('%H:%M:%S')
    output_data['expected_demand'] = output_data['yhat'].round(4)
    
    # Convert to the desired JSON structure
    result_json = output_data[['time', 'expected_demand']].to_dict(orient='records')

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(result_json, f, indent=4)
    
    print(f"Successfully generated forecast at {output_path}")


def main():
    """Main function to run the script from the command line."""
    parser = argparse.ArgumentParser(description="Generate a 24-hour forecast from hourly traffic data.")
    parser.add_argument("--input", required=True, help="Path to the input CSV file (must have 'ds' and 'y' columns).")
    parser.add_argument("--output", required=True, help="Path to save the output JSON forecast file.")
    
    args = parser.parse_args()
    
    generate_forecast(args.input, args.output)

if __name__ == '__main__':
    main()
