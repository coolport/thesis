import pandas as pd
import numpy as np
import json
import os

def build_traffic_profile():
    """
    Generates a realistic, verifiable 24-hour traffic profile by reading the
    clean, separated peak volume CSVs.

    Methodology:
    1.  Reads the peak AM (7-8 AM) and peak PM (5-6 PM) traffic volumes from the 
        clean CSVs, excluding underpass traffic as per the project scope.
    2.  These two real-world hourly totals are used as anchor points.
    3.  A standard bimodal (two-peak) distribution is generated as a template for a typical
        urban traffic rhythm.
    4.  This template is scaled and adjusted to precisely match the two real-world anchor points.
    5.  The final output is a JSON file containing the percentage of total daily traffic 
        that occurs in each of the 24 hours.
    """
    print("--- Building verifiable 24-hour traffic profile from clean CSVs ---")

    try:
        df_am = pd.read_csv('data/volume_am.csv')
        df_pm = pd.read_csv('data/volume_pm.csv')
    except FileNotFoundError as e:
        print(f"Error: A required volume file was not found. {e}")
        return

    # --- 1. Calculate Real Hourly Totals from Peak Data ---
    # Filter out underpass traffic, but keep U-turns as requested.
    am_surface_traffic = df_am[~df_am['LANE'].str.contains('_Underpass', na=False)]
    pm_surface_traffic = df_pm[~df_pm['LANE'].str.contains('_Underpass', na=False)]

    # Sum the TOTAL column to get the true hourly volume for the peak hours
    total_am_peak_volume = am_surface_traffic['TOTAL'].sum()
    total_pm_peak_volume = pm_surface_traffic['TOTAL'].sum()

    print(f"Real Surface-Level Volume (7-8 AM): {total_am_peak_volume}")
    print(f"Real Surface-Level Volume (5-6 PM): {total_pm_peak_volume}")

    # --- 2. Engineer the 24-Hour Curve ---
    hours = np.arange(24)
    # Bimodal distribution parameters (mean, std_dev, amplitude)
    am_peak_hour, am_std_dev, am_amplitude = 8, 2.5, 1.0
    pm_peak_hour, pm_std_dev, pm_amplitude = 17.5, 3.0, 0.9
    base_load = 0.1 # Represents low-level overnight traffic

    am_curve = am_amplitude * np.exp(-((hours - am_peak_hour) ** 2) / (2 * am_std_dev ** 2))
    pm_curve = pm_amplitude * np.exp(-((hours - pm_peak_hour) ** 2) / (2 * pm_std_dev ** 2))
    template_profile = am_curve + pm_curve + base_load

    # --- 3. Scale the Template to Match Real Anchor Points ---
    template_am_val = template_profile[7] # 7 AM
    template_pm_val = template_profile[17] # 5 PM

    am_scale_factor = total_am_peak_volume / template_am_val
    pm_scale_factor = total_pm_peak_volume / template_pm_val

    scaling_factors = np.interp(hours, [7, 17], [am_scale_factor, pm_scale_factor])
    scaled_profile = template_profile * scaling_factors

    # --- 4. Final Normalization and Output ---
    total_scaled_volume = scaled_profile.sum()
    if total_scaled_volume == 0:
        print("Error: Total scaled volume is zero, cannot create distribution.")
        return
        
    final_distribution = scaled_profile / total_scaled_volume

    output_data = []
    for hour, percentage in enumerate(final_distribution):
        output_data.append({"hour": hour, "percentage": round(percentage, 6)})

    output_dir = 'data/profiles'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'standard_24h_profile.json')

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=4)

    print(f"Successfully built and saved verifiable profile to {output_path}")

if __name__ == '__main__':
    build_traffic_profile()