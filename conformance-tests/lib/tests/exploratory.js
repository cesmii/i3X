'use strict';

const { pass, fail, warn, skip, httpProblem, okJson } = require('../results');
const V = require('../validators');

const BOGUS_ID = 'i3x-test-suite-nonexistent-element-7f3a9c';

function firstProblems(problems, n = 5) {
  return problems.slice(0, n).join('; ') + (problems.length > n ? ` (+${problems.length - n} more)` : '');
}

module.exports = [
  // ---------------------------------------------------------------- namespaces
  {
    id: 'EXP-01',
    name: 'GET /namespaces returns a success envelope with valid Namespace records',
    level: 'MUST',
    ref: 'namespaceEndpoints',
    async run(ctx) {
      const res = await ctx.client.request('GET', '/namespaces');
      if (!okJson(res)) return fail(httpProblem(res, 'GET /namespaces'));
      const env = V.successEnvelopeProblems(res.json);
      if (env.length) return fail(`GET /namespaces: ${firstProblems(env)}`);
      if (!Array.isArray(res.json.result)) return fail('GET /namespaces: "result" must be an array of Namespace objects');
      const problems = [];
      res.json.result.forEach((ns, i) => problems.push(...V.validateShape('Namespace', ns, `$.result[${i}]`)));
      if (problems.length) return fail(`Namespace records are malformed: ${firstProblems(problems)} — each namespace needs "uri" and "displayName".`);
      ctx.namespaces = res.json.result;
      return pass(`${res.json.result.length} namespace(s)`);
    }
  },
  {
    id: 'EXP-02',
    name: 'Server exposes at least one Namespace',
    level: 'MUST',
    ref: 'namespaces',
    async run(ctx) {
      if (!ctx.namespaces) return skip('GET /namespaces did not succeed', 'blocked');
      if (ctx.namespaces.length === 0) return fail('No namespaces returned. The spec requires: "A server MUST have at least one Namespace".');
      return pass();
    }
  },
  {
    id: 'EXP-03',
    name: 'Namespace URIs are unique',
    level: 'MUST',
    ref: 'namespaces',
    async run(ctx) {
      if (!ctx.namespaces) return skip('GET /namespaces did not succeed', 'blocked');
      const seen = new Set();
      const dups = ctx.namespaces.filter((ns) => (seen.has(ns.uri) ? true : (seen.add(ns.uri), false)));
      if (dups.length) return fail(`Duplicate namespace URI(s): ${dups.map((d) => d.uri).join(', ')} — "Each Namespace MUST have a unique URI".`);
      return pass();
    }
  },

  // --------------------------------------------------------------- object types
  {
    id: 'EXP-04',
    name: 'GET /objecttypes returns valid ObjectTypeResponse records with JSON Schema definitions',
    level: 'MUST',
    ref: 'objectTypeEndpoints',
    async run(ctx) {
      const res = await ctx.client.request('GET', '/objecttypes');
      if (!okJson(res)) return fail(httpProblem(res, 'GET /objecttypes'));
      const env = V.successEnvelopeProblems(res.json);
      if (env.length) return fail(`GET /objecttypes: ${firstProblems(env)}`);
      if (!Array.isArray(res.json.result)) return fail('GET /objecttypes: "result" must be an array');
      const problems = [];
      res.json.result.forEach((t, i) => problems.push(...V.validateShape('ObjectTypeResponse', t, `$.result[${i}]`)));
      if (problems.length) {
        return fail(
          `ObjectType records are malformed: ${firstProblems(problems)}. Each type requires elementId, displayName, namespaceUri, sourceTypeId, and a JSON Schema under "schema".`
        );
      }
      ctx.objectTypes = res.json.result;
      ctx.typesById = new Map(res.json.result.map((t) => [t.elementId, t]));
      if (res.json.result.length === 0) return warn('Server declares zero Object Types — every Object must reference a type.');
      return pass(`${res.json.result.length} type(s)`);
    }
  },
  {
    id: 'EXP-05',
    name: 'Every Object Type belongs to a declared Namespace',
    level: 'MUST',
    ref: 'objectTypes',
    async run(ctx) {
      if (!ctx.objectTypes || !ctx.namespaces) return skip('Types or namespaces unavailable', 'blocked');
      const uris = new Set(ctx.namespaces.map((n) => n.uri));
      const orphans = ctx.objectTypes.filter((t) => !uris.has(t.namespaceUri));
      if (orphans.length) {
        return fail(
          `${orphans.length} Object Type(s) reference a namespaceUri not present in GET /namespaces (e.g. "${orphans[0].elementId}" → "${orphans[0].namespaceUri}"). "Each ObjectType ... MUST belong to one and only one Namespace".`
        );
      }
      return pass();
    }
  },
  {
    id: 'EXP-06',
    name: 'GET /objecttypes?namespaceUri= filters by namespace',
    level: 'MUST',
    ref: 'objectTypeEndpoints',
    async run(ctx) {
      if (!ctx.objectTypes || !ctx.objectTypes.length) return skip('No object types available', 'blocked');
      const uri = ctx.objectTypes[0].namespaceUri;
      const res = await ctx.client.request('GET', '/objecttypes', { query: { namespaceUri: uri } });
      if (!okJson(res)) return fail(httpProblem(res, 'GET /objecttypes?namespaceUri='));
      const list = res.json.result;
      if (!Array.isArray(list)) return fail('Filtered response "result" must be an array');
      const wrong = list.filter((t) => t.namespaceUri !== uri);
      if (wrong.length) return fail(`Filter returned ${wrong.length} type(s) from other namespaces (e.g. "${wrong[0].elementId}").`);
      const expected = ctx.objectTypes.filter((t) => t.namespaceUri === uri).length;
      if (list.length !== expected) return fail(`Filter for "${uri}" returned ${list.length} type(s), expected ${expected} based on the unfiltered listing.`);
      return pass();
    }
  },
  {
    id: 'EXP-07',
    name: 'POST /objecttypes/query returns a bulk response in request order',
    level: 'MUST',
    ref: 'bulkResponse',
    async run(ctx) {
      if (!ctx.objectTypes || !ctx.objectTypes.length) return skip('No object types available', 'blocked');
      const ids = ctx.objectTypes.slice(0, 3).map((t) => t.elementId).reverse();
      const res = await ctx.client.request('POST', '/objecttypes/query', { body: { elementIds: ids } });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /objecttypes/query'));
      const problems = V.bulkEnvelopeProblems(res.json, { requestedIds: ids, itemShape: 'ObjectTypeResponse' });
      if (problems.length) return fail(firstProblems(problems));
      return pass();
    }
  },
  {
    id: 'EXP-08',
    name: 'POST /objecttypes/query reports unknown elementIds as per-item 404 failures',
    level: 'MUST',
    ref: 'bulkResponse',
    async run(ctx) {
      if (!ctx.objectTypes || !ctx.objectTypes.length) return skip('No object types available', 'blocked');
      const ids = [ctx.objectTypes[0].elementId, BOGUS_ID];
      const res = await ctx.client.request('POST', '/objecttypes/query', { body: { elementIds: ids } });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /objecttypes/query'));
      const problems = V.bulkEnvelopeProblems(res.json, { requestedIds: ids });
      if (problems.length) return fail(firstProblems(problems));
      const bad = res.json.results[1];
      if (bad.success !== false) return fail(`Unknown elementId "${BOGUS_ID}" was reported as success — it must fail per-item with a 404 responseDetail.`);
      if (bad.responseDetail && bad.responseDetail.status !== 404) {
        return fail(`Unknown elementId failure carries status ${bad.responseDetail.status}, expected 404 ("ElementId or resource doesn't exist").`);
      }
      return pass();
    }
  },

  // --------------------------------------------------------- relationship types
  {
    id: 'EXP-09',
    name: 'GET /relationshiptypes returns valid RelationshipType records',
    level: 'MUST',
    ref: 'relationshipTypeEndpoints',
    async run(ctx) {
      const res = await ctx.client.request('GET', '/relationshiptypes');
      if (!okJson(res)) return fail(httpProblem(res, 'GET /relationshiptypes'));
      const env = V.successEnvelopeProblems(res.json);
      if (env.length) return fail(`GET /relationshiptypes: ${firstProblems(env)}`);
      if (!Array.isArray(res.json.result)) return fail('"result" must be an array of RelationshipType objects');
      const problems = [];
      res.json.result.forEach((r, i) => problems.push(...V.validateShape('RelationshipType', r, `$.result[${i}]`)));
      if (problems.length) {
        return fail(
          `RelationshipType records are malformed: ${firstProblems(problems)}. Each requires elementId, displayName, namespaceUri, relationshipId and reverseOf.`
        );
      }
      ctx.relationshipTypes = res.json.result;
      ctx.relById = new Map(res.json.result.map((r) => [r.elementId, r]));
      return pass(`${res.json.result.length} relationship type(s)`);
    }
  },
  {
    id: 'EXP-10',
    name: 'Every Relationship Type has a registered, symmetric reverseOf',
    level: 'MUST',
    ref: 'relationshipTypes',
    async run(ctx) {
      if (!ctx.relationshipTypes) return skip('GET /relationshiptypes did not succeed', 'blocked');
      const problems = [];
      for (const r of ctx.relationshipTypes) {
        const rev = ctx.relById.get(r.reverseOf);
        if (!rev) {
          problems.push(`"${r.elementId}" declares reverseOf "${r.reverseOf}" which is not registered in /relationshiptypes`);
        } else if (rev.reverseOf !== r.elementId) {
          problems.push(`"${r.elementId}" ↔ "${rev.elementId}" are not symmetric (reverseOf chain does not return to the origin)`);
        }
      }
      if (problems.length) {
        return fail(`${firstProblems(problems)}. "Every Relationship Type MUST define a reverseOf that is also registered in the address space".`);
      }
      return pass();
    }
  },
  {
    id: 'EXP-11',
    name: 'POST /relationshiptypes/query returns a bulk response and per-item 404s for unknown ids',
    level: 'MUST',
    ref: 'relationshipTypeEndpoints',
    async run(ctx) {
      if (!ctx.relationshipTypes || !ctx.relationshipTypes.length) return skip('No relationship types available', 'blocked');
      const ids = [ctx.relationshipTypes[0].elementId, BOGUS_ID];
      const res = await ctx.client.request('POST', '/relationshiptypes/query', { body: { elementIds: ids } });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /relationshiptypes/query'));
      const problems = V.bulkEnvelopeProblems(res.json, { requestedIds: ids, itemShape: 'RelationshipType' });
      if (problems.length) return fail(firstProblems(problems));
      if (res.json.results[1].success !== false) return fail('Unknown relationship type elementId must fail per-item with a 404 responseDetail.');
      return pass();
    }
  },

  // -------------------------------------------------------------------- objects
  {
    id: 'EXP-12',
    name: 'GET /objects returns valid ObjectInstanceResponse records',
    level: 'MUST',
    ref: 'objectEndpoints',
    async run(ctx) {
      const res = await ctx.client.request('GET', '/objects');
      if (!okJson(res)) return fail(httpProblem(res, 'GET /objects'));
      const env = V.successEnvelopeProblems(res.json);
      if (env.length) return fail(`GET /objects: ${firstProblems(env)}`);
      if (!Array.isArray(res.json.result)) return fail('"result" must be an array of Object instances');
      const problems = [];
      res.json.result.forEach((o, i) => problems.push(...V.validateShape('ObjectInstanceResponse', o, `$.result[${i}]`)));
      if (problems.length) {
        return fail(
          `Object records are malformed: ${firstProblems(problems)}. Each Object requires elementId, displayName, typeElementId and isComposition.`
        );
      }
      ctx.objects = res.json.result;
      ctx.objectsById = new Map(res.json.result.map((o) => [o.elementId, o]));
      if (!res.json.result.length) return warn('Server has no Objects — most query/subscribe tests will be skipped.');
      return pass(`${res.json.result.length} object(s)`);
    }
  },
  {
    id: 'EXP-13',
    name: "Every Object's typeElementId resolves to a registered Object Type",
    level: 'MUST',
    ref: 'objects',
    async run(ctx) {
      if (!ctx.objects || !ctx.typesById) return skip('Objects or types unavailable', 'blocked');
      const orphans = ctx.objects.filter((o) => !ctx.typesById.has(o.typeElementId));
      if (orphans.length) {
        return fail(
          `${orphans.length} Object(s) reference a typeElementId not present in GET /objecttypes (e.g. "${orphans[0].elementId}" → "${orphans[0].typeElementId}"). Register the type, or use an UnknownType placeholder so every typeElementId resolves.`
        );
      }
      return pass();
    }
  },
  {
    id: 'EXP-14',
    name: 'ElementIds are well-formed and unique across the address space',
    level: 'MUST',
    ref: 'elementId',
    async run(ctx) {
      const all = [
        ...(ctx.objects || []).map((o) => o.elementId),
        ...(ctx.objectTypes || []).map((t) => t.elementId),
        ...(ctx.relationshipTypes || []).map((r) => r.elementId)
      ];
      if (!all.length) return skip('Nothing discovered to check', 'blocked');
      const problems = [];
      const seen = new Set();
      for (const id of all) {
        for (const p of V.elementIdProblems(id)) problems.push(`"${id}" ${p}`);
        if (seen.has(id)) problems.push(`"${id}" is not unique within the platform`);
        seen.add(id);
      }
      if (problems.length) return fail(`${firstProblems(problems)}. ElementIds MUST be unique strings without surrounding whitespace or non-printable characters.`);
      return pass(`${all.length} elementIds checked`);
    }
  },
  {
    id: 'EXP-15',
    name: 'GET /objects?root=true returns at least one root Object',
    level: 'MUST',
    ref: 'objects',
    async run(ctx) {
      const res = await ctx.client.request('GET', '/objects', { query: { root: 'true' } });
      if (!okJson(res)) return fail(httpProblem(res, 'GET /objects?root=true'));
      const roots = res.json.result;
      if (!Array.isArray(roots) || roots.length === 0) {
        return fail(
          'No root Objects returned. "The Server MUST have at least one root Object which is queried using the /objects?root=true endpoint" — clients rely on this to begin browsing.'
        );
      }
      ctx.rootObjects = roots;
      const withParent = roots.filter((o) => typeof o.parentId === 'string' && o.parentId !== '' && o.parentId !== '/');
      if (withParent.length) {
        return warn(`${withParent.length} root Object(s) carry a non-null parentId (e.g. "${withParent[0].elementId}" → "${withParent[0].parentId}"); roots should have parentId null.`);
      }
      return pass(`${roots.length} root object(s)`);
    }
  },
  {
    id: 'EXP-16',
    name: 'GET /objects?typeElementId= filters by type',
    level: 'MUST',
    ref: 'objectEndpoints',
    async run(ctx) {
      if (!ctx.objects || !ctx.objects.length) return skip('No objects available', 'blocked');
      const typeId = ctx.objects[0].typeElementId;
      const res = await ctx.client.request('GET', '/objects', { query: { typeElementId: typeId } });
      if (!okJson(res)) return fail(httpProblem(res, 'GET /objects?typeElementId='));
      const list = res.json.result;
      if (!Array.isArray(list)) return fail('Filtered response "result" must be an array');
      const wrong = list.filter((o) => o.typeElementId !== typeId);
      if (wrong.length) return fail(`Filter returned ${wrong.length} object(s) of other types (e.g. "${wrong[0].elementId}" of type "${wrong[0].typeElementId}").`);
      if (!list.length) return fail(`Filter for type "${typeId}" returned no objects, but at least one object of that type exists.`);
      return pass();
    }
  },
  {
    id: 'EXP-17',
    name: 'GET /objects?includeMetadata=true returns metadata with type provenance',
    level: 'MUST',
    ref: 'objectEndpoints',
    async run(ctx) {
      if (!ctx.objects || !ctx.objects.length) return skip('No objects available', 'blocked');
      const res = await ctx.client.request('GET', '/objects', { query: { includeMetadata: 'true' } });
      if (!okJson(res)) return fail(httpProblem(res, 'GET /objects?includeMetadata=true'));
      const list = res.json.result || [];
      const withMeta = list.filter((o) => o.metadata && typeof o.metadata === 'object');
      if (!withMeta.length) return fail('includeMetadata=true returned no "metadata" objects — the metadata key must be included when requested.');
      const missing = withMeta.filter((o) => typeof o.metadata.typeNamespaceUri !== 'string' || typeof o.metadata.sourceTypeId !== 'string');
      if (missing.length) {
        return fail(
          `${missing.length} object(s) have metadata without required "typeNamespaceUri"/"sourceTypeId" (e.g. "${missing[0].elementId}"). These provenance fields are required whenever metadata is returned.`
        );
      }
      // Stash for the relationship checks
      ctx.objectsWithMetadata = list;
      return pass();
    }
  },
  {
    id: 'EXP-18',
    name: 'POST /objects/list returns a bulk response in request order with per-item 404s',
    level: 'MUST',
    ref: 'objectEndpoints',
    async run(ctx) {
      if (!ctx.objects || !ctx.objects.length) return skip('No objects available', 'blocked');
      const ids = [...ctx.objects.slice(0, 2).map((o) => o.elementId), BOGUS_ID];
      const res = await ctx.client.request('POST', '/objects/list', { body: { elementIds: ids } });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /objects/list'));
      const problems = V.bulkEnvelopeProblems(res.json, { requestedIds: ids, itemShape: 'ObjectInstanceResponse' });
      if (problems.length) return fail(firstProblems(problems));
      const bad = res.json.results[ids.length - 1];
      if (bad.success !== false) return fail(`Unknown elementId "${BOGUS_ID}" must fail per-item with a 404 responseDetail (got success=true).`);
      if (bad.responseDetail && bad.responseDetail.status !== 404) return fail(`Unknown elementId failure carries status ${bad.responseDetail.status}, expected 404.`);
      return pass();
    }
  },

  // ------------------------------------------------------------- relationships
  {
    id: 'EXP-19',
    name: 'POST /objects/related returns RelatedObjectResult entries with registered relationship types',
    level: 'MUST',
    ref: 'objectEndpoints',
    async run(ctx) {
      if (!ctx.objects || !ctx.objects.length) return skip('No objects available', 'blocked');
      const ids = ctx.objects.slice(0, Math.min(10, ctx.objects.length)).map((o) => o.elementId);
      const res = await ctx.client.request('POST', '/objects/related', { body: { elementIds: ids } });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /objects/related'));
      const problems = V.bulkEnvelopeProblems(res.json, { requestedIds: ids });
      if (problems.length) return fail(firstProblems(problems));
      const edges = [];
      const shapeProblems = [];
      res.json.results.forEach((item, i) => {
        if (item.success && Array.isArray(item.result)) {
          item.result.forEach((edge, j) => {
            shapeProblems.push(...V.validateShape('RelatedObjectResult', edge, `$.results[${i}].result[${j}]`));
            edges.push({ from: item.elementId, rel: edge.sourceRelationship, to: edge.object && edge.object.elementId });
          });
        }
      });
      if (shapeProblems.length) return fail(`Related-object entries are malformed: ${firstProblems(shapeProblems)} — each entry needs "sourceRelationship" and a full "object" record.`);
      if (ctx.relById) {
        const unregistered = edges.filter((e) => e.rel && !ctx.relById.has(e.rel));
        if (unregistered.length) {
          return fail(
            `${unregistered.length} edge(s) use a sourceRelationship not registered in /relationshiptypes (e.g. "${unregistered[0].rel}"). "Servers MUST ensure that all relationship types used ... are registered in /relationshiptypes".`
          );
        }
      }
      ctx.relatedEdges = edges;
      return pass(`${edges.length} edge(s) discovered`);
    }
  },
  {
    id: 'EXP-20',
    name: 'Relationships are traversable in both directions (bidirectional storage)',
    level: 'MUST',
    ref: 'relationshipSemantics',
    async run(ctx) {
      if (!ctx.relatedEdges || !ctx.relatedEdges.length) return skip('No relationship edges discovered to verify', 'untestable');
      if (!ctx.relById) return skip('Relationship types unavailable', 'blocked');
      const sample = ctx.relatedEdges.filter((e) => e.to && e.rel && ctx.relById.has(e.rel)).slice(0, 5);
      if (!sample.length) return skip('No usable edges to verify', 'untestable');
      const failures = [];
      for (const edge of sample) {
        const reverse = ctx.relById.get(edge.rel).reverseOf;
        const res = await ctx.client.request('POST', '/objects/related', { body: { elementIds: [edge.to] } });
        if (!okJson(res) || !res.json.results || !res.json.results[0] || !Array.isArray(res.json.results[0].result)) {
          failures.push(`could not query related objects for "${edge.to}"`);
          continue;
        }
        const found = res.json.results[0].result.some((e2) => e2.object && e2.object.elementId === edge.from && e2.sourceRelationship === reverse);
        if (!found) {
          failures.push(`"${edge.from}" —${edge.rel}→ "${edge.to}" exists, but "${edge.to}" has no "${reverse}" edge back to "${edge.from}"`);
        }
      }
      if (failures.length) {
        return fail(
          `${firstProblems(failures, 3)}. "All relationships MUST be stored bidirectionally" so clients can discover the graph from any node.`
        );
      }
      return pass(`${sample.length} edge(s) verified in both directions`);
    }
  },
  {
    id: 'EXP-21',
    name: 'Hierarchy is reachable through /objects/related (parentId matches a HasParent-style edge)',
    level: 'MUST',
    ref: 'relationshipSemantics',
    async run(ctx) {
      if (!ctx.objects) return skip('Objects unavailable', 'blocked');
      const child = ctx.objects.find((o) => typeof o.parentId === 'string' && o.parentId && o.parentId !== '/' && (ctx.objectsById ? ctx.objectsById.has(o.parentId) : true));
      if (!child) return skip('No object with a resolvable parentId found', 'untestable');
      const res = await ctx.client.request('POST', '/objects/related', { body: { elementIds: [child.elementId] } });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /objects/related'));
      const item = res.json.results && res.json.results[0];
      const edges = item && Array.isArray(item.result) ? item.result : [];
      const toParent = edges.some((e) => e.object && e.object.elementId === child.parentId);
      if (!toParent) {
        return fail(
          `Object "${child.elementId}" has parentId "${child.parentId}" but POST /objects/related returns no edge to that parent. Hierarchical relationships MUST be included in /objects/related (synthesized if necessary) — relying on parentId alone leaves objects unreachable by graph traversal.`
        );
      }
      return pass();
    }
  },
  {
    id: 'EXP-22',
    name: 'POST /objects/related honors the relationshipType filter',
    level: 'MUST',
    ref: 'objectEndpoints',
    async run(ctx) {
      if (!ctx.relatedEdges || !ctx.relatedEdges.length) return skip('No relationship edges discovered', 'untestable');
      const edge = ctx.relatedEdges.find((e) => e.rel && e.to);
      if (!edge) return skip('No usable edge for filter test', 'untestable');
      const res = await ctx.client.request('POST', '/objects/related', {
        body: { elementIds: [edge.from], relationshipType: edge.rel }
      });
      if (!okJson(res)) return fail(httpProblem(res, 'POST /objects/related (filtered)'));
      const item = res.json.results && res.json.results[0];
      const edges = item && Array.isArray(item.result) ? item.result : [];
      const wrong = edges.filter((e) => e.sourceRelationship !== edge.rel);
      if (wrong.length) return fail(`Filter for relationshipType "${edge.rel}" returned ${wrong.length} edge(s) of other types (e.g. "${wrong[0].sourceRelationship}").`);
      if (!edges.length) return fail(`Filter for relationshipType "${edge.rel}" on "${edge.from}" returned no edges, but at least one such edge exists.`);
      return pass();
    }
  }
];
