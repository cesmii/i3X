# Demo Implementation

This Demo implementation attempts to illustrate the functionality of i3X as specified in the [Implementation Guide](../spec/IMPLEMENTATION_GUIDE.md), but it should not be considered prescriptive.

As an API definition, i3X can be implemented by any number of platforms, in any number of programming languages. While this Demo explores one set of patterns for an implementation, it cannot illustrate all possible approaches.

Some key characteristics of this Demo:

- The server implementation has sample data source providers used to illustrate that i3X can be driven by a wide array of underlying data sources
- The server implementation supports connecting different data sources for each of the types of interfaces in the API
- The server implementation information model is file-based -- most real-world implementations will draw their Namespace and Type definitions, as well as their live and historical data from existing platforms
- The server implementation illustrates each of the styles of Relationships that i3X supports. Read the [Understanding Relationships](../spec/UNDERSTANDING_RELATIONSHIPS.md) document to learn more

This Demo is for illustrative purposes and is not suitable for production use.