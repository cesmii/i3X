# i3X Contextual Manufacturing API Working Group Charter 2

## Duration
- Start Date: October 2026
- End Date: January 2028 (15 months)
- Chairs: Matthew Parris (GE Appliances, a Haier Company), Aron Semle (HighByte), Jonathan Wise (CESMII)
- Team Contact: i3x@cesmii.org
- Meeting Schedule: Video Conference twice per month

## Motivation and Background
The manufacturing information ecosystem benefits from the contributions of many players, over multiple decades of technology evolution. While this diversity creates a lot of platform choice for manufacturers, it has the opposite effect on the creation of app value. Application developers must choose which platforms to build against, and therefore are forced to develop against proprietary API implementations with no hope of portability between them.

This working group is guiding the evolution of a common API, consisting of a base set of server primitives that a wide array of platforms can implement to commoditize this access to data. Such a common API does not prevent platform vendors from differentiating on their capabilities, but it will encourage a proliferation of portable apps to help spur adoption of such platforms, and create a vibrant marketplace of apps bringing value to end-users. 

## Scope
- Evolution and maintenance of the specification for a common API that can be implemented on a wide variety of information platform architectures, including those that are standards-based, and those that are proprietary but wishing to support a layer of openness.
- Draft guidance for i3X-on-OPC UA implementations, especially as it pertains to serializing a UA Information Model.
- Developer Documentation, Tools and Demos to support the understanding and adoption of the API.
- Conformance tests and tools to help adopters validate their implementation.
- Triage of feature requests, bug reports, and ideas from the broader community of adopters.
- Community engagement, evangelism and feedback gathering to inform the evolution of the API.

### Out of Scope
- Implementation of the API on all possible targets.
- Breaking changes or a 2.0 release.

## Deliverables
- A 1.0.1 Patch Release to address documentation bugs or gaps in 1.0, clarify ambiguous guidance, or sharpen implementation details. Includes updates to the Conformance Tests.
- A 1.1.0 Minor Release which will provide additive functionality with no breaking changes from 1.0. Includes updates to the Conformance Tests.
- A Draft Guide for i3X-on-OPC UA implementations, providing prescriptive information on how to best preserve the fidelity of OPC UA Namespaces and serialize an OPC UA Address Space.
- Updates to sample implementation of the API as a server which includes an open API test page (via Swagger, or similar interface) and some sample data, available as open source software.
- Updates to reference implementation of a client of the API to be used as a test, demonstration and discoverability tool, available as open source software.
- Updates to sample or SDK code in at least two programming languages demonstrating how to consume the API.
- Updates to sample test cases to support demo validation.
- Updates to Conformance Test Suite to validate implementations online and within a private network.

## Planned Timeline
- October 2026: General Kick-off, establish Charter 2
- November 2026: OPC UA Work Stream kick-off
- January 2027: 1.0.1 Patch Release
- July 2027: 1.1.0 Minor Release Preview
- August 2027: OPC UA Guide Draft #1
- September 2027: 1.1.0 Minor Release Final
- October 2027: OPC UA Guide Draft #2
- November 2027: Tooling, SDK, Conformance Test updates complete
- December 2027: Triage and ideation for Next Release
- January 2028: Charter Complete

## Success Criteria
- Demonstration of sample client interacting with updated sample server implementation.
- Demonstration of interoperability against the updated API implemented on three or more information server platforms.
- All new features should have expressions of interest from at least two potential implementors before being incorporated in the specification.

## Coordination
- The Working Group will seek community review and feedback through GitHub Issues and email sent to i3x@cesmii.org.
- The Working Group will meet regularly to triage and respond to Issues via Video Conference.
- The Working Group will make demonstration implementations, tests and sample code publicly available through GitHub.
- The Working Group will make a working public demonstration endpoint available through a web endpoint on the i3x.dev domain.
- The Working Group will make Conformance Test tools publicly available through a web endpoint on the i3x.dev domain, and downloadable for on-prem testing.

## Participation
To be successful, this Working Group is expected to have 6 or more active participants for its duration, including representatives from the key implementors of this specification. The Working Group participants are expected to contribute a minimum of 1 hour, two times per month. Meetings must be led by at least one Chairperson.

Documentation, code and test implementation will be a voluntary contribution to the Working Group's output, as time allows.

## Communication
This group primarily conducts its technical work on GitHub Issues. The public is invited to review, discuss and contribute to this work.

## Decision Policy
Typically, a member of the public or working group participant makes an initial proposal through GitHub Issues, which is then refined in discussion with members of the group during regular meetings, and consensus emerges with little formal voting being required.

The group will seek to make decisions through such consensus where possible; however, when consensus is not easily arrived at, final decisions may be made by the three Chairpersons. In the event that one Chairperson has to resign, decisions may be made by the remaining two Chairpersons. In the event that two Chairpersons have to resign, the Working Group will pause until at least one replacement Chair is nominated and accepts. 

To afford asynchronous decisions and organizational deliberation, any resolution taken in a face-to-face meeting or teleconference may be considered provisional, depending on the Chairs' evaluation of the group consensus on the issue. In the case of ongoing contention, a call for consensus (CfC) will be issued (for example, via email, GitHub Issue or web-based survey), with a response period of two weeks, unless all Chairpersons are present and in unanimity. If no clear consensus can be reached by the end of the response period, the resolution will be adjudicated by the Chairpersons outside of a meeting, with a publicly recorded decision.

All decisions made should be considered resolved unless and until new information becomes available or unless reopened at the discretion of the Chairs. Consensus or Chairperson ruling should be recorded in the comments of the GitHub Issue or Pull Request where the issue was tracked or originated.

## Patent Policy
To promote the widest adoption of standards, this Working Group seeks to issue a specification that can be implemented on a permissive Open Source License and Royalty-Free basis. No contributor will include or claim IP rights over the output of the Working Group.

## About this Charter
The creation of this charter was informed by the [W3C Charter template](https://w3c.github.io/charter-drafts/charter-template.html), but this Working Group is not currently a part of the W3C process.