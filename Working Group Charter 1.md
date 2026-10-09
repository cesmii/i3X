# Contextualized Manufacturing API Working Group Charter

### Completion

The Working Group completed this Charter in June of 2026 with the release of 1.0. A new charter will be established for future work in late 2026.

Thank you to all who contributed!

### Duration
- Start Date: November 2024
- End Date: November 2025 (1 year)
- Chairs: Jonathan Wise (CESMII)
- Team Contact: rfc@cesmii.org
- Meeting Schedule: Video conference twice per month

## Motivation and Background
The manufacturing information ecosystem benefits from the contributions of many players, over multiple decades of technology evolution. While this diversity creates a lot of platform choice for manufacturers, it has the opposite effect on the creation of app value. Application developers must choose which platforms to build against, and therefore are forced to develop against proprietary API implementations with no hope of portability between them.

This working group is guiding the creation of a common API, consisting of a base set of server primitives that a wide array of platforms can implement to commoditize this access to data. Such a common API does not prevent platform vendors from differentiating on their capabilities, but it will encourage a proliferation of portable apps to help spur adoption of such platforms, and create a vibrant marketplace of apps bringing value to end-users. 

## Scope
- Specification for a common API that can be implemented on a wide variety of information platform architectures, including those that are standards-based, and those that are proprietary but wishing to support a layer of openness.
- Articulation of use-cases that this API is designed to support.
- Identification of potential information platform server vendors that should be capable of, and solicited for, adoption.
- Identification of potential information platform client tool vendors that should be capable of, and solicited for, adoption.
- Community engagement, evangelism and feedback gathering to inform the evolution of the API.

### Out of Scope
- Implementation of the API on all possible targets.

## Deliverables
- Sample implementation of the API as a server which includes an open API test page (via Swagger, or similar interface) and some sample data, available as open source software.
- Reference implementation of a client of the API to be used as a test, demonstration and discoverability tool, available as open source software.
- Sample code in at least two programming languages demonstrating how to consume the API.
- Sample test cases to support implementation validation.

## Planned Timeline
- Nov 2024: Kickoff and 1.0 Publication
- Dec 2025: Group Charter Publication
- Feb 2025: Articulation of use-cases that this API is designed to support
- Feb 2025: Identification of potential information platform server & client vendors
- Mar 2025: Visual documentation of API (Living document using Swagger or similar UI)
- Apr 2025: Sample implementation of the API as a server with data
- Jun 2025: Reference implementation of a client interacting with the API
- Aug 2025: Draft of Specification Document
- Oct 2025: Sample code in at least two programming languages demonstrating how to consume the API
- Oct 2025: Sample test cases to support implementation validation.
- Nov 2025: Final Specification Document

## Success Criteria
- Demonstration of sample client interacting with a sample server implementation.
- Demonstration of interoperability against the API implemented on three or more information server platforms.
- All new features should have expressions of interest from at least two potential implementors before being incorporated in the specification.

## Coordination
- The Working Group will seek community review and feedback through GitHub Issues and email sent to rfc@cesmii.org.
- The Working Group will meet regularly to triage and respond to Issues via Video Conference.
- The Working Group will make demonstration implementations, tests and sample code publicly available through GitHub.
- The Working Group will make a working public demonstration endpoint available through a Cloud endpoint.

## Participation
To be successful, this Working Group is expected to have 6 or more active participants for its duration, including representatives from the key implementors of this specification. The Working Group participants are expected to contribute a minimum of 1 hour, two times per month.

Code and test implementation will be a voluntary contribution to the Working Group's output, as time allows.

## Communication
This group primarily conducts its technical work on GitHub issues. The public is invited to review, discuss and contribute to this work.

## Decision Policy
This group will seek to make decisions through consensus and due process. Typically, an editor or other participant makes an initial proposal, which is then refined in discussion with members of the group and other reviewers, and consensus emerges with little formal voting being required.

However, if a decision is necessary for timely progress and consensus is not achieved after careful consideration of the range of views presented, the Chairs may call for a group vote and record a decision along with any objections.

To afford asynchronous decisions and organizational deliberation, any resolution (including publication decisions) taken in a face-to-face meeting or teleconference will be considered provisional. A call for consensus (CfC) will be issued for all resolutions (for example, via email, GitHub issue or web-based survey), with a response period of two weeks, depending on the chair's evaluation of the group consensus on the issue. If no objections are raised by the end of the response period, the resolution will be considered to have consensus as a resolution of the Working Group.

All decisions made by the group should be considered resolved unless and until new information becomes available or unless reopened at the discretion of the Chairs.

## Patent Policy
To promote the widest adoption of standards, this Working Group seeks to issue a specification that can be implemented on a permissive Open Source License and Royalty-Free basis. No contributor will include or claim IP rights over the output of the Working Group.

## About this Charter
The creation of this charter was informed by the [W3C Charter template](https://w3c.github.io/charter-drafts/charter-template.html), but this Working Group is not currently a part of the W3C process.
