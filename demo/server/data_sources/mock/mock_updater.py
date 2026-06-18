import copy
import threading
import time
import random
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Callable


class MockDataUpdater:
    """Handles random value generation for mock data source to simulate real-time updates"""

    def __init__(self, data_source):
        self.data_source = data_source
        self.running = False
        self.thread = None
        self.update_callback = None

        # History accumulation: the live "head" record (index 0) is mutated every tick to
        # drive subscriptions, but to give clients a continuously-rolling history we also
        # freeze a snapshot of the head into the records array every `history_interval_s`
        # seconds, capping the buffer at `max_history_points` so memory stays bounded.
        self.history_interval_s = 30
        self.max_history_points = 480  # 30s * 480 ≈ 4 hours of rolling history
        self._last_snapshot: Dict[str, float] = {}  # elementId -> monotonic time of last snapshot

    def start(self, update_callback: Optional[Callable] = None):
        """Start the background thread that generates random updates"""
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
        """Main loop that generates random updates"""
        while self.running:
            # Get all instances with records (directly from data, not through get_all_instances which filters out records)
            instances = self.data_source.data["instances"]

            # Generate random updates for non-static instances
            for instance in instances:
                # Skip instances with "static" flag set to True
                if instance.get("static", False):
                    continue

                # Check if instance has a records array
                records_array = instance.get("records")
                if (
                    not records_array
                    or not isinstance(records_array, list)
                    or len(records_array) == 0
                ):
                    continue

                # Get the most recent record (first element in array)
                current_record = records_array[0]

                # Skip if record doesn't have the expected structure
                if not isinstance(current_record, dict) or "value" not in current_record:
                    continue

                # Make a copy to detect changes
                old_record = current_record.copy()

                # Randomize numeric values in the current record's value
                # Handle both primitive values and complex objects
                # (bool is excluded: it subclasses int, but randomizing would corrupt it to 0/1)
                if isinstance(current_record["value"], (int, float)) and not isinstance(current_record["value"], bool):
                    # For primitive numeric values, randomize directly
                    v = current_record["value"]
                    variation = v * 0.1
                    new_val = v + random.uniform(-variation, variation)
                    current_record["value"] = int(new_val) if isinstance(v, int) else new_val
                elif isinstance(current_record["value"], (dict, list)):
                    # For complex objects, randomize recursively
                    self.randomize_numeric_values(current_record["value"])

                # Update timestamp at record level
                current_record["timestamp"] = datetime.now(timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )

                # Also update timestamp inside value if it exists (check for both "Timestamp" and "timestamp")
                if isinstance(current_record["value"], dict):
                    if "Timestamp" in current_record["value"]:
                        current_record["value"]["Timestamp"] = current_record["timestamp"]
                    elif "timestamp" in current_record["value"]:
                        current_record["value"]["timestamp"] = current_record["timestamp"]

                # If callback is provided, notify about the update
                if self.update_callback and old_record != current_record:
                    self.update_callback(instance, current_record)

                # Periodically freeze the current head into history so clients get a
                # continuously-rolling trend (not just one moving point). We insert a
                # copy at index 0: the copy becomes the new live head that future ticks
                # mutate, while the prior head (now at index 1) is preserved as a sample.
                element_id = instance.get("elementId")
                last = self._last_snapshot.get(element_id, 0.0)
                if time.monotonic() - last >= self.history_interval_s:
                    records_array.insert(0, copy.deepcopy(current_record))
                    # Cap the buffer so a long-running server doesn't grow unbounded
                    if len(records_array) > self.max_history_points:
                        del records_array[self.max_history_points:]
                    self._last_snapshot[element_id] = time.monotonic()

            time.sleep(1)  # Update every second

    def randomize_numeric_values(self, obj):
        """Simulate data changes by changing numeric values in the data"""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, bool):
                    # bool subclasses int — leave booleans alone or they degrade to 0/1
                    continue
                elif isinstance(v, (int, float)):
                    # Change numeric value randomly +/- up to 10%
                    variation = v * 0.1
                    new_val = v + random.uniform(-variation, variation)
                    # If original was int, convert back to int
                    obj[k] = int(new_val) if isinstance(v, int) else new_val
                elif isinstance(v, dict) or isinstance(v, list):
                    self.randomize_numeric_values(v)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, bool):
                    continue
                elif isinstance(item, (int, float)):
                    variation = item * 0.1
                    new_val = item + random.uniform(-variation, variation)
                    obj[i] = int(new_val) if isinstance(item, int) else new_val
                elif isinstance(item, dict) or isinstance(item, list):
                    self.randomize_numeric_values(item)
