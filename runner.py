import traci
import subprocess
import sys

# Path to the SUMO executable
sumo_binary = "sumo-gui"  # or "sumo" for command-line

# Command to run SUMO
sumo_cmd = [
    sumo_binary,
    "-c",
    "/home/aidan/thesis/edsa_east.sumocfg",
    "--tripinfo-output",
    "tripinfo.xml",
]

try:
    # Start SUMO as a subprocess
    traci.start(sumo_cmd)

    step = 0
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        # Your simulation logic here
        # e.g., print the number of vehicles
        if step % 100 == 0:
            print(f"Step: {step}, Vehicles: {traci.vehicle.getIDCount()}")
        step += 1

except traci.exceptions.TraCIException as e:
    print(f"Error starting SUMO: {e}")
    sys.exit(1)
finally:
    traci.close()
    print("Simulation finished.")
