Smart Manufacturing API Working Group\
Request for Comments: 001\
Category: Informational\
Community Feedback Draft

# Common API for Industrial Information Interface eXchange (I3X)

#### Status of this Memo

This memo provides information for the Smart Manufacturing/Industry 4.0 community. It proposes a set of common interfaces for programmatic access to contextualized manufacturing information that any information platform vendor can implement to support portable application development.

While this document follows Internet RFC style and conventions, and may refer to Internet RFCs, it is not intended for consideration by the IETF or IAB as the problem domain is specific to manufacturing information systems.

#### Draft Specific Comments

As an early RFC, the authors opted to remain silent on the style of interface implementation, although both REST and GraphQL are considerations for a future specification. As a result, specific implementation guidance cannot be included at this stage. Once a style is selected, future versions of this document will be updated with more implementation details.

#### Copyright Notice

Copyright (C) CESMII, the Smart Manufacturing Institute, 2024. All Rights Reserved.

## Abstract

This document provides a common API that any information platform vendor can implement on a server to abstract the vendor-specific implementations of data organization and contextualization into a set of programmer's interfaces that helps ensure applications written against one implementation can work against another. While informed by OPC UA's REST API, and designed to be implementable against that API, this API should be supportable on a wide variety of existing, and future, information platforms. This RFC pertains specifically to the requirements for server-side implementations, and does not specifically address client requirements (save for those that may be inferred from server functionality).

## 1. Introduction

Raw manufacturing data is rarely stored in a ready-to-consume fashion, with the best commonly implemented structure being key-value pairs, often available only through live sampling, but sometimes stored historically as time-series values with a timestamp attached. Any structure or organization more sophisticated is invariably a feature of a proprietary, vendor-specific implementation, or requires homogeneous adoption of a more modern protocol and a complementary vendor ecosystem, often augmented by non-standard, or internal-only practices for semantic and structural consistency.

Vendor-dependent, non-standard, or internal-only infrastructure prevents application portability across information infrastructure variations. The part of an information stack where information value is rendered is permanently tied to the platform it was initially built against. This state is similar to that of general computing in the early 1980s, in which operating system variations proliferated, breaking application portability. In that era, highly successful commercial efforts (such as Microsoft Windows) and standardization efforts (such as POSIX) eventually led to a finite, and tolerable number of platforms that application developers must support -- kicking off 3+ decades of rapid innovation, the likes of which have never been replicated in the manufacturing world.

This document defines an API that any modern platform provider can implement to abstract applications from the specifics of the platform implementation, and ensure a base-level of application portability and compatibility. As the first RFC in a series, this document does not specify the technologies to be used for the implementation of the API; rather it focuses on the capabilities and primitives necessary for an implementation. As a RFC, this document invites feedback and discussion from the manufacturing community.

Comparisons may be drawn to the OPC/UA REST API, which exposes OPC/UA Client-Server functionality over REST. This API is not intended to replace, or compete, with this functionality. Rather it proposes a complementary API for Information Platforms that typically sit above one or more OPC/UA servers, and provide data to applications that may come from multiple data sources.

Comparisons may also be drawn to the concept of a Unified Namespace (UNS), often implemented using one or more MQTT Brokers. This API is intended to complement a UNS architecture, providing a query layer that can provide application developers with an abstraction that can sit above one or more MQTT brokers, as well as other live and historical data sources.

Finally, comparisons may be drawn to commercial offerings that provide similar functionality. This is by design: this API proposes a common programmer's interface not tied to any specific vendor's implementation, but implementable by many to create compatibility in support of application portability. Platform vendors who wish to support this API MAY choose to implement the API along-side, or on top of, their own proprietary APIs.

## 2. Definitions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in Internet RFC 2119 [RFC2119].

