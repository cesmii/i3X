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
            "elementId": "work-center-type",    # A unique ID within the implementation's address space
            "displayName": "WorkCenterType",    # A human readable name the implementation may wish to localize
            "namespaceUri": "https://isa.org/isa95",    # A reference to a source of the namespace, which may be external to the implementation
            "sourceTypeId": "WorkCenterType",                 # A reference to the member of the source namespace being used (or projected) for this type
            "schema": "Namespaces/isa95.json#types/work-center-type",   # A demo-implementation-specific pointer to the location of the type's schema
            "related": {"relationshipType": "HasChildren", "types": ["https://isa.org/isa95:work-unit-type"]},
        },
        {
            "elementId": "work-unit-type",
            "displayName": "WorkUnitType",
            "namespaceUri": "https://isa.org/isa95",
            "sourceTypeId": "WorkUnitType",
            "schema": "Namespaces/isa95.json#types/work-unit-type",
            "related": {"relationshipType": "HasComponent"},
        },
        {
            "elementId": "state-type",
            "displayName": "StateType",
            "namespaceUri": "https://abelara.com/equipment",
            "sourceTypeId": "StateType",
            "schema": "Namespaces/abelara.json#types/state-type",
        },
        {
            "elementId": "product-type",
            "displayName": "ProductType",
            "namespaceUri": "https://abelara.com/equipment",
            "sourceTypeId": "ProductType",
            "schema": "Namespaces/abelara.json#types/product-type",
        },
        {
            "elementId": "production-type",
            "displayName": "ProductionType",
            "namespaceUri": "https://abelara.com/equipment",
            "sourceTypeId": "ProductionType",
            "schema": "Namespaces/abelara.json#types/production-type",
            "related": {"relationshipType": "HasChildren", "types": ["https://abelara.com/equipment:product-type"]},
        },
        {
            "elementId": "measurements-type",
            "displayName": "MeasurementsType",
            "namespaceUri": "https://abelara.com/equipment",
            "sourceTypeId": "MeasurementsType",
            "schema": "Namespaces/abelara.json#types/measurements-type",
            "related": {"relationshipType": "HasComponent", "types": ["https://abelara.com/equipment:measurement-type"]},
        },
        {
            "elementId": "measurement-type",
            "displayName": "MeasurementType",
            "namespaceUri": "https://abelara.com/equipment",
            "sourceTypeId": "MeasurementType",
            "schema": "Namespaces/abelara.json#types/measurement-type",
            "related": {"relationshipType": "HasComponent", "types": ["https://abelara.com/equipment:measurement-value-type", "https://abelara.com/equipment:measurement-health-type"]},
        },
        {
            "elementId": "measurement-value-type",
            "displayName": "MeasurementValueType",
            "namespaceUri": "https://abelara.com/equipment",
            "sourceTypeId": "MeasurementValueType",
            "schema": "Namespaces/abelara.json#types/measurement-value-type"
        },
        {
            "elementId": "measurement-health-type",
            "displayName": "MeasurementHealthType",
            "namespaceUri": "https://abelara.com/equipment",
            "sourceTypeId": "MeasurementHealthType",
            "schema": "Namespaces/abelara.json#types/measurement-health-type"
        },
        {
            "elementId": "sensor-type",
            "displayName": "SensorType",
            "namespaceUri": "https://thinkiq.com/equipment",
            "sourceTypeId": "1001",
            "schema": "Namespaces/thinkiq.json#types/sensor-type"
        },
        {
            "elementId": "temperature-sensor-type",
            "displayName": "TemperatureSensorType",
            "namespaceUri": "https://thinkiq.com/equipment",
            "sourceTypeId": "1002",
            "schema": "Namespaces/thinkiq.json#types/temperature-sensor-type"
        },
        {
            "elementId": "precision-temperature-sensor-type",
            "displayName": "PrecisionTemperatureSensorType",
            "namespaceUri": "https://thinkiq.com/equipment",
            "sourceTypeId": "1003",
            "schema": "Namespaces/thinkiq.json#types/precision-temperature-sensor-type",
            "related": {"relationshipType": "InheritsFrom", "types": ["https://thinkiq.com/equipment:temperature-sensor-type"]},
        },
    ],
    "instances": [
        {
            "elementId": "pump-station",
            "displayName": "pump-station",
            "description": "West facility pump station supplying coolant to the primary production area",
            "typeElementId": "work-center-type",
            "parentId": None,
            # A platform implementation would read its graph in order to populate these required response fields.
            #   This element has child objects, but they do not make up the data of this element, so this element is NOT complex
            #   We would expect a client would not want to recurse through these relationships by default
            "isComposition": False,
            # Optional object metadata (RFC 3.1.2) — instance-level properties not declared in the type schema,
            # returned as-is when includeMetadata=true. These describe the object itself, not its value.
            "operationStartDate": "July 1, 1980",
            "lastMaintainedDate": "August 1, 2001",
            # This is where we maintain the graph relationships used above and in the /related endpoints for the mock data
            "relationships": {
                "HasChildren": [
                    "pump-101",
                    "tank-201",
                    "sensor-001",
                    "sensor-002",
                    "sensor-003"
                ],
            },
        },
        {
            "elementId": "pump-101",
            "displayName": "pump-101",
            "description": "Primary centrifugal pump supplying coolant to Tank 201 on the west production line",
            "typeElementId": "work-unit-type",
            "parentId": "pump-station",
            # This element's data is made up of the data of other elements, so this element IS complex
            #   We would expect a client would want to recurse a complex structure by default
            "isComposition": True,
            # Optional object metadata (RFC 3.1.2) — instance-level properties not declared in the type schema,
            # returned as-is when includeMetadata=true. These describe the object itself, not its value.
            "operationStartDate": "July 1, 1980",
            "lastMaintainedDate": "August 1, 2001",
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
        },
        {
            "elementId": "pump-101-state",
            "displayName": "pump-101 State",
            "typeElementId": "state-type",
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
                    "quality": "Good",
                    #Our mock platform implementation was smart enough to lift this metadata from the payload. 
                    "timestamp": "2025-10-29T18:20:44Z",
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
                    "quality": "Good",
                    "timestamp": "2025-10-28T18:20:44Z",
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
                    "quality": "Good",
                    "timestamp": "2025-10-27T18:20:44Z",
                },
            ],
        },
        {
            "elementId": "pump-101-production",
            "displayName": "pump-101 Production",
            "typeElementId": "production-type",
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
            "displayName": "pump-101 Product",
            "typeElementId": "product-type",
            "parentId": "pump-101-production",
            "isComposition": False,
            "relationships": {
                "HasParent": "pump-101-production",
            },
            "records": [
                {
                    "value": "Product A",
                    "quality": "Good",
                    "timestamp": "2025-10-28T18:20:44Z",
                },
                {
                    "value": "Product B",
                    "quality": "Good",
                    "timestamp": "2025-10-28T18:20:44Z",
                },
            ]
        },
        {
            "elementId": "pump-101-measurements",
            "displayName": "pump-101 Measurements",
            "typeElementId": "measurements-type",
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
            "displayName": "pump-101 Bearing Temperature",
            "typeElementId": "measurement-type",
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
                    "quality": "Good",
                    "timestamp": "2025-10-28T18:20:44Z",
                },
                {
                    "value": {
                        "inTolerance": True,
                        "tolerance": 5.1,
                    },
                    "quality": "Good",
                    "timestamp": "2025-10-27T18:20:44Z",
                }
            ]
        },
        {
            "elementId": "pump-101-measurements-bearing-temperature-value",
            "displayName": "Pump 101 Bearing Temperature Value",
            "typeElementId": "measurement-value-type",
            "parentId": "pump-101-bearing-temperature",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "pump-101-bearing-temperature"
            },
            # Optional object metadata (RFC 3.1.2) — instance-level properties not declared in the type schema,
            # returned as-is when includeMetadata=true. These describe the object itself, not its value.
            "engUnit": "°F",
            "interpolation": "None",
            "records": [
                {
                    "value": 70.34,
                    "quality": "Good",
                    "timestamp": "2025-10-28T18:32:47Z"
                },
                {
                    "value": 71.79,
                    "quality": "Good",
                    "timestamp": "2025-10-27T18:32:47Z"
                }
            ],
        },
        {
            "elementId": "pump-101-measurements-bearing-temperature-health",
            "displayName": "Pump 101 Bearing Health",
            "typeElementId": "measurement-health-type",
            "parentId": "pump-101-bearing-temperature",
            "isComposition": False,
            "relationships": {
                "ComponentOf": "pump-101-bearing-temperature"
            },
            "records": [
                {
                    "value": 12,
                    "quality": "Good",
                    "timestamp": "2025-10-28T18:32:47Z"
                },
                {
                    "value": 13,
                    "quality": "Good",
                    "timestamp": "2025-10-27T18:32:47Z"
                }
            ]
        },
        {
            "elementId": "tank-201",
            "displayName": "tank-201",
            "typeElementId": "work-unit-type",
            "parentId": "pump-station",
            "isComposition": False,
            "description": "Primary coolant storage tank on the west production line, capacity 500L",
            "relationships": {
                "SuppliedBy": "pump-101",
                "MonitoredBy": "sensor-001",
            },
        },
        {
            "elementId": "sensor-001",
            "displayName": "TempSensor-101",
            "typeElementId": "sensor-type",
            "parentId": "pump-station",
            "isComposition": False,
            "description": "Temperature sensor monitoring coolant level in Tank 201",
            "relationships": {
                "Monitors": "tank-201"
            },
            # Optional object metadata (RFC 3.1.2) — instance-level properties not declared in the type schema,
            # returned as-is when includeMetadata=true. These describe the object itself, not its value.
            "engUnit": "CEL",
            "calibrationDate": "2025-01-15",
            "records": [
                {
                    "value": 67.1,
                    # Should these be specified (at least as optional)?
                    "quality": "Good",
                    "timestamp": "2025-10-28T10:15:30Z",
                    # Extra value-specific metadata may originate in the publisher's payload and is allowable
                    "localTimestamp": "2025-01-28T07:15:30-03:00",
                },
                {
                    "value": 54.9,
                    "quality": "Good",
                    "timestamp": "2025-10-27T10:15:30Z",
                    "localTimestamp": "2025-01-27T07:15:30-03:00",
                },
                {
                    "value": 68.2,
                    "quality": "Good",
                    "timestamp": "2025-10-26T10:15:30Z",
                    "localTimestamp": "2025-01-26T07:15:30-03:00",
                },
            ],
        },
        {
            # Example of allOf type extension: precision-temperature-sensor-type inherits
            # temperature-sensor-type and adds accuracy + calibrationDate to the value shape.
            "elementId": "sensor-002",
            "displayName": "PrecisionTempSensor-301",
            "typeElementId": "precision-temperature-sensor-type",
            "parentId": "pump-station",
            "isComposition": False,
            "relationships": {
                "Monitors": "pump-101",
                "InheritsFrom": "temperature-sensor-type"
            },
            # Optional object metadata (RFC 3.1.2) — instance-level properties not declared in the type schema,
            # returned as-is when includeMetadata=true. These describe the object itself, not its value.
            "engUnit": "CEL",
            "records": [
                {
                    "value": {
                        "temperature": 85.2,
                        "unit": "CEL",
                        "accuracy": 0.1,
                        "calibrationDate": "2025-06-01"
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-10-28T10:15:30Z",
                },
                {
                    "value": {
                        "temperature": 83.7,
                        "unit": "CEL",
                        "accuracy": 0.1,
                        "calibrationDate": "2025-06-01"
                    },
                    "quality": "GOOD",
                    "timestamp": "2025-10-27T10:15:30Z",
                },
            ],
        },
        {
            # Example of an extended object: typed as temperature-sensor-type (which declares only
            # 'temperature' and 'unit'), but its value also carries vendor_serial and firmware_version
            # — attributes not in the declared schema. isExtended=true will be set on this object,
            # and extendedAttributes will be populated when includeMetadata=true is requested.
            "elementId": "sensor-003",
            "displayName": "TempSensor-VendorX",
            "typeElementId": "temperature-sensor-type",
            "parentId": "pump-station",
            "isComposition": False,
            "relationships": {
                "HasParent": "pump-station",
                "Monitors": "tank-201"
            },
            # Optional object metadata (RFC 3.1.2) — instance-level properties not declared in the type schema,
            # returned as-is when includeMetadata=true. These describe the object itself, not its value.
            "engUnit": "CEL",
            "records": [
                {
                    "value": {
                        "temperature": 72.4,
                        "unit": "CEL",
                        "vendor_serial": "SN-XYZ-9001",
                        "firmware_version": "2.3.1"
                    },
                    "quality": "Good",
                    "timestamp": "2025-10-28T10:15:30Z",
                },
                {
                    "value": {
                        "temperature": 71.8,
                        "unit": "CEL",
                        "vendor_serial": "SN-XYZ-9001",
                        "firmware_version": "2.3.1"
                    },
                    "quality": "Good",
                    "timestamp": "2025-10-27T10:15:30Z",
                },
            ],
        },
    ],
    "relationshipTypes": [
        # Used for topological relationships
        #   These will not usually indicate data structure complexity (one thing has another below/inside it)
        {
            "elementId": "HasParent",
            "displayName": "HasParent",
            "namespaceUri": "https://cesmii.org/i3x",
            "relationshipId": "HasParent",  # included in order to reference an external definition. for example, if the relationshipType is defined by a UA nodeset. 
            "reverseOf": "HasChildren",
        },
        {
            "elementId": "HasChildren",
            "displayName": "HasChildren",
            "namespaceUri": "https://cesmii.org/i3x",
            "relationshipId": "HasChildren",
            "reverseOf": "HasParent"
        },
        # Used for OOP relationships
        #   These will always indicate data structure complexity (one thing is made-up of another)
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
        },
        # Used for Graph relationships
        {
            "elementId": "Monitors",
            "displayName": "Monitors",
            "namespaceUri": "https://thinkiq.com/equipment",
            "relationshipId": "Monitors",
            "reverseOf": "MonitoredBy"
        },
        {
            "elementId": "MonitoredBy",
            "displayName": "MonitoredBy",
            "namespaceUri": "https://thinkiq.com/equipment",
            "relationshipId": "MonitoredBy",
            "reverseOf": "Monitors"
        },
        {
            "elementId": "SuppliesTo",
            "displayName": "SuppliesTo",
            "namespaceUri": "https://thinkiq.com/equipment",
            "relationshipId": "SuppliesTo",
            "reverseOf": "SuppliedBy"
        },
        {
            "elementId": "SuppliedBy",
            "displayName": "SuppliedBy",
            "namespaceUri": "https://thinkiq.com/equipment",
            "relationshipId": "SuppliedBy",
            "reverseOf": "SuppliesTo"
        },
    ],
}
