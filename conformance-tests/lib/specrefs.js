'use strict';

// Pointers into the normative i3X 1.0 documents. Every test cites one of
// these so a failing implementer can jump straight to the relevant section.

const GUIDE = 'https://github.com/cesmii/i3X/blob/1.0/spec/IMPLEMENTATION_GUIDE.md';
const RELATIONSHIPS = 'https://github.com/cesmii/i3X/blob/1.0/spec/UNDERSTANDING_RELATIONSHIPS.md';
const OPENAPI = 'https://api.i3x.dev/v1/openapi.json';
const SDK_DOCS = 'https://www.i3x.dev/sdk/category/server-developers';

const REFS = {
  compliance: { title: 'Implementation Guide § Compliance', url: `${GUIDE}#compliance` },
  transport: { title: 'Implementation Guide § Transport & Encoding', url: `${GUIDE}#transport--encoding` },
  security: { title: 'Implementation Guide § Security & Authentication', url: `${GUIDE}#security--authentication` },
  versioning: { title: 'Implementation Guide § Versioning', url: `${GUIDE}#versioning` },
  responseFormat: { title: 'Implementation Guide § Response Format', url: `${GUIDE}#response-format` },
  failure: { title: 'Implementation Guide § Response Format — Failure', url: `${GUIDE}#failure` },
  bulkResponse: { title: 'Implementation Guide § Response Format — Bulk Response', url: `${GUIDE}#bulk-response` },
  elementId: { title: 'Implementation Guide § ElementId and DisplayName', url: `${GUIDE}#elementid-and-displayname` },
  namespaces: { title: 'Implementation Guide § Namespaces', url: `${GUIDE}#namespaces` },
  objectTypes: { title: 'Implementation Guide § Object Types', url: `${GUIDE}#object-types` },
  relationshipTypes: { title: 'Implementation Guide § Relationship Types', url: `${GUIDE}#relationship-types` },
  relationshipSemantics: { title: 'Implementation Guide § Relationship Semantics', url: `${GUIDE}#relationship-semantics` },
  objects: { title: 'Implementation Guide § Objects', url: `${GUIDE}#objects` },
  serverCapabilities: { title: 'Implementation Guide § Server Capabilities Endpoints (GET /info)', url: `${GUIDE}#server-capabilities-endpoints` },
  namespaceEndpoints: { title: 'Implementation Guide § Namespace Endpoints', url: `${GUIDE}#namespace-endpoints` },
  objectTypeEndpoints: { title: 'Implementation Guide § Object Type Endpoints', url: `${GUIDE}#object-type-endpoints` },
  relationshipTypeEndpoints: { title: 'Implementation Guide § Relationship Type Endpoints', url: `${GUIDE}#relationship-type-endpoints` },
  objectEndpoints: { title: 'Implementation Guide § Object Endpoints', url: `${GUIDE}#object-endpoints` },
  queryMethods: { title: 'Implementation Guide § Query Methods', url: `${GUIDE}#query-methods` },
  maxDepth: { title: 'Implementation Guide § maxDepth Parameter Semantics', url: `${GUIDE}#maxdepth-parameter-semantics` },
  nullValues: { title: 'Implementation Guide § Null Value Handling', url: `${GUIDE}#null-value-handling` },
  updateMethods: { title: 'Implementation Guide § Update Methods', url: `${GUIDE}#update-methods` },
  subscribeMethods: { title: 'Implementation Guide § Subscribe Methods', url: `${GUIDE}#subscribe-methods` },
  subscriptions: { title: 'Implementation Guide § Subscriptions', url: `${GUIDE}#subscriptions` },
  registering: { title: 'Implementation Guide § Registering and Unregistering Objects', url: `${GUIDE}#registering-and-unregistering-objects` },
  streaming: { title: 'Implementation Guide § Streaming', url: `${GUIDE}#streaming` },
  sync: { title: 'Implementation Guide § Sync', url: `${GUIDE}#sync` },
  syncDataLoss: { title: 'Implementation Guide § Sync Data Loss', url: `${GUIDE}#sync-data-loss` },
  lifecycle: { title: 'Implementation Guide § Subscription Life Cycle', url: `${GUIDE}#subscription-life-cycle` },
  relationships: { title: 'Understanding i3X Relationships', url: RELATIONSHIPS },
  openapi: { title: 'i3X 1.0 OpenAPI definition', url: OPENAPI }
};

module.exports = { REFS, GUIDE, RELATIONSHIPS, OPENAPI, SDK_DOCS };