- **Address Space** - The complete collection of contextualized information that a platform makes available to clients
- **API** - Application Programming Interface
- **I3X** - Industrial Information Interface eXchange
- **CMIP** - Contextualized Manufacturing Information Platform that supports I3X
- **Element** - Any object or object attribute persisted by a CMIP
- **ElementId** - A platform-specific, persistent and unique key for an Element that MUST be a string
- **Control System** - An system and associated instrumentation used for industrial process control
- **Request** - A generic means of a consumer to inform the producer what information is needed
- **Response** - A generic means of a producer to fulfill the needs of the consumer
- **Query** - A read operation
- **Update** - A write operation, inclusive of creation
- **URI** - Uniform Resource Indicator, a unique identifier for a resource
  
## 3. Address Space Overview

The complete collection of Relationship Types and Relationships, Object Types and Object Instances persisted in a contextualized manufacturing information platform SHALL be referred to as the Address Space. Implementations of this API MUST have the entire Address Space readily available for querying; the authors are aware that this is an anti-pattern for implementations like a OPC UA server, where the Address Space "unfolds" through multiple Browse queries. 

### 3.1 Object Elements

The reader will observe that the API requires the underlying platform to support the idea of organizing data into objects with attributes. Those objects MUST be composable using other objects. Implementations MAY choose to have attributes of different styles internally (for example: OPC UA differentiates between properties and variables), but MUST simplify those variations to object parameters to support easy-to-consume JSON serialization. If the calling application requests additional metadata for an object, an implementation MAY return details about its specific attribute behavior (as described in [section 5.1.1](#511-response-serialization) and [section 5.1.2](#512-request-headers))

### 3.1.1 Required Object Metadata

- DisplayName: a human-friendly name for the purpose of browsing or displaying objects within an address space
- ParentId: the ElementId of the parent object
- HasChildren: if the element value is complex, a boolean value indicating if the element is composed of one or more child objects
- NamespaceURI: if the element value is an object, a URI indicating the Namespace of the object MUST be returned. If the value is an attribute, a URI indicating the Namespace SHOULD be returned.

### 3.1.2 Optional Object Metadata

- Interpolation: if the element value is interpolated, rather than stored, indicate the interpolation method
- EngUnit: a string indicating the engineering unit for measuring the element value. Where present, the definitions found in [UNECE Recommendation Number 20](https://unece.org/trade/documents/2021/06/uncefact-rec20-0) MUST be used.
- Quality: a data quality indicator following the standard established by the [OPC UA standard status codes](https://reference.opcfoundation.org/Core/Part8/v104/docs/A.3.2.3#_Ref377938607). If data quality is not available, a CMIP may omit this metadata field.
- Property or Attribute Metadata: Additional metadata related to the object as required by an implementation. Granting that existing contextual information platforms may already have defined metadata, or have an option for users to create ad-hoc metadata, this additional "property bag" MAY optionally be implemented to contain this metadata. This kind of metadata SHOULD be minimal, as Relationships are more easily mappable to a Knowledge Graph, and thus provide for richer contextual information.

### 3.2 Object Relationships

#### 3.2.1 Type Relationships

As described in 5.2.2, Objects are derived from Types. This derivation is a relationship that MUST be persisted by underlying platforms in order to support queries in the API.

#### 3.2.2 Organizational Relationships

To properly support Object Orientation, underlying platforms MUST support organizational relationships between Objects. These common relationships, such as HasParent/HasChildren, represent topological or organizational hierarchy where child objects are separate entities organized under a parent.

#### 3.2.3 Composition Relationships

Underlying platforms MAY support composition relationships (HasComponent/ComponentOf) to indicate when child data IS part of the parent's definition. When an element has `isComposition: true`, its value is composed of the values of its component children. Clients querying values for composition elements SHOULD expect to recurse through HasComponent relationships to retrieve the complete value structure.

#### 3.2.4 Non-Hierarchical Relationships

Modern manufacturing information involves relationships in data that are not strictly hierarchical. Examples include "equipment train" relationships in ISA-95, supply chain relationships that track material flow, and human resource relationships where qualified operators can be associated with equipment they have been certified on. Modern information platforms SHOULD include support for non-hierarchical relationships.

### 3.3 ObjectTypes

An ObjectType defines the schema for a class of objects within the contextualized manufacturing information model. It describes the structure, attributes, and relationships that instances of that type may exhibit, for example, defining what constitutes a `Machine`, `Sensor`, or `ProductionOrder`.

ObjectTypes serve as the basis for instantiation and discovery through the I3X interfaces, such as retrieving the definition of a single ObjectType, enumerating all available ObjectTypes within a namespace, and listing object instances derived from a given ObjectType.

### 3.4 Namespaces

A Namespace provides a logical scope within the address space that groups related types, instances, and relationships. Namespaces allow clients to explore and manage subsets of the overall model, such as those tied to a particular site, discipline, or version, without conflict or ambiguity.

### 3.5 ElementIds

Within the scope of the platform providing the I3X interface, an ElementId is a unique string value that is assigned to every fundamental element in the address space. It enables unambiguous reference, linking, and retrieval of items within the CMIP address space.  Elements that contain an ElementId include:  ObjectTypes, Object Instances, Relationship Types, and Namespaces.

## 4. I3X Address Space Methods

### 4.1 Exploratory Methods
Exploratory methods are Read-only operations, reflecting the current state of an information store at the time of the query, or in some cases, at the time specified as a query parameter. Operations to change relationships between elements are performed as an Update of an instance object, using the Value interfaces described in [section 4.2](#query-methods).

#### 4.1.1 Namespaces

This Query MUST return an array of Namespaces registered in the contextualized manufacturing information platform. All Namespaces MUST have a Namespace URI to support follow-up queries.

#### 4.1.2 Object Type Definition

This Query MUST return a JSON structure defining a Type registered in the contextualized manufacturing information platform for the requested Type's ElementId.

The Query MAY accept an array of JSON structures defining Types for the requested ElementIds to reduce round-trips where multiple Type definitions are required by an application, in which case, the return payload MUST be an array of arrays.

#### 4.1.3 Object Types

This Query MUST return an array of Type definitions registered in the contextualized manufacturing information platform. All Types MUST have an ElementId to support follow-up queries.

The the response payload MAY be filtered by NamespaceURI if indicated by an optional query parameter.

#### 4.1.4 Relationship Types

This Query MUST return an array of relationship type definitions registered in the CMIP. At minimum, implementations MUST support organizational hierarchy relationship types:
- **Organizational:** HasParent, HasChildren - for topological/organizational hierarchy

Implementations MAY support Class-composition. If supported, these minimum relationship types MUST be used:
- **Composition:** HasComponent, ComponentOf - for data composition relationships where child data is part of the parent's definition

Each relationship type definition MUST include:
- elementId: unique identifier for the relationship type
- displayName: human-readable name
- namespaceUri: the namespace URI for the relationship type
- reverseOf: the elementId of the inverse relationship type (e.g., HasParent's reverseOf is HasChildren)

Implementations MAY return additional relationship types for non-hierarchical relationships. These relationship type names SHALL be treated as keywords for follow-up queries. 

#### 4.1.5 Instances of an Object Type

This Query MUST return an array of instance objects that are of the requested Type's ElementId. The returned value payload MUST include the metadata indicated in [section 3.1.1](#311-required-object-metadata) and, if indicated by an optional query parameter, MAY include the metadata indicated in [section 3.1.2](#312-optional-object-metadata).

#### 4.1.6 Objects linked by Relationship Type

This Query MUST return an array of objects related to the requested ElementId by the Type name of relationship specified in the query. Implementations MAY support a timestamp as a query parameter, which would allow for the exploration of historical relationships. 

Each element in the returned object array MUST include the metadata indicated in [section 3.1.1](#311-required-object-metadata) and, if indicated by an optional query parameter, MAY include the metadata indicated in [section 3.1.2](#312-optional-object-metadata).

If the Query specifies an optional query parameter, an implementation MAY support following relationships to the specified depth - with the caveat that implementations may need to limit depth. As the required metadata for each object requires a boolean indication if an element HasChildren, a client may detect depth limiting by the server implementation, and recursively send follow-up requests to continue exploring the relationship hierarchy. If the depth parameter is omited, the depth SHALL be interpreted as zero. 

#### 4.1.7 Object Definition

If the ElementId exists as an instance object, this query MUST return the instance object, conforming to the Type definition from which the instance object is derived. The returned payload MUST include the most recent values of metadata indicated in [section 3.1.1](#311-required-object-metadata) and, if indicated by an optional query parameter, MAY include the most recent values of metadata indicated in [section 3.1.2](#312-optional-object-metadata).

### 4.2 Value Methods
Value methods MAY be used to both Read and Write values in a CMIP, depending on the server implementation. In order to keep this document independent of any specific implementation technology choices, a Read operation shall be referred to as a Query; a Write operation shall be referred to as an Update. An Update may change an existing value in the CMIP.

#### 4.2.1 Queries

##### 4.2.1.1 Object Element LastKnownValue

When invoked as a Query, the LastKnownValue interface MUST return the current value available in the CMIP for the requested object, by ElementId.

When invoked as a Query, the LastKnownValue interface MAY support an array of requested object ElementIds to reduce round-trips where multiple values are required by an application, in which case, the return payload MUST be an array.

When the requested element has `isComposition: true`, the Query MUST support an optional `maxDepth` parameter to control recursion through HasComponent relationships:
- maxDepth=0: Infinite recursion - include all nested component values
- maxDepth=1: No recursion - return only this element's direct value (default)
- maxDepth=N (N>1): Recurse up to N levels deep through HasComponent relationships

When recursing, the response structure MUST include the element's own value under a `value` key (if present), with each component child's value keyed by its elementId.

When invoked as a Query, the response payload MUST include the Value-Quality-Timestamp (VQT) structure:
- value: the actual data value
- quality: a quality indicator (e.g., "Good", "GoodNoData", "Bad")
- timestamp: a timestamp corresponding to the time and date the data was recorded in the CMIP, following the standard established by [Internet RFC 3339](https://www.rfc-editor.org/rfc/rfc3339)

##### 4.2.1.2 Object Element HistoricalValue

When invoked as a Query, the HistoricalValue interface MUST return an array of historical values in a time range available in the contextualized information platform for the requested object, by ElementId.

When invoked as a Query, the HistoricalValue interface MAY support an array of requested object ElementIds to reduce round-trips where multiple values are required by an application, in which case, the return payload MUST be an array of arrays.

When the requested element has `isComposition: true`, the Query MUST support an optional `maxDepth` parameter to control recursion through HasComponent relationships, with the same semantics as defined in [section 4.2.1.1](#4211-object-element-lastknownvalue).

When invoked as a Query, each element in the response array MUST include the Value-Quality-Timestamp (VQT) structure:
- value: the actual data value
- quality: a quality indicator (e.g., "Good", "GoodNoData", "Bad")
- timestamp: a timestamp corresponding to the time and date the data was recorded in the CMIP, following the standard established by [Internet RFC 3339](https://www.rfc-editor.org/rfc/rfc3339)

#### 4.2.2 Update Methods

##### 4.2.2.1 Object Element LastKnownValue

Implementations MAY include the ability to write to the LastKnownValue. If this feature is implemented, the following considerations apply:

When invoked as an Update, the LastKnownValue interface MUST accept a new current value for the requested object to be recorded in the CMIP, by ElementId. If the CMIP supports write-back to a Control System (for example, via an interface to a PLC) additional security requirements outside the scope of this proposal MUST be considered.) 

When invoked as an Update the LastKnownValue interface MAY accept an array of current values for an array of of ElementIds.

##### 4.2.2.2 Object Element HistoricalValue

Implementations MAY include the ability to write to HistoricalValue(s). If this feature is implemented, the following considerations apply:

When invoked as an Update, the HistoricalValue interface MUST accept an updated historical value for the requested object and timestamp, by ElementId.

When invoked as an Update, the HistoricalValue interface MAY accept an array of updated historical values for an array of specified objects and timestamps, by ElementId.

When invoked in order to Create a new historical record, the HistoricalValue interface MAY accept an array of new historical values for an array of specified objects and timestamps, by ElementId.

When updating Historical data, the CMIP SHOULD implement auditing or tracking of such changes.

#### 4.2.3 Subscription Methods

The contributors to this RFC, and the broader community, have communicated clearly that the minimum requirements for a modern industrial information API must include the ability to publish data on-change to subscribing clients. The proposed implementation attempts to harmonize strengths from both MQTT and OPC/UA's REST interface, while supporting a wide variety of network scenarios.

##### 4.2.3.1 Create Subscription

Registers a client for a new Subscription. This initial handshake allows the CMIP to allocate resources for a client. The response from the SMIP MUST include a Subscription Id that may be used for follow-up calls. Implementations SHALL support two delivery modes.

###### Streaming: At Most Once

The CMIP will publish messages to subscribed clients as the data becomes available via Server-Sent Events (SSE), but provide no guarantee of message delivery.

###### Sync: Exactly Once

The server will publish messages to subscribed clients when the client indicates readiness via polling and will persist the message for re-delivery until the client acknowledges successful receipt. Only the most recent value is guaranteed to be delivered; in its initial version a CMIP provides no buffer for messages between acknowledged messages.

##### 4.2.3.2 Register Monitored Items

Registers the ElementIds the client wishes to subscribe to, for a given Subscription Id. Upon registration, the CMIP MUST begin publishing changed values. This method is additive, that is the client can add additional monitored items later.

The registration request MUST include:
- elementIds: an array of ElementIds to monitor

The registration request MAY include:
- maxDepth: controls recursion through HasComponent relationships for elements with `isComposition: true`, using the same semantics as defined in [section 4.2.1.1](#4211-object-element-lastknownvalue). Default is 1 (no recursion).

For streaming subscriptions, this method call establishes an ongoing connection between the client and CMIP. The server MUST stream changes to Subscribed items over this connection immediately until the connection is broken or the Unsubscribe method is called. Each update being streamed MUST include:
- elementId: the ElementId of the changed element
- value: the new value (with recursive structure if maxDepth was specified)
- quality: the quality indicator
- timestamp: the timestamp of the change

For sync subscriptions, the registration confirms which items will be monitored. Changed values are retrieved via the Sync method ([section 4.2.3.3](#4233-sync)).

Note: I3X explicitly permits subscribing to composition structures (an ElementId may represent a single property of an object, an entire object, or a tree of composed objects). The `maxDepth` parameter controls how deep the CMIP recurses through HasComponent relationships when publishing updates. As the required metadata for each object includes `isComposition`, a client can determine which elements have component children.

##### 4.2.3.3 Remove Monitored Items

Removes the ElementIds the client no longer wishes to have in the subscription, for a given Subscription Id.

##### 4.2.3.4 Sync

This method is used only for sync subscriptions, and is called with a specific Subscription Id, to allow the client to:
- Acknowledge receipt of previous messages
- Check for changes to subscribed elements

When servicing the Sync call, the CMIP MUST respond with an array of updates for elements that have changed since the last Sync call. Each update in the response array MUST include:
- elementId: the ElementId of the changed element
- value: the new value (with recursive structure if maxDepth was specified during registration)
- quality: the quality indicator
- timestamp: the timestamp of the change

If no elements have changed since the last Sync call, the response MUST be an empty array.

If the client does not acknowledge a previous message, the CMIP MUST re-send that message as part of the response to the Sync call. The CMIP must maintain state for all pending (un-acknowledged) messages, with the caveat that only the latest value is ever available to sync clients.

##### 4.2.3.5 Unsubscribe

When invoked, the Unsubscribe interface MUST accept a single subscription ID and MAY accept an array of subscription IDs or a wildcard, and cancels publication of future messages matching the parameter to the invoking client, allowing the CMIP to release resources and state held for the client.

## 5. Implementation Requirements

To support I3X, a CMIP must have certain capabilities. While this, and subsequent, RFCs will not define requirements for implementation specifics, some base functionality must exist. Vendors MAY differentiate on optimization, performance and scalability, to meet the requirements of the API.

The I3X API SHALL be implemented over an encrypted transport, and support the interfaces listed in this section. In order to properly support some of these interfaces, implementations MUST support the required capabilities listed in [section 3](#3-address-space-overview), and MAY support the optional capabilities listed in [section 3](#3-address-space-overview). 

### 5.1 Request and Response Structure

#### 5.1.1 Response Serialization

Implementations MUST support a default JSON serialization for all responses.

Implementations MAY support a Binary serialization for all responses, where the format of such response will be determined in a future RFC.

#### 5.1.2 Request Headers

Applications consuming the API SHOULD use the normal "accept" and "content-type" headers for indicating inbound and outbound serialization format. If omitted, the default JSON serialization should be used.

### 5.2 Type Safety

#### 5.2.1 Data Type Definitions

Underlying platforms MAY persist data values using any primitive types they wish, but MUST support return attribute values (both Live and Historical) cast or coerced to one of the primitive JavaScript primitive types to support JSON serialization (eg: a value persisted as FLOAT must be returned as NUMBER).

#### 5.2.2 Complex Type Definitions

Underlying platforms MUST derive Objects from separately declared definitions (also known as Class, Template or Schema definitions in other environments). In I3X, these definitions are generalized as Type definitions, given first-class treatment, and MUST be serializable to easy-to-consume JSON. Implementing platforms SHOULD support importing Type definitions from the [OPC UA Part 5 Information Modeling standard](https://reference.opcfoundation.org/Core/Part5/v104/docs/) (IEC62541-5). Implementing platforms MAY support importing Type definitions from the [Asset Administration Shell SubModelTemplate standard](https://www.zvei.org/fileadmin/user_upload/Presse_und_Medien/Publikationen/2020/Dezember/Submodel_Templates_of_the_Asset_Administration_Shell/201117_I40_ZVEI_SG2_Submodel_Spec_ZVEI_Technical_Data_Version_1_1.pdf). Implementing platforms MAY also support an internal Type definition and storage format.

### 5.3 Security Considerations

#### 5.3.1 Authorization

As a programmer's interface, this RFC primarily considers application authorization: implementations MUST support authorization using API keys as a minimum. Implementations MAY choose to replace API keys with JWT or OAuth. 

#### 5.3.2 Authentication

Implementations MAY require user authentication in order to refine application authorization for some or all of the data the API supports.

#### 5.3.3 Encryption

Implementations MUST require an encrypted transport for all communication in production.

### 5.4 Performance Considerations

While this API suggests that large volumes of Structural and Historical data will be accessible, the reality of many underlying data sources is that it may take multiple calls (for example, to browse an Address Space in the case of OPC/UA, or to fetch history from a separate store where a MQTT Broker is paired with a Historian) to respond to a given query. While it is the intent of this proposal to provide such abstraction -- shielding an application developer from the complexity of such architectures -- obvious performance implications exist. This proposal cannot prescribe how to solve all of these issues, but implementers MAY consider the following:

- Implementations MAY use an in-memory cache, on-disk database, or some hybrid for frequently accessed data, as long as Exploratory Interface queries can be responded to promptly.
- Implementations MAY pre-fetch data, such as pre-browsing an Address Space in a background thread.
- Implementations MAY require query limits or windows, to manage the size of requests or responses.
- Implementations MAY choose to persist state, using authentication, a session, or some token.

Implementations of this API MUST have Current Values for all persisted Object Instances, including their attribute values, readily available for querying. Implementations that are not connected directly to a manufacturing data source (eg: Cloud platforms, Historians) MUST return the most recent value received from the underlying data source.

Implementations of this API MUST be able to return Historical Value responses within a common HTTP client timeout (currently Firefox and Chrome use 300 seconds as a default.) If the complete payload cannot be returned within this time frame, a partial payload and poll-able callback URL MUST be returned.

## 6. Acknowledgements

Unless requested otherwise, contributor names and organizations from private previews of this document will be acknowledged in the public release.


