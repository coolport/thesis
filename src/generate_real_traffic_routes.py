
import pandas as pd
import json
import os
import random
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

def generate_real_traffic_routes():
    """
    Generates a high-fidelity SUMO route file (.rou.xml) based on the real
    traffic data, the 24-hour profile, and the turning profile.

    This replaces the simple, predictable <flow>-based traffic with thousands
    of unique <vehicle> entries with randomized departure times, creating a 
    much more realistic simulation environment.
    """
    print("--- Generating high-fidelity SUMO route file ---")

    try:
        # 1. Load all necessary data and profiles
        df_total = pd.read_csv('data/volume_total.csv')
        with open('data/profiles/standard_24h_profile.json', 'r') as f:
            dist_profile = {item['hour']: item['percentage'] for item in json.load(f)}
        with open('data/profiles/standard_turning_profile.json', 'r') as f:
            turn_profile = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: A required data or profile file was not found. {e}")
        return

    # --- 2. Calculate Total and Per-Direction 24h Volumes ---
    df_surface = df_total[~df_total['LANE'].str.contains('_Underpass', na=False)].copy()
    total_14h_surface_volume = df_surface['TOTAL'].sum()
    
    dist_14h = sum(dist_profile.get(h, 0) for h in range(6, 20))
    if dist_14h == 0: return

    total_24h_volume = total_14h_surface_volume / dist_14h

    approach_totals = {}
    for direction in ['North', 'South', 'East', 'West']:
        approach_totals[direction[0]] = df_surface[df_surface['LANE'].str.contains(direction, na=False)]['TOTAL'].sum()
    
    total_approach_proportions = {k: v / sum(approach_totals.values()) for k, v in approach_totals.items()}

    # --- 3. Generate Vehicle Definitions for the XML file ---
    vehicle_id = 0
    vehicles = []

    for hour in range(24):
        # Total vehicles to generate in this hour
        total_hourly_vehicles = int(total_24h_volume * dist_profile.get(hour, 0))

        for approach, approach_prop in total_approach_proportions.items():
            # Vehicles for this approach in this hour
            num_vehicles_approach = int(total_hourly_vehicles * approach_prop)

            # Distribute vehicles into straight, left, right based on turning profile
            tp = turn_profile.get(approach, {})
            num_straight = int(num_vehicles_approach * tp.get('straight', 0))
            num_left = int(num_vehicles_approach * tp.get('left', 0))
            num_right = int(num_vehicles_approach * tp.get('right', 0))

            # Generate vehicles for each turn type
            for i in range(num_straight):
                depart_time = hour * 3600 + random.uniform(0, 3599)
                vehicles.append(("veh_{}".format(vehicle_id), round(depart_time, 2), f"route_{approach}_S")) # Assuming S is straight
                vehicle_id += 1
            for i in range(num_left):
                depart_time = hour * 3600 + random.uniform(0, 3599)
                vehicles.append(("veh_{}".format(vehicle_id), round(depart_time, 2), f"route_{approach}_L")) # Assuming L is left
                vehicle_id += 1
            for i in range(num_right):
                depart_time = hour * 3600 + random.uniform(0, 3599)
                vehicles.append(("veh_{}".format(vehicle_id), round(depart_time, 2), f"route_{approach}_R")) # Assuming R is right
                vehicle_id += 1

    # --- 4. Create the XML structure ---
    # Sort vehicles by departure time to prevent SUMO warnings
    vehicles.sort(key=lambda x: x[1])

    routes_root = Element('routes')
    SubElement(routes_root, 'vType', id="car", accel="2.6", decel="4.5", sigma="0.5", length="5", maxSpeed="70")

    # Define the routes based on a corrected mapping
    route_definitions = {
        "route_N_S": "N_to_center center_to_S", "route_N_L": "N_to_center center_to_E", "route_N_R": "N_to_center center_to_W",
        "route_S_S": "S_to_center center_to_N", "route_S_L": "S_to_center center_to_W", "route_S_R": "S_to_center center_to_E",
        "route_E_S": "E_to_center center_to_W", "route_E_L": "E_to_center center_to_N", "route_E_R": "E_to_center center_to_S",
        "route_W_S": "W_to_center center_to_E", "route_W_L": "W_to_center center_to_S", "route_W_R": "W_to_center center_to_N",
    }
    for route_id, edges in route_definitions.items():
        SubElement(routes_root, 'route', id=route_id, edges=edges)

    for id, depart, route in vehicles:
        SubElement(routes_root, 'vehicle', id=id, type="car", route=route, depart=str(depart))

    # --- 5. Write the pretty-printed XML file ---
    xml_str = minidom.parseString(tostring(routes_root)).toprettyxml(indent="   ")
    output_path = 'sumo/real_traffic.rou.xml'
    with open(output_path, 'w') as f:
        f.write(xml_str)
    
    print(f"Successfully generated high-fidelity route file with {len(vehicles)} vehicles to {output_path}")

if __name__ == '__main__':
    generate_real_traffic_routes()
