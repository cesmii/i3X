# Ignition CNC Mock Data - I3X API compliant
# Based on OPC UA CNC profile with Inductive Automation UDT extensions
# Element IDs use Base64 encoding matching the original Ignition format

import base64

def _encode_id(path):
    """Encode a path to Base64 element ID (strip padding like original)"""
    return base64.b64encode(path.encode('utf-8')).decode('utf-8').rstrip('=')

# Pre-computed Base64 element IDs for types (matching original format)
TYPE_IDS = {
    # OPC Foundation types - folder-type stays as-is per original
    "folder-type": "folder-type",
    "NetworkAddressDataType": _encode_id("[default]_types_/UA/NetworkAddressDataType"),
    # Inductive Automation UDT
    "Motor": _encode_id("[default]_types_/Motor"),
    # CESMII CNC Profile types
    "CNCBaseType": _encode_id("[default]_types_/profiles/CNC/CNCBaseType"),
    "MachineInformationType": _encode_id("[default]_types_/profiles/CNC/MachineInformationType"),
    "Identification": _encode_id("[default]_types_/profiles/CNC/Identification"),
    "MachineStatusType": _encode_id("[default]_types_/profiles/CNC/MachineStatusType"),
    "CoolantSystemType": _encode_id("[default]_types_/profiles/CNC/CoolantSystemType"),
    "ICoolantPumpType": _encode_id("[default]_types_/profiles/CNC/ICoolantPumpType"),
    "ICoolantTankType": _encode_id("[default]_types_/profiles/CNC/ICoolantTankType"),
    "ICoolantFilterType": _encode_id("[default]_types_/profiles/CNC/ICoolantFilterType"),
    "ToolType": _encode_id("[default]_types_/profiles/CNC/ToolType"),
    "IToolInformationType": _encode_id("[default]_types_/profiles/CNC/IToolInformationType"),
    "ToolStatusType": _encode_id("[default]_types_/profiles/CNC/ToolStatusType"),
    "ChannelType": _encode_id("[default]_types_/profiles/CNC/ChannelType"),
    "PositionType": _encode_id("[default]_types_/profiles/CNC/PositionType"),
    "CommandType": _encode_id("[default]_types_/profiles/CNC/CommandType"),
    "SpindleType": _encode_id("[default]_types_/profiles/CNC/SpindleType"),
    "AxisType": _encode_id("[default]_types_/profiles/CNC/AxisType"),
    "MotorType": _encode_id("[default]_types_/profiles/CNC/MotorType"),
}

