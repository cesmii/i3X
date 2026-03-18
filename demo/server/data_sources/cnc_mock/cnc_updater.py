"""
CNC Data Updater - Generates realistic value updates for CNC machine simulation.

This module handles background value generation to simulate real-time CNC machine data.
"""
import threading
import time
import random
from datetime import datetime, timezone
from typing import Optional, Callable


class CNCDataUpdater:
    """Handles value generation for CNC data source to simulate real-time updates"""

    def __init__(self, data_source):
        self.data_source = data_source
        self.running = False
        self.thread = None
        self.update_callback = None

    def start(self, update_callback: Optional[Callable] = None):
        """Start the background thread that generates updates"""
        if self.running:
            return

        self.update_callback = update_callback
        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the background update thread"""
        self.running = False
        if self.thread:
            self.thread.join()

    def _update_loop(self):
        """Main loop that generates CNC-specific updates"""
        while self.running:
            # Access raw data directly (not through get_all_instances which filters records)
            instances = self.data_source.data["instances"]

            for instance in instances:
                # Skip instances without records
                records_array = instance.get("records")
                if not records_array or not isinstance(records_array, list) or len(records_array) == 0:
                    continue

                current_record = records_array[0]
                if not isinstance(current_record, dict) or "value" not in current_record:
                    continue

                # Make a copy to detect changes
                old_record = current_record.copy()

                # Apply CNC-specific value updates based on instance type
                type_id = instance.get("typeElementId", "")
                value = current_record["value"]

                if isinstance(value, dict):
                    self._update_cnc_values(value, type_id, instance.get("elementId", ""))

                # Update timestamp
                current_record["timestamp"] = datetime.now(timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )

                # Notify callback if value changed
                if self.update_callback and old_record != current_record:
                    self.update_callback(instance, current_record)

            time.sleep(1)  # Update every second

    def _update_cnc_values(self, value: dict, type_id: str, element_id: str):
        """Apply CNC-specific value updates based on type"""

        if type_id == "motor-type":
            # Motor values - simulate spindle motor behavior
            if "RPM" in value and value["RPM"] > 0:
                # Running motor - vary RPM slightly
                value["RPM"] = max(0, value["RPM"] + random.uniform(-50, 50))
                value["Current"] = max(0.5, value["Current"] + random.uniform(-0.5, 0.5))
                value["Vibration"] = max(0.01, value["Vibration"] + random.uniform(-0.02, 0.02))
                value["LoadRate"] = max(0, min(100, value["LoadRate"] + random.uniform(-2, 2)))
                value["Efficiency"] = max(80, min(98, value["Efficiency"] + random.uniform(-0.5, 0.5)))
            # Idle motor stays relatively stable

        elif type_id == "position-type":
            # Position values - simulate axis movement
            if "ActualPosition" in value:
                actual = value["ActualPosition"]
                commanded = value.get("CommandedPosition", actual)

                # Move actual toward commanded
                diff = commanded - actual
                if abs(diff) > 0.001:
                    # Move partway toward commanded position
                    step = diff * random.uniform(0.3, 0.7)
                    value["ActualPosition"] = actual + step
                    value["RemainingDistance"] = abs(commanded - value["ActualPosition"])
                else:
                    # At commanded position - maybe get new command
                    if random.random() < 0.1:  # 10% chance of new command
                        value["CommandedPosition"] = commanded + random.uniform(-50, 50)
                        value["RemainingDistance"] = abs(value["CommandedPosition"] - actual)

        elif type_id == "machine-status-type":
            # Machine status - simulate power consumption based on state
            state = value.get("MachineState", "Idle")
            if state == "Running":
                value["PowerConsumption"] = max(5, value.get("PowerConsumption", 10) + random.uniform(-0.5, 0.5))
                value["EnergyIntensity"] = max(0.1, value.get("EnergyIntensity", 0.4) + random.uniform(-0.02, 0.02))
            else:
                # Idle state - low power
                value["PowerConsumption"] = max(1, value.get("PowerConsumption", 3) + random.uniform(-0.1, 0.1))
                value["EnergyIntensity"] = 0.0

        elif type_id == "coolant-tank-type":
            # Coolant tank - simulate gradual level decrease and temperature variation
            if "Level" in value:
                value["Level"] = max(10, min(100, value["Level"] + random.uniform(-0.2, 0.1)))
            if "Temperature" in value:
                value["Temperature"] = max(18, min(35, value["Temperature"] + random.uniform(-0.3, 0.3)))

        elif type_id == "coolant-pump-type":
            # Coolant pump - flow/pressure based on parent machine state
            # Check if parent CNC is running (simplified - just vary values)
            if "cnc-001" in element_id:
                # CNC-001 is running
                value["Flow"] = max(8, min(18, value.get("Flow", 12) + random.uniform(-0.5, 0.5)))
                value["Pressure"] = max(3, min(6, value.get("Pressure", 4) + random.uniform(-0.1, 0.1)))
                value["Power"] = max(0.5, min(1.5, value.get("Power", 0.75) + random.uniform(-0.05, 0.05)))
            # CNC-002 pump stays at 0 (idle)
