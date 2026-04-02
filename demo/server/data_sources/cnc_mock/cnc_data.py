"""
CNC Mock Data - Based on OPC UA NodeSet2 information model from cesmii.net.profiles.cnc.nodeset2.xml

This module defines mock data for two CNC machines grouped in a work-center,
using the CESMII CNC profile types.
"""
from datetime import datetime, timezone

# Generate current timestamp
def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

CNC_NAMESPACE = "http://cesmii.net/profiles/CNC"
I3X_NAMESPACE = "https://cesmii.org/i3x"
ISA95_NAMESPACE = "https://isa.org/isa95"

CNC_DATA = {
    "namespaces": [
        {"uri": I3X_NAMESPACE, "displayName": "I3X"},
        {"uri": ISA95_NAMESPACE, "displayName": "ISA95"},
        {"uri": CNC_NAMESPACE, "displayName": "CESMII CNC Profile"},
    ],
    "objectTypes": [
        # ISA-95 Work Center type for organizing CNC machines
        {
            "elementId": "work-center-type",
            "displayName": "WorkCenterType",
            "namespaceUri": ISA95_NAMESPACE,
            "sourceTypeId": "WorkCenterType",
            "schema": {
                "type": "object",
                "description": "A work center that organizes manufacturing equipment"
            }
        },
        # CNC Base Type - main CNC machine type
        {
            "elementId": "cnc-base-type",
            "displayName": "CNCBaseType",
            "namespaceUri": CNC_NAMESPACE,
            "sourceTypeId": "CNCBaseType",
            "schema": {
                "type": "object",
                "description": "Base CNC type that aggregates key components of a CNC Machine"
            }
        },
        # Machine Status Type
        {
            "elementId": "machine-status-type",
            "displayName": "MachineStatusType",
            "namespaceUri": CNC_NAMESPACE,
            "sourceTypeId": "MachineStatusType",
            "schema": {
                "type": "object",
                "properties": {
                    "MachineState": {"type": "string"},
                    "PowerConsumption": {"type": "number", "description": "kWh"},
                    "EnergyIntensity": {"type": "number", "description": "kWh/part"}
                }
            }
        },
        # Spindle Type
        {
            "elementId": "spindle-type",
            "displayName": "SpindleType",
            "namespaceUri": CNC_NAMESPACE,
            "sourceTypeId": "SpindleType",
            "schema": {
                "type": "object",
                "description": "CNC Spindle with motor and operational attributes"
            }
        },
        # Motor Type
        {
            "elementId": "motor-type",
            "displayName": "MotorType",
            "namespaceUri": CNC_NAMESPACE,
            "sourceTypeId": "MotorType",
            "schema": {
                "type": "object",
                "properties": {
                    "RPM": {"type": "number"},
                    "Current": {"type": "number"},
                    "Voltage": {"type": "number"},
                    "Vibration": {"type": "number"},
                    "Efficiency": {"type": "number"},
                    "LoadRate": {"type": "number"}
                }
            }
        },
        # Axis Type
        {
            "elementId": "axis-type",
            "displayName": "AxisType",
            "namespaceUri": CNC_NAMESPACE,
            "sourceTypeId": "AxisType",
            "schema": {
                "type": "object",
                "description": "CNC Axis with position and motor attributes"
            }
        },
        # Position Type
        {
            "elementId": "position-type",
            "displayName": "PositionType",
            "namespaceUri": CNC_NAMESPACE,
            "sourceTypeId": "PositionType",
            "schema": {
                "type": "object",
                "properties": {
                    "ActualPosition": {"type": "number"},
                    "CommandedPosition": {"type": "number"},
                    "RemainingDistance": {"type": "number"}
                }
            }
        },
        # Coolant System Type
        {
            "elementId": "coolant-system-type",
            "displayName": "CoolantSystemType",
            "namespaceUri": CNC_NAMESPACE,
            "sourceTypeId": "CoolantSystemType",
            "schema": {
                "type": "object",
                "description": "CNC Coolant System with tank, pump, and filter"
            }
        },
        # Coolant Tank Type
        {
            "elementId": "coolant-tank-type",
            "displayName": "CoolantTankType",
            "namespaceUri": CNC_NAMESPACE,
            "sourceTypeId": "CoolantTankType",
            "schema": {
                "type": "object",
                "properties": {
                    "Level": {"type": "number"},
                    "Temperature": {"type": "number"},
                    "Capacity": {"type": "number"}
                }
            }
        },
        # Coolant Pump Type
        {
            "elementId": "coolant-pump-type",
            "displayName": "CoolantPumpType",
            "namespaceUri": CNC_NAMESPACE,
            "sourceTypeId": "CoolantPumpType",
            "schema": {
                "type": "object",
                "properties": {
                    "Flow": {"type": "number"},
                    "Pressure": {"type": "number"},
                    "Power": {"type": "number"}
                }
            }
        },
    ],
    "instances": [
        # Work Center - organizational container for both CNC machines
        {
            "elementId": "cnc-work-center",
            "displayName": "CNC Work Center",
            "namespaceUri": ISA95_NAMESPACE,
            "typeElementId": "work-center-type",
            "parentId": None,
            "isComposition": False,
            "relationships": {
                "HasChildren": ["cnc-001", "cnc-002"]
            },
            "location": "Building A, Floor 2",
            "operationStartDate": "2020-03-15"
        },

        # ==================== CNC-001 ====================
        {
            "elementId": "cnc-001",
            "displayName": "CNC Machine 001",
            "typeElementId": "cnc-base-type",
            "parentId": "cnc-work-center",
            "isComposition": True,
            "relationships": {
                "HasParent": "cnc-work-center",
                "HasComponent": [
                    "cnc-001-status",
                    "cnc-001-spindle",
                    "cnc-001-axis-x",
                    "cnc-001-axis-y",
                    "cnc-001-axis-z",
                    "cnc-001-coolant"
                ]
            },
            "manufacturer": "FANUC",
            "model": "Robodrill D21MiB5",
            "serialNumber": "CNC-2020-001"
        },
        # CNC-001 Status
        {
            "elementId": "cnc-001-status",
            "displayName": "CNC-001 Status",
            "typeElementId": "machine-status-type",
            "parentId": "cnc-001",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "cnc-001"
            },
            "records": [
                {
                    "value": {
                        "MachineState": "Running",
                        "PowerConsumption": 12.5,
                        "EnergyIntensity": 0.42
                    },
                    "quality": "GOOD",
                    "timestamp": now()
                }
            ]
        },
        # CNC-001 Spindle
        {
            "elementId": "cnc-001-spindle",
            "displayName": "CNC-001 Main Spindle",
            "typeElementId": "spindle-type",
            "parentId": "cnc-001",
            "isComposition": True,
            "relationships": {
                "ComponentOf": "cnc-001",
                "HasComponent": ["cnc-001-spindle-motor"]
            }
        },
        # CNC-001 Spindle Motor
        {
            "elementId": "cnc-001-spindle-motor",
            "displayName": "CNC-001 Spindle Motor",
            "typeElementId": "motor-type",
            "parentId": "cnc-001-spindle",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "cnc-001-spindle"
            },
            "records": [
                {
                    "value": {
                        "RPM": 8500.0,
                        "Current": 15.2,
                        "Voltage": 380.0,
                        "Vibration": 0.12,
                        "Efficiency": 92.5,
                        "LoadRate": 65.0
                    },
                    "quality": "GOOD",
                    "timestamp": now()
                }
            ],
            "engUnit": "various"
        },
        # CNC-001 X Axis
        {
            "elementId": "cnc-001-axis-x",
            "displayName": "CNC-001 X Axis",
            "typeElementId": "axis-type",
            "parentId": "cnc-001",
            "isComposition": True,
            "relationships": {
                "ComponentOf": "cnc-001",
                "HasComponent": ["cnc-001-axis-x-position"]
            },
            "axisId": "X"
        },
        {
            "elementId": "cnc-001-axis-x-position",
            "displayName": "CNC-001 X Axis Position",
            "typeElementId": "position-type",
            "parentId": "cnc-001-axis-x",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "cnc-001-axis-x"
            },
            "records": [
                {
                    "value": {
                        "ActualPosition": 125.45,
                        "CommandedPosition": 125.50,
                        "RemainingDistance": 0.05
                    },
                    "quality": "GOOD",
                    "timestamp": now()
                }
            ],
            "engUnit": "mm"
        },
        # CNC-001 Y Axis
        {
            "elementId": "cnc-001-axis-y",
            "displayName": "CNC-001 Y Axis",
            "typeElementId": "axis-type",
            "parentId": "cnc-001",
            "isComposition": True,
            "relationships": {
                "ComponentOf": "cnc-001",
                "HasComponent": ["cnc-001-axis-y-position"]
            },
            "axisId": "Y"
        },
        {
            "elementId": "cnc-001-axis-y-position",
            "displayName": "CNC-001 Y Axis Position",
            "typeElementId": "position-type",
            "parentId": "cnc-001-axis-y",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "cnc-001-axis-y"
            },
            "records": [
                {
                    "value": {
                        "ActualPosition": 78.20,
                        "CommandedPosition": 78.25,
                        "RemainingDistance": 0.05
                    },
                    "quality": "GOOD",
                    "timestamp": now()
                }
            ],
            "engUnit": "mm"
        },
        # CNC-001 Z Axis
        {
            "elementId": "cnc-001-axis-z",
            "displayName": "CNC-001 Z Axis",
            "typeElementId": "axis-type",
            "parentId": "cnc-001",
            "isComposition": True,
            "relationships": {
                "ComponentOf": "cnc-001",
                "HasComponent": ["cnc-001-axis-z-position"]
            },
            "axisId": "Z"
        },
        {
            "elementId": "cnc-001-axis-z-position",
            "displayName": "CNC-001 Z Axis Position",
            "typeElementId": "position-type",
            "parentId": "cnc-001-axis-z",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "cnc-001-axis-z"
            },
            "records": [
                {
                    "value": {
                        "ActualPosition": -45.10,
                        "CommandedPosition": -45.00,
                        "RemainingDistance": 0.10
                    },
                    "quality": "GOOD",
                    "timestamp": now()
                }
            ],
            "engUnit": "mm"
        },
        # CNC-001 Coolant System
        {
            "elementId": "cnc-001-coolant",
            "displayName": "CNC-001 Coolant System",
            "typeElementId": "coolant-system-type",
            "parentId": "cnc-001",
            "isComposition": True,
            "relationships": {
                "ComponentOf": "cnc-001",
                "HasComponent": ["cnc-001-coolant-tank", "cnc-001-coolant-pump"]
            }
        },
        {
            "elementId": "cnc-001-coolant-tank",
            "displayName": "CNC-001 Coolant Tank",
            "typeElementId": "coolant-tank-type",
            "parentId": "cnc-001-coolant",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "cnc-001-coolant"
            },
            "records": [
                {
                    "value": {
                        "Level": 85.0,
                        "Temperature": 22.5,
                        "Capacity": 100.0
                    },
                    "quality": "GOOD",
                    "timestamp": now()
                }
            ],
            "engUnit": "L/C"
        },
        {
            "elementId": "cnc-001-coolant-pump",
            "displayName": "CNC-001 Coolant Pump",
            "typeElementId": "coolant-pump-type",
            "parentId": "cnc-001-coolant",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "cnc-001-coolant"
            },
            "records": [
                {
                    "value": {
                        "Flow": 12.5,
                        "Pressure": 4.2,
                        "Power": 0.75
                    },
                    "quality": "GOOD",
                    "timestamp": now()
                }
            ],
            "engUnit": "L/min, bar, kW"
        },

        # ==================== CNC-002 ====================
        {
            "elementId": "cnc-002",
            "displayName": "CNC Machine 002",
            "typeElementId": "cnc-base-type",
            "parentId": "cnc-work-center",
            "isComposition": True,
            "relationships": {
                "HasParent": "cnc-work-center",
                "HasComponent": [
                    "cnc-002-status",
                    "cnc-002-spindle",
                    "cnc-002-axis-x",
                    "cnc-002-axis-y",
                    "cnc-002-axis-z",
                    "cnc-002-coolant"
                ]
            },
            "manufacturer": "Mazak",
            "model": "VARIAXIS i-700",
            "serialNumber": "CNC-2021-002"
        },
        # CNC-002 Status
        {
            "elementId": "cnc-002-status",
            "displayName": "CNC-002 Status",
            "typeElementId": "machine-status-type",
            "parentId": "cnc-002",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "cnc-002"
            },
            "records": [
                {
                    "value": {
                        "MachineState": "Idle",
                        "PowerConsumption": 3.2,
                        "EnergyIntensity": 0.0
                    },
                    "quality": "GOOD",
                    "timestamp": now()
                }
            ]
        },
        # CNC-002 Spindle
        {
            "elementId": "cnc-002-spindle",
            "displayName": "CNC-002 Main Spindle",
            "typeElementId": "spindle-type",
            "parentId": "cnc-002",
            "isComposition": True,
            "relationships": {
                "ComponentOf": "cnc-002",
                "HasComponent": ["cnc-002-spindle-motor"]
            }
        },
        # CNC-002 Spindle Motor
        {
            "elementId": "cnc-002-spindle-motor",
            "displayName": "CNC-002 Spindle Motor",
            "typeElementId": "motor-type",
            "parentId": "cnc-002-spindle",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "cnc-002-spindle"
            },
            "records": [
                {
                    "value": {
                        "RPM": 0.0,
                        "Current": 0.5,
                        "Voltage": 380.0,
                        "Vibration": 0.01,
                        "Efficiency": 0.0,
                        "LoadRate": 0.0
                    },
                    "quality": "GOOD",
                    "timestamp": now()
                }
            ],
            "engUnit": "various"
        },
        # CNC-002 X Axis
        {
            "elementId": "cnc-002-axis-x",
            "displayName": "CNC-002 X Axis",
            "typeElementId": "axis-type",
            "parentId": "cnc-002",
            "isComposition": True,
            "relationships": {
                "ComponentOf": "cnc-002",
                "HasComponent": ["cnc-002-axis-x-position"]
            },
            "axisId": "X"
        },
        {
            "elementId": "cnc-002-axis-x-position",
            "displayName": "CNC-002 X Axis Position",
            "typeElementId": "position-type",
            "parentId": "cnc-002-axis-x",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "cnc-002-axis-x"
            },
            "records": [
                {
                    "value": {
                        "ActualPosition": 0.0,
                        "CommandedPosition": 0.0,
                        "RemainingDistance": 0.0
                    },
                    "quality": "GOOD",
                    "timestamp": now()
                }
            ],
            "engUnit": "mm"
        },
        # CNC-002 Y Axis
        {
            "elementId": "cnc-002-axis-y",
            "displayName": "CNC-002 Y Axis",
            "typeElementId": "axis-type",
            "parentId": "cnc-002",
            "isComposition": True,
            "relationships": {
                "ComponentOf": "cnc-002",
                "HasComponent": ["cnc-002-axis-y-position"]
            },
            "axisId": "Y"
        },
        {
            "elementId": "cnc-002-axis-y-position",
            "displayName": "CNC-002 Y Axis Position",
            "typeElementId": "position-type",
            "parentId": "cnc-002-axis-y",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "cnc-002-axis-y"
            },
            "records": [
                {
                    "value": {
                        "ActualPosition": 0.0,
                        "CommandedPosition": 0.0,
                        "RemainingDistance": 0.0
                    },
                    "quality": "GOOD",
                    "timestamp": now()
                }
            ],
            "engUnit": "mm"
        },
        # CNC-002 Z Axis
        {
            "elementId": "cnc-002-axis-z",
            "displayName": "CNC-002 Z Axis",
            "typeElementId": "axis-type",
            "parentId": "cnc-002",
            "isComposition": True,
            "relationships": {
                "ComponentOf": "cnc-002",
                "HasComponent": ["cnc-002-axis-z-position"]
            },
            "axisId": "Z"
        },
        {
            "elementId": "cnc-002-axis-z-position",
            "displayName": "CNC-002 Z Axis Position",
            "typeElementId": "position-type",
            "parentId": "cnc-002-axis-z",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "cnc-002-axis-z"
            },
            "records": [
                {
                    "value": {
                        "ActualPosition": 0.0,
                        "CommandedPosition": 0.0,
                        "RemainingDistance": 0.0
                    },
                    "quality": "GOOD",
                    "timestamp": now()
                }
            ],
            "engUnit": "mm"
        },
        # CNC-002 Coolant System
        {
            "elementId": "cnc-002-coolant",
            "displayName": "CNC-002 Coolant System",
            "typeElementId": "coolant-system-type",
            "parentId": "cnc-002",
            "isComposition": True,
            "relationships": {
                "ComponentOf": "cnc-002",
                "HasComponent": ["cnc-002-coolant-tank", "cnc-002-coolant-pump"]
            }
        },
        {
            "elementId": "cnc-002-coolant-tank",
            "displayName": "CNC-002 Coolant Tank",
            "typeElementId": "coolant-tank-type",
            "parentId": "cnc-002-coolant",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "cnc-002-coolant"
            },
            "records": [
                {
                    "value": {
                        "Level": 92.0,
                        "Temperature": 21.0,
                        "Capacity": 150.0
                    },
                    "quality": "GOOD",
                    "timestamp": now()
                }
            ],
            "engUnit": "L/C"
        },
        {
            "elementId": "cnc-002-coolant-pump",
            "displayName": "CNC-002 Coolant Pump",
            "typeElementId": "coolant-pump-type",
            "parentId": "cnc-002-coolant",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "cnc-002-coolant"
            },
            "records": [
                {
                    "value": {
                        "Flow": 0.0,
                        "Pressure": 0.0,
                        "Power": 0.0
                    },
                    "quality": "GOOD",
                    "timestamp": now()
                }
            ],
            "engUnit": "L/min, bar, kW"
        },
    ],
    "relationshipTypes": [
        {
            "elementId": "HasParent",
            "displayName": "HasParent",
            "namespaceUri": I3X_NAMESPACE,
            "relationshipId": "HasParent",
            "reverseOf": "HasChildren",
        },
        {
            "elementId": "HasChildren",
            "displayName": "HasChildren",
            "namespaceUri": I3X_NAMESPACE,
            "relationshipId": "HasChildren",
            "reverseOf": "HasParent"
        },
        {
            "elementId": "HasComponent",
            "displayName": "HasComponent",
            "namespaceUri": I3X_NAMESPACE,
            "relationshipId": "HasComponent",
            "reverseOf": "ComponentOf"
        },
        {
            "elementId": "ComponentOf",
            "displayName": "ComponentOf",
            "namespaceUri": I3X_NAMESPACE,
            "relationshipId": "ComponentOf",
            "reverseOf": "HasComponent"
        },
    ],
}