IGNITION_CNC_DATA = {
    "namespaces": [
        {
            "uri": "http://opcfoundation.org/UA/",
            "displayName": "OPC Foundation UA"
        },
        {
            "uri": "https://inductiveautomation.com/UDT",
            "displayName": "Inductive Automation UDT"
        },
        {
            "uri": "http://cesmii.net/profiles/CNC",
            "displayName": "CESMII CNC Profile"
        }
    ],
    "objectTypes": [
        # OPC Foundation types
        {
            "elementId": TYPE_IDS["folder-type"],
            "displayName": "Folder",
            "namespaceUri": "http://opcfoundation.org/UA/",
            "sourceTypeId": "folder-type",
            "schema": "Namespaces/opcfoundation.json#types/folder-type"
        },
        {
            "elementId": TYPE_IDS["NetworkAddressDataType"],
            "displayName": "NetworkAddressDataType",
            "namespaceUri": "http://opcfoundation.org/UA/",
            "sourceTypeId": "[default]_types_/UA/NetworkAddressDataType",
            "schema": "Namespaces/opcfoundation.json#types/NetworkAddressDataType"
        },
        # Inductive Automation UDT types
        {
            "elementId": TYPE_IDS["Motor"],
            "displayName": "Motor",
            "namespaceUri": "https://inductiveautomation.com/UDT",
            "sourceTypeId": "[default]_types_/Motor",
            "schema": "Namespaces/inductive.json#types/Motor"
        },
        # CESMII CNC Profile types
        {
            "elementId": TYPE_IDS["CNCBaseType"],
            "displayName": "CNCBaseType",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "sourceTypeId": "[default]_types_/profiles/CNC/CNCBaseType",
            "schema": "Namespaces/cesmii_cnc.json#types/CNCBaseType"
        },
        {
            "elementId": TYPE_IDS["MachineInformationType"],
            "displayName": "MachineInformationType",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "sourceTypeId": "[default]_types_/profiles/CNC/MachineInformationType",
            "schema": "Namespaces/cesmii_cnc.json#types/MachineInformationType"
        },
        {
            "elementId": TYPE_IDS["Identification"],
            "displayName": "Identification",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "sourceTypeId": "[default]_types_/profiles/CNC/Identification",
            "schema": "Namespaces/cesmii_cnc.json#types/Identification"
        },
        {
            "elementId": TYPE_IDS["MachineStatusType"],
            "displayName": "MachineStatusType",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "sourceTypeId": "[default]_types_/profiles/CNC/MachineStatusType",
            "schema": "Namespaces/cesmii_cnc.json#types/MachineStatusType"
        },
        {
            "elementId": TYPE_IDS["CoolantSystemType"],
            "displayName": "CoolantSystemType",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "sourceTypeId": "[default]_types_/profiles/CNC/CoolantSystemType",
            "schema": "Namespaces/cesmii_cnc.json#types/CoolantSystemType"
        },
        {
            "elementId": TYPE_IDS["ICoolantPumpType"],
            "displayName": "ICoolantPumpType",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "sourceTypeId": "[default]_types_/profiles/CNC/ICoolantPumpType",
            "schema": "Namespaces/cesmii_cnc.json#types/ICoolantPumpType"
        },
        {
            "elementId": TYPE_IDS["ICoolantTankType"],
            "displayName": "ICoolantTankType",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "sourceTypeId": "[default]_types_/profiles/CNC/ICoolantTankType",
            "schema": "Namespaces/cesmii_cnc.json#types/ICoolantTankType"
        },
        {
            "elementId": TYPE_IDS["ICoolantFilterType"],
            "displayName": "ICoolantFilterType",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "sourceTypeId": "[default]_types_/profiles/CNC/ICoolantFilterType",
            "schema": "Namespaces/cesmii_cnc.json#types/ICoolantFilterType"
        },
        {
            "elementId": TYPE_IDS["ToolType"],
            "displayName": "ToolType",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "sourceTypeId": "[default]_types_/profiles/CNC/ToolType",
            "schema": "Namespaces/cesmii_cnc.json#types/ToolType"
        },
        {
            "elementId": TYPE_IDS["IToolInformationType"],
            "displayName": "IToolInformationType",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "sourceTypeId": "[default]_types_/profiles/CNC/IToolInformationType",
            "schema": "Namespaces/cesmii_cnc.json#types/IToolInformationType"
        },
        {
            "elementId": TYPE_IDS["ToolStatusType"],
            "displayName": "ToolStatusType",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "sourceTypeId": "[default]_types_/profiles/CNC/ToolStatusType",
            "schema": "Namespaces/cesmii_cnc.json#types/ToolStatusType"
        },
        {
            "elementId": TYPE_IDS["ChannelType"],
            "displayName": "ChannelType",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "sourceTypeId": "[default]_types_/profiles/CNC/ChannelType",
            "schema": "Namespaces/cesmii_cnc.json#types/ChannelType"
        },
        {
            "elementId": TYPE_IDS["PositionType"],
            "displayName": "PositionType",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "sourceTypeId": "[default]_types_/profiles/CNC/PositionType",
            "schema": "Namespaces/cesmii_cnc.json#types/PositionType"
        },
        {
            "elementId": TYPE_IDS["CommandType"],
            "displayName": "CommandType",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "sourceTypeId": "[default]_types_/profiles/CNC/CommandType",
            "schema": "Namespaces/cesmii_cnc.json#types/CommandType"
        },
        {
            "elementId": TYPE_IDS["SpindleType"],
            "displayName": "SpindleType",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "sourceTypeId": "[default]_types_/profiles/CNC/SpindleType",
            "schema": "Namespaces/cesmii_cnc.json#types/SpindleType"
        },
        {
            "elementId": TYPE_IDS["AxisType"],
            "displayName": "AxisType",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "sourceTypeId": "[default]_types_/profiles/CNC/AxisType",
            "schema": "Namespaces/cesmii_cnc.json#types/AxisType"
        },
        {
            "elementId": TYPE_IDS["MotorType"],
            "displayName": "MotorType",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "sourceTypeId": "[default]_types_/profiles/CNC/MotorType",
            "schema": "Namespaces/cesmii_cnc.json#types/MotorType"
        }
    ],
    "relationshipTypes": [
        {
            "elementId": "HasParent",
            "displayName": "HasParent",
            "namespaceUri": "https://cesmii.org/i3x",
            "relationshipId": "HasParent",
            "reverseOf": "HasChildren"
        },
        {
            "elementId": "HasChildren",
            "displayName": "HasChildren",
            "namespaceUri": "https://cesmii.org/i3x",
            "relationshipId": "HasChildren",
            "reverseOf": "HasParent"
        },
        {
            "elementId": "HasComponent",
            "displayName": "HasComponent",
            "namespaceUri": "https://cesmii.org/i3x",
            "relationshipId": "HasComponent",
            "reverseOf": "ComponentOf"
        },
        {
            "elementId": "ComponentOf",
            "displayName": "ComponentOf",
            "namespaceUri": "https://cesmii.org/i3x",
            "relationshipId": "ComponentOf",
            "reverseOf": "HasComponent"
        },
        {
            "elementId": "InheritedBy",
            "displayName": "InheritedBy",
            "namespaceUri": "https://cesmii.org/i3x",
            "relationshipId": "InheritedBy",
            "reverseOf": "InheritsFrom"
        },
        {
            "elementId": "InheritsFrom",
            "displayName": "InheritsFrom",
            "namespaceUri": "https://cesmii.org/i3x",
            "relationshipId": "InheritsFrom",
            "reverseOf": "InheritedBy"
        }
    ],
    "instances": [
        # Root folder
        {
            "elementId": "cnc-shop-floor",
            "displayName": "CNC Shop Floor",
            "namespaceUri": "http://opcfoundation.org/UA/",
            "typeElementId": TYPE_IDS["folder-type"],
            "parentId": None,
            "isComposition": False,
            "static": True,
            "relationships": {
                "HasChildren": ["cnc-machine-001"]
            }
        },
        # CNC Machine
        {
            "elementId": "cnc-machine-001",
            "displayName": "CNC Machine 001",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["CNCBaseType"],
            "parentId": "cnc-shop-floor",
            "isComposition": True,
            "static": True,
            "relationships": {
                "HasParent": "cnc-shop-floor",
                "HasComponent": [
                    "machine-info",
                    "channel-001",
                    "spindle-001",
                    "axis-x",
                    "axis-y",
                    "axis-z"
                ]
            }
        },
        # Machine Information
        {
            "elementId": "machine-info",
            "displayName": "Machine Information",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["MachineInformationType"],
            "parentId": "cnc-machine-001",
            "isComposition": True,
            "static": True,
            "relationships": {
                "ComponentOf": "cnc-machine-001",
                "HasComponent": [
                    "identification",
                    "machine-status",
                    "coolant-system",
                    "tool-list"
                ]
            }
        },
        # Identification
        {
            "elementId": "identification",
            "displayName": "Identification",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["Identification"],
            "parentId": "machine-info",
            "isComposition": False,
            "static": True,
            "relationships": {
                "ComponentOf": "machine-info"
            },
            "records": [
                {
                    "value": {
                        "Manufacturer": "Haas Automation",
                        "Model": "VF-2SS",
                        "SerialNumber": "1234567890",
                        "YearOfConstruction": 2022,
                        "SoftwareRevision": "100.22.000.1200"
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T08:00:00Z"
                }
            ]
        },
        # Machine Status
        {
            "elementId": "machine-status",
            "displayName": "Machine Status",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["MachineStatusType"],
            "parentId": "machine-info",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "machine-info"
            },
            "records": [
                {
                    "value": {
                        "MachineState": "Running",
                        "PowerConsumption": 12.5,
                        "EnergyIntensity": 0.85,
                        "OperatingMode": "Automatic",
                        "AlarmActive": False
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T10:30:00Z"
                }
            ]
        },
        # Coolant System
        {
            "elementId": "coolant-system",
            "displayName": "Coolant System",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["CoolantSystemType"],
            "parentId": "machine-info",
            "isComposition": True,
            "static": True,
            "relationships": {
                "ComponentOf": "machine-info",
                "HasComponent": [
                    "coolant-pump",
                    "coolant-tank",
                    "coolant-filter"
                ]
            }
        },
        # Coolant Pump
        {
            "elementId": "coolant-pump",
            "displayName": "Coolant Pump",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["ICoolantPumpType"],
            "parentId": "coolant-system",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "coolant-system"
            },
            "records": [
                {
                    "value": {
                        "Pressure": 4.5,
                        "Flow": 25.0,
                        "Power": 750,
                        "Running": True
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T10:30:00Z"
                }
            ]
        },
        # Coolant Tank
        {
            "elementId": "coolant-tank",
            "displayName": "Coolant Tank",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["ICoolantTankType"],
            "parentId": "coolant-system",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "coolant-system"
            },
            "records": [
                {
                    "value": {
                        "Level": 85.0,
                        "Temperature": 22.5,
                        "Capacity": 200,
                        "LowLevelAlarm": False
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T10:30:00Z"
                }
            ]
        },
        # Coolant Filter
        {
            "elementId": "coolant-filter",
            "displayName": "Coolant Filter",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["ICoolantFilterType"],
            "parentId": "coolant-system",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "coolant-system"
            },
            "records": [
                {
                    "value": {
                        "Status": "Normal",
                        "Clock": 1250.5,
                        "PressureDrop": 0.15
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T10:30:00Z"
                }
            ]
        },
        # Tool List Container
        {
            "elementId": "tool-list",
            "displayName": "Tool List",
            "namespaceUri": "http://opcfoundation.org/UA/",
            "typeElementId": TYPE_IDS["folder-type"],
            "parentId": "machine-info",
            "isComposition": True,
            "static": True,
            "relationships": {
                "ComponentOf": "machine-info",
                "HasComponent": ["tool-001"]
            }
        },
        # Tool 001
        {
            "elementId": "tool-001",
            "displayName": "Tool 001",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["ToolType"],
            "parentId": "tool-list",
            "isComposition": True,
            "static": True,
            "relationships": {
                "ComponentOf": "tool-list",
                "HasComponent": ["tool-001-info", "tool-001-status"]
            }
        },
        # Tool 001 Information
        {
            "elementId": "tool-001-info",
            "displayName": "Tool 001 Information",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["IToolInformationType"],
            "parentId": "tool-001",
            "isComposition": False,
            "static": True,
            "relationships": {
                "ComponentOf": "tool-001"
            },
            "records": [
                {
                    "value": {
                        "Name": "End Mill 10mm",
                        "ToolNumber": 1,
                        "Diameter": 10.0,
                        "Length": 75.0,
                        "ToolType": "EndMill",
                        "Material": "Carbide"
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T08:00:00Z"
                }
            ]
        },
        # Tool 001 Status
        {
            "elementId": "tool-001-status",
            "displayName": "Tool 001 Status",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["ToolStatusType"],
            "parentId": "tool-001",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "tool-001"
            },
            "records": [
                {
                    "value": {
                        "Temperature": 45.0,
                        "CuttingForce": 850.0,
                        "WearLevel": 15.0,
                        "InUse": True
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T10:30:00Z"
                }
            ]
        },
        # Channel 001
        {
            "elementId": "channel-001",
            "displayName": "Channel 001",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["ChannelType"],
            "parentId": "cnc-machine-001",
            "isComposition": True,
            "relationships": {
                "ComponentOf": "cnc-machine-001",
                "HasComponent": ["position-bcs", "position-wcs"]
            },
            "records": [
                {
                    "value": {
                        "ChannelNumber": 1,
                        "ActiveProgram": "O1234",
                        "ProgramStatus": "Running",
                        "FeedOverride": 100.0,
                        "SpeedOverride": 100.0
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T10:30:00Z"
                }
            ]
        },
        # Position BCS (Basic Coordinate System)
        {
            "elementId": "position-bcs",
            "displayName": "Position BCS",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["PositionType"],
            "parentId": "channel-001",
            "isComposition": True,
            "relationships": {
                "ComponentOf": "channel-001",
                "HasComponent": ["position-bcs-x", "position-bcs-y", "position-bcs-z"]
            },
            "records": [
                {
                    "value": {
                        "CoordinateSystem": "BCS"
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T10:30:00Z"
                }
            ]
        },
        # Position BCS X
        {
            "elementId": "position-bcs-x",
            "displayName": "Position BCS X",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["CommandType"],
            "parentId": "position-bcs",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "position-bcs"
            },
            "records": [
                {
                    "value": {
                        "Commanded": 125.500,
                        "Actual": 125.498,
                        "Error": 0.002
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T10:30:00Z"
                }
            ],
            "engUnit": "mm"
        },
        # Position BCS Y
        {
            "elementId": "position-bcs-y",
            "displayName": "Position BCS Y",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["CommandType"],
            "parentId": "position-bcs",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "position-bcs"
            },
            "records": [
                {
                    "value": {
                        "Commanded": 75.250,
                        "Actual": 75.248,
                        "Error": 0.002
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T10:30:00Z"
                }
            ],
            "engUnit": "mm"
        },
        # Position BCS Z
        {
            "elementId": "position-bcs-z",
            "displayName": "Position BCS Z",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["CommandType"],
            "parentId": "position-bcs",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "position-bcs"
            },
            "records": [
                {
                    "value": {
                        "Commanded": -50.100,
                        "Actual": -50.098,
                        "Error": -0.002
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T10:30:00Z"
                }
            ],
            "engUnit": "mm"
        },
        # Position WCS (Work Coordinate System)
        {
            "elementId": "position-wcs",
            "displayName": "Position WCS",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["PositionType"],
            "parentId": "channel-001",
            "isComposition": True,
            "relationships": {
                "ComponentOf": "channel-001",
                "HasComponent": ["position-wcs-x", "position-wcs-y", "position-wcs-z"]
            },
            "records": [
                {
                    "value": {
                        "CoordinateSystem": "WCS"
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T10:30:00Z"
                }
            ]
        },
        # Position WCS X
        {
            "elementId": "position-wcs-x",
            "displayName": "Position WCS X",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["CommandType"],
            "parentId": "position-wcs",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "position-wcs"
            },
            "records": [
                {
                    "value": {
                        "Commanded": 25.500,
                        "Actual": 25.498,
                        "Error": 0.002
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T10:30:00Z"
                }
            ],
            "engUnit": "mm"
        },
        # Position WCS Y
        {
            "elementId": "position-wcs-y",
            "displayName": "Position WCS Y",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["CommandType"],
            "parentId": "position-wcs",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "position-wcs"
            },
            "records": [
                {
                    "value": {
                        "Commanded": -25.250,
                        "Actual": -25.252,
                        "Error": 0.002
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T10:30:00Z"
                }
            ],
            "engUnit": "mm"
        },
        # Position WCS Z
        {
            "elementId": "position-wcs-z",
            "displayName": "Position WCS Z",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["CommandType"],
            "parentId": "position-wcs",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "position-wcs"
            },
            "records": [
                {
                    "value": {
                        "Commanded": 50.100,
                        "Actual": 50.102,
                        "Error": -0.002
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T10:30:00Z"
                }
            ],
            "engUnit": "mm"
        },
        # Spindle 001
        {
            "elementId": "spindle-001",
            "displayName": "Spindle 001",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["SpindleType"],
            "parentId": "cnc-machine-001",
            "isComposition": True,
            "static": True,
            "relationships": {
                "ComponentOf": "cnc-machine-001",
                "HasComponent": ["spindle-motor", "spindle-rpm"]
            },
            "records": [
                {
                    "value": {
                        "SpindleNumber": 1,
                        "MaxRPM": 12000,
                        "MaxTorque": 119
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T08:00:00Z"
                }
            ]
        },
        # Spindle Motor
        {
            "elementId": "spindle-motor",
            "displayName": "Spindle Motor",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["MotorType"],
            "parentId": "spindle-001",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "spindle-001"
            },
            "records": [
                {
                    "value": {
                        "RPM": 8500,
                        "Current": 15.5,
                        "Voltage": 380,
                        "Vibration": 0.8,
                        "Temperature": 55.0,
                        "Torque": 45.0
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T10:30:00Z"
                }
            ]
        },
        # Spindle RPM Command
        {
            "elementId": "spindle-rpm",
            "displayName": "Spindle RPM",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["CommandType"],
            "parentId": "spindle-001",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "spindle-001"
            },
            "records": [
                {
                    "value": {
                        "Commanded": 8500,
                        "Actual": 8498,
                        "Error": 2
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T10:30:00Z"
                }
            ],
            "engUnit": "RPM"
        },
        # Axis X
        {
            "elementId": "axis-x",
            "displayName": "Axis X",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["AxisType"],
            "parentId": "cnc-machine-001",
            "isComposition": True,
            "static": True,
            "relationships": {
                "ComponentOf": "cnc-machine-001",
                "HasComponent": ["axis-x-motor"]
            },
            "records": [
                {
                    "value": {
                        "AxisName": "X",
                        "AxisNumber": 1,
                        "IsHomed": True,
                        "MaxTravel": 762,
                        "MaxVelocity": 35560
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T08:00:00Z"
                }
            ]
        },
        # Axis X Motor
        {
            "elementId": "axis-x-motor",
            "displayName": "Axis X Motor",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["MotorType"],
            "parentId": "axis-x",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "axis-x"
            },
            "records": [
                {
                    "value": {
                        "RPM": 2500,
                        "Current": 8.5,
                        "Voltage": 380,
                        "Vibration": 0.3,
                        "Temperature": 42.0,
                        "Torque": 25.0
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T10:30:00Z"
                }
            ]
        },
        # Axis Y
        {
            "elementId": "axis-y",
            "displayName": "Axis Y",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["AxisType"],
            "parentId": "cnc-machine-001",
            "isComposition": True,
            "static": True,
            "relationships": {
                "ComponentOf": "cnc-machine-001",
                "HasComponent": ["axis-y-motor"]
            },
            "records": [
                {
                    "value": {
                        "AxisName": "Y",
                        "AxisNumber": 2,
                        "IsHomed": True,
                        "MaxTravel": 406,
                        "MaxVelocity": 35560
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T08:00:00Z"
                }
            ]
        },
        # Axis Y Motor
        {
            "elementId": "axis-y-motor",
            "displayName": "Axis Y Motor",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["MotorType"],
            "parentId": "axis-y",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "axis-y"
            },
            "records": [
                {
                    "value": {
                        "RPM": 1800,
                        "Current": 7.2,
                        "Voltage": 380,
                        "Vibration": 0.25,
                        "Temperature": 40.0,
                        "Torque": 20.0
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T10:30:00Z"
                }
            ]
        },
        # Axis Z
        {
            "elementId": "axis-z",
            "displayName": "Axis Z",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["AxisType"],
            "parentId": "cnc-machine-001",
            "isComposition": True,
            "static": True,
            "relationships": {
                "ComponentOf": "cnc-machine-001",
                "HasComponent": ["axis-z-motor"]
            },
            "records": [
                {
                    "value": {
                        "AxisName": "Z",
                        "AxisNumber": 3,
                        "IsHomed": True,
                        "MaxTravel": 508,
                        "MaxVelocity": 35560
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T08:00:00Z"
                }
            ]
        },
        # Axis Z Motor
        {
            "elementId": "axis-z-motor",
            "displayName": "Axis Z Motor",
            "namespaceUri": "http://cesmii.net/profiles/CNC",
            "typeElementId": TYPE_IDS["MotorType"],
            "parentId": "axis-z",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "axis-z"
            },
            "records": [
                {
                    "value": {
                        "RPM": 3200,
                        "Current": 12.0,
                        "Voltage": 380,
                        "Vibration": 0.35,
                        "Temperature": 48.0,
                        "Torque": 35.0
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-01-15T10:30:00Z"
                }
            ]
        }
    ]
}
