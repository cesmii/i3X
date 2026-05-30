from datetime import datetime

# SIMPLIFIED I3X API compliant mock data - Industrial Information Interface eXchange (RFC 001)
I3X_DATA = {
    "namespaces": [
        {"uri": "https://cesmii.org/i3x", "displayName": "I3X"},
        {"uri": "https://isa.org/isa95", "displayName": "ISA95"},
        {"uri": "https://abelara.com/equipment", "displayName": "Abelara Equipment"},
        {"uri": "https://thinkiq.com/equipment", "displayName": "ThinkIQ Equipment"}
    ],
    "objectTypes": [
        {
            "elementId": "work-center-type",
            "displayName": "WorkCenterType",
            "namespaceUri": "https://isa.org/isa95",
            "schema": "Namespaces/isa95.json#types/work-center-type",
        },
        {
            "elementId": "work-unit-type",
            "displayName": "WorkUnitType",
            "namespaceUri": "https://isa.org/isa95",
            "schema": "Namespaces/isa95.json#types/work-unit-type",
        },
        {
            "elementId": "state-type",
            "displayName": "StateType",
            "namespaceUri": "https://abelara.com/equipment",
            "schema": "Namespaces/abelara.json#types/state-type",
        },
        {
            "elementId": "product-type",
            "displayName": "ProductType",
            "namespaceUri": "https://abelara.com/equipment",
            "schema": "Namespaces/abelara.json#types/product-type",
        },
        {
            "elementId": "production-type",
            "displayName": "ProductionType",
            "namespaceUri": "https://abelara.com/equipment",
            "schema": "Namespaces/abelara.json#types/production-type",
        },
        {
            "elementId": "measurements-type",
            "displayName": "MeasurementsType",
            "namespaceUri": "https://abelara.com/equipment",
            "schema": "Namespaces/abelara.json#types/measurements-type"
        },
        {
            "elementId": "measurement-type",
            "displayName": "MeasurementType",
            "namespaceUri": "https://abelara.com/equipment",
            "schema": "Namespaces/abelara.json#types/measurement-type"
        },
        {
            "elementId": "measurement-value-type",
            "displayName": "MeasurementValueType",
            "namespaceUri": "https://abelara.com/equipment",
            "schema": "Namespaces/abelara.json#types/measurement-value-type"
        },
        {
            "elementId": "measurement-health-type",
            "displayName": "MeasurementHealthType",
            "namespaceUri": "https://abelara.com/equipment",
            "schema": "Namespaces/abelara.json#types/measurement-health-type"
        },
        {
            "elementId": "sensor-type",
            "displayName": "SensorType",
            "namespaceUri": "https://thinkiq.com/equipment",
            "schema": "Namespaces/thinkiq.json#types/sensor-type"
        },
    ],
    "instances": [
        {
            "elementId": "pump-station",
            "displayName": "[DEPRECATED - See 1.0-RC] pump-station",
            "namespaceUri": "https://isa.org/isa95",
            "typeId": "work-center-type",
            # A "/" is unsed to indicate this object is attached to the root
            "parentId": "/",
            # A platform implementation would read its graph in order to populate these required response fields.
            #   This element has child objects, but they do not make up the data of this element, so this element is NOT complex
            #   We would expect a client would not want to recurse through these relationships by default
            "isComposition": False,
            # This is where we maintain the graph relationships used above and in the /related endpoints for the mock data
            "relationships": {
                "HasParent": "/",
                "HasChildren": [
                    "pump-101",
                    "tank-201",
                    "sensor-001"
                ],
            },
            # Optional property or attribute metadata (extra fields, per RFC 3.1.2 bullet 4)
            "operationStartDate": "July 1, 1980",
            "lastMaintainedDate": "August 1, 2001"
        },
        {
            "elementId": "pump-101",
            "displayName": "[DEPRECATED - See 1.0-RC] pump-101",
            "namespaceUri": "https://isa.org/isa95",
            "typeId": "work-unit-type",
            "parentId": "pump-station",
            # This element's data is made up of the data of other elements, so this element IS complex
            #   We would expect a client would want to recurse a complex structure by default
            "isComposition": True,
            # This is where we maintain the graph relationships used above and in the /related endpoints for the mock data
            "relationships": {
                "HasParent": "pump-station",
                "HasComponent": [
                    "pump-101-state",
                    "pump-101-production",
                    "pump-101-measurements"
                ],
                "SuppliesTo": ["tank-201"],
            },
            # Optional property or attribute metadata (extra fields, per RFC 3.1.2 bullet 4)
            "operationStartDate": "July 1, 1980",
            "lastMaintainedDate": "August 1, 2001"
        },
        {
            "elementId": "pump-101-state",
            "displayName": "[DEPRECATED - See 1.0-RC] pump-101 State",
            "namespaceUri": "https://abelara.com/equipment",
            "typeId": "state-type",
            "parentId": "pump-101",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "pump-101",
            },
            "records": [
                {
                    "value": {
                        "description": "Pump is in maintenance",
                        "color": "#800080",
                        "type": {
                            "id": 5,
                            "name": "Maintenance",
                            "description": "Equipment under maintenance",
                        },
                        "metadata": {
                            "source": "plc-controller",
                            "uri": "opc://plc1/DB1.DBW0",
                            "asset": {
                                "id": 101,
                                "name": "Pump-101",
                                "description": "Centrifugal water pump for cooling system",
                            },
                        },
                    },
                    #Values need metadata too, in fact some of the RFC 3.1.2 Object Metadata really belongs at the Value level
                    "quality": "GOOD",
                    #Our mock platform implementation was smart enough to lift this metadata from the payload. 
                    "timestamp": "2025-10-29T18:20:44.779036+00:00",
                },
                {
                    "value": {
                        "description": "Pump is in operation",
                        "color": "#00FF00",
                        "type": {
                            "id": 1,
                            "name": "Operating",
                            "description": "Equipment operating normally",
                        },
                        "metadata": {
                            "source": "plc-controller",
                            "uri": "opc://plc1/DB1.DBW0",
                            "asset": {
                                "id": 101,
                                "name": "Pump-101",
                                "description": "Centrifugal water pump for cooling system",
                            },
                        },
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-10-28T18:20:44.779036+00:00",
                },
                {
                    "value": {
                        "description": "Pump is in operation",
                        "color": "#FFFF00",
                        "type": {
                            "id": 1,
                            "name": "Starved",
                            "description": "Equipment starved",
                        },
                        "metadata": {
                            "source": "plc-controller",
                            "uri": "opc://plc1/DB1.DBW0",
                            "asset": {
                                "id": 101,
                                "name": "Pump-101",
                                "description": "Centrifugal water pump for cooling system",
                            },
                        },
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-10-27T18:20:44.779036+00:00",
                },
            ],
        },
        {
            "elementId": "pump-101-production",
            "displayName": "[DEPRECATED - See 1.0-RC] pump-101 Production",
            "namespaceUri": "https://abelara.com/equipment",
            "typeId": "production-type",
            "parentId": "pump-101",
            # This element has related data, but that data is not a part of the definition of this data, so it is not complex
            "isComposition": False,
            "relationships": {
                "ComponentOf": "pump-101",
                # Related classes, not a part of the definition of this element. Client can "dig" through HasChildren as needed
                "HasChildren": [
                    "pump-101-production-product",
                ]
            },
        },
        {
            "elementId": "pump-101-production-product",
            "displayName": "[DEPRECATED - See 1.0-RC] pump-101 Product",
            "namespaceUri": "https://abelara.com/equipment",
            "typeId": "product-type",
            "parentId": "pump-101-production",
            "isComposition": False,
            "relationships": {
                "HasParent": "pump-101-production",
            },
            "records": [
                {
                    "value": "Product A",
                    "quality": "GOOD",
                    "timestamp": "2025-10-28T18:20:44.779036+00:00",
                },
                {
                    "value": "Product B",
                    "quality": "GOOD",
                    "timestamp": "2025-10-28T18:20:44.779036+00:00",
                },
            ]
        },
        {
            "elementId": "pump-101-measurements",
            "displayName": "[DEPRECATED - See 1.0-RC] pump-101 Measurements",
            "namespaceUri": "https://abelara.com/equipment",
            "typeId": "measurements-type",
            "parentId": "pump-101",
            # This element has related data, and that data IS a part of the definition of this data, so it IS complex
            "isComposition": True,
            "relationships": {
                "ComponentOf": "pump-101",
                "HasComponent": [
                    "pump-101-bearing-temperature",
                ],
            },
        },
        {
            "elementId": "pump-101-bearing-temperature",
            "displayName": "[DEPRECATED - See 1.0-RC] pump-101 Bearing Temperature",
            "namespaceUri": "https://abelara.com/equipment",
            "typeId": "measurement-type",
            "parentId": "pump-101-measurements",
            # This element has related data, and that data IS a part of the definition of this data, so it IS complex
            "isComposition": True,
            "relationships": {
                "ComponentOf": "pump-101-measurements",
                "HasComponent": ["pump-101-measurements-bearing-temperature-value", "pump-101-measurements-bearing-temperature-health"]
            },
            "records": [
                {
                    "value": {
                        "inTolerance": True,
                        "tolerance": 5.0,
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-10-28T18:20:44.779036+00:00",
                },
                {
                    "value": {
                        "inTolerance": True,
                        "tolerance": 5.1,
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-10-27T18:20:44.779036+00:00",
                }
            ]
        },
        {
            "elementId": "pump-101-measurements-bearing-temperature-value",
            "displayName": "[DEPRECATED - See 1.0-RC] Pump 101 Bearing Temperature Value",
            "namespaceUri": "https://abelara.com/equipment",
            "typeId": "measurement-value-type",
            "parentId": "pump-101-bearing-temperature",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "pump-101-bearing-temperature"
            },
            "records": [
                {
                    "value": 70.34,
                    "quality": "GOOD",
                    "timestamp": "2025-10-28T18:32:47.673157+00:00"
                },
                {
                    "value": 71.79,
                    "quality": "GOOD",
                    "timestamp": "2025-10-27T18:32:47.673157+00:00"
                }
            ],
             # Optional Object Metadata (RFC 3.1.2)
            "engUnit": "°F",
            "interpolation": "None"
        },
        {
            "elementId": "pump-101-measurements-bearing-temperature-health",
            "displayName": "[DEPRECATED - See 1.0-RC] Pump 101 Bearing Health",
            "namespaceUri": "https://abelara.com/equipment",
            "typeId": "measurement-health-type",
            "parentId": "pump-101-bearing-temperature",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "pump-101-bearing-temperature"
            },
            "records": [
                {
                    "value": 12,
                    "quality": "GOOD",
                    "timestamp": "2025-10-28T18:32:47.673157+00:00"
                },
                {
                    "value": 13,
                    "quality": "GOOD",
                    "timestamp": "2025-10-27T18:32:47.673157+00:00"
                }
            ]
        },
        {
            "elementId": "tank-201",
            "displayName": "[DEPRECATED - See 1.0-RC] tank-201",
            "namespaceUri": "https://isa.org/isa95",
            "typeId": "work-unit-type",
            "parentId": "pump-station",
            "isComposition": False,
            "relationships": {
                "SuppliedBy": "pump-101",
                "MonitoredBy": "sensor-001",
            },
        },
        {
            "elementId": "sensor-001",
            "displayName": "[DEPRECATED - See 1.0-RC] TempSensor-101",
            "namespaceUri": "https://thinkiq.com/equipment",
            "typeId": "sensor-type",
            "parentId": "pump-station",
            "isComposition": False,
            "relationships": {
                "Monitors": "tank-201"
            },
            "records": [
                {
                    "value": 67.1,
                    # Should these be specified (at least as optional)?
                    "quality": "GOOD",
                    "timestamp": "2025-10-28T10:15:30Z",
                    # Extra value-specific metadata may originate in the publisher's payload and is allowable
                    "localTimestamp": "2025-01-28T07:15:30-03:00",
                },
                {
                    "value": 54.9,
                    "quality": "GOOD",
                    "timestamp": "2025-10-27T10:15:30Z",
                    "localTimestamp": "2025-01-27T07:15:30-03:00",
                },
                {
                    "value": 68.2,
                    "quality": "GOOD",
                    "timestamp": "2025-10-26T10:15:30Z",
                    "localTimestamp": "2025-01-26T07:15:30-03:00",
                },
            ],
            # Optional Object Metadata (RFC 3.1.2)
            "engUnit": "CEL",
            "calibrationDate": "2025-01-15",
        },
    ],
    "relationshipTypes": [
        # Used for topological relationships
        #   These will not usually indicate data structure complexity (one thing has another below/inside it)
        {
            "elementId": "HasParent",
            "displayName": "HasParent",
            "namespaceUri": "https://cesmii.org/i3x",
            "reverseOf": "HasChildren",
        },
        {
            "elementId": "HasChildren",
            "displayName": "HasChildren",
            "namespaceUri": "https://cesmii.org/i3x",
            "reverseOf": "HasParent"
        },
        # Used for OOP relationships
        #   These will always indicate data structure complexity (one thing is made-up of another)
        {
            "elementId": "HasComponent",
            "displayName": "HasComponent",
            "namespaceUri": "https://cesmii.org/i3x",
            "reverseOf": "ComponentOf"
        },
        {
            "elementId": "ComponentOf",
            "displayName": "ComponentOf",
            "namespaceUri": "https://cesmii.org/i3x",
            "reverseOf": "HasComponent"
        },
        {
            "elementId": "InheritedBy",
            "displayName": "InheritedBy",
            "namespaceUri": "https://cesmii.org/i3x",
            "reverseOf": "InheritsFrom"
        },
        {
            "elementId": "InheritsFrom",
            "displayName": "InheritsFrom",
            "namespaceUri": "https://cesmii.org/i3x",
            "reverseOf": "InheritedBy"
        },
        # Used for Graph relationships
        {
            "elementId": "Monitors",
            "displayName": "Monitors",
            "namespaceUri": "https://thinkiq.com/equipment",
            "reverseOf": "MonitoredBy"
        },
        {
            "elementId": "MonitoredBy",
            "displayName": "MonitoredBy",
            "namespaceUri": "https://thinkiq.com/equipment",
            "reverseOf": "Monitors"
        },
        {
            "elementId": "SuppliesTo",
            "displayName": "SuppliesTo",
            "namespaceUri": "https://thinkiq.com/equipment",
            "reverseOf": "SuppliedBy"
        },
        {
            "elementId": "SuppliedBy",
            "displayName": "SuppliedBy",
            "namespaceUri": "https://thinkiq.com/equipment",
            "reverseOf": "SuppliesTo"
        },
    ],
}
