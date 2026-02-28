# i3X - Industrial Information Interoperability eXchange

## Status of This Effort

i3X is in a _pre-release_ Alpha state. While the API signature is largely stable, expect significant changes to response structures, and minor changes to method calls over the first quarter of 2026 while we stabilize a 1.0 release. If you want to help, please see [Contributing.md](#Contributing.md)

## What is i3X?

i3X is a Common API for Contextual Manufacturing Information Platforms. It aims to provide a common interface for a wide array of composable back-end data sources with a unified namespace.

<a href="https://i3x.dev/viz"><img src="https://i3x.dev/images/i3XHero.png?1"><br>Click to View Interactive Explainer</a>

## Who is CESMII?

CESMII is the United States' institute for Smart Manufacturing. We are a not-for-profit consortia of manufacturing ecosystem members focused on improving access to clean, contextual information to help manufacturers make better decisions. 

Learn more about CESMII at [cesmii.org](https://www.cesmii.org)

## Where to Learn More

This repo is focused on the development of a specification for the API, including issues, PRs and tasks for the Working Group. This effort is open and collaborative, all are welcome to read and participate -- but this is not the best place to learn the high level details.

For general information about i3X, please visit [https://www.i3x.dev](https://www.i3x.dev)

For implementation information for Client and Server developers, please visit [https://www.i3x.dev/docs](https://www.i3x.dev/docs)

## Problem Statement
The manufacturing information ecosystem benefits from the contributions of many players, over multiple decades of technology evolution. While this diversity creates a lot of platform choice for manufacturers, it has the opposite effect on the creation of app value. Application developers must choose which platforms to build against, and therefore are forced to develop against proprietary, or open but competing, API implementations with no hope of portability between them. Apps create information value by consuming and producing the data available in a platform, and rendering it in ways that are helpful to end users -- analytics, visualization, notification, machine learning... all of these need contextualized data, and all end up abstracted by an underlying platform (be it an Historian, MES, MOM, EMI, or broker or server).

## Proposed Solution
This initial proposal recommends the [creation of a common API](https://github.com/cesmii/API/blob/main/RFC%20for%20Contextualized%20Manufacturing%20Information%20API.md), consisting of a base set of server primitives that a wide array of platforms can implement to commoditize this access to data. Such a common API does not prevent platform vendors from differentiating on their capabilities, but it will encourage a proliferation of portable apps to help spur adoption of such platforms, and enable a vibrant marketplace of apps bringing value to end-users. The analogies in other industries should be obvious: Apple and Android users benefit from common APIs for access to device and platform capabilities exposed to app developers that have led to App Stores full of creative, useful, and enjoyable app experiences. Those platform vendors have benefited, but more importantly, the user has benefited.

## Trying it Out
A public endpoint for the in-progress Demo implementation is available at [https://api.i3x.dev/v0//](https://api.i3x.dev/v0//) with a Swagger page at [https://api.i3x.dev/v0//docs](https://api.i3x.dev/v0//docs).

<img src="https://www.acetechnologies.net/i3X/screenshots/subscriptions.png" height=200 style="height:200px">

If you prefer a GUI, [ACE Technologies](https://www.acetechnologies.net) has provided a cross-platform [i3X Explorer](https://www.acetechnologies.net/i3x) client you can use to explore both the i3X functions and the Demo namespace.

The Demo data includes an exploration of the complex relationships supported by i3X. [Review the demo readme](demo/README.md) for an explanation of how these relationships work.

## Call to Action
The authors of this specification seek your feedback on how to move toward common interfaces for common industrial information functionality. In this public stage, this document is offered RFC-style, not as a prescription, but as an invitation: [review the RFC](https://github.com/cesmii/API/blob/main/RFC%20for%20Contextualized%20Manufacturing%20Information%20API.md), and consider participating in the [prototype implementation](https://github.com/cesmii/API/tree/prototypes). The tasks for that effort will be [tracked publically here](https://github.com/orgs/cesmii/projects/1). If you wish to contribute, please review the [Contributing.md guidelines](Contributing.md).

If you are unable to contribute code, but want to help identify issues or future enhancements, the preferred feedback mechanism is to use [GitHub issues](https://github.com/cesmii/API/issues), where input can be tracked, discussed, and categorized as an improvement or a feature request. If you desire to provide feedback, but cannot use GitHub issues, please email us: rfc@cesmii.org

## Background
This proposal has been created by industry participants with experience developing or using manufacturing information platforms such as those provided by Rockwell Automation, OSI Pi, ThinkIQ, Inductive Automation, ThingWorx and HighByte, are deep users and often contributors to the ecosystems around OPC UA, Asset Administration Shell, MQTT and Sparkplug/B, and have more than 50 years of combined experience in designing, developing, implementing and using manufacturing information software. 

## API Usage
The block diagram below shows where the i3X API is most applicable, namely within the realm of software applications running on top of operating systems on PCs or servers. Information being accessed through the API are assumed to have already been processed by contexualization functions to make it ready for consumption by other applications.
![API Block Diagram](images/api-block-diagram.PNG)

## API tech stack within the Data Access Model
The image below shows the tech stack for a general Web Browser compared to the i3X API, from the perspective of the Data Access Model.  Refer to the article ["How all protocols fail at data access interoperabilty"](https://iebmedia.com/technology/iiot/how-all-protocols-fail-at-data-access-interoperability/) for more information regarding The Data Access Model.
![API Data Access Model](images/data-access-model.PNG)
