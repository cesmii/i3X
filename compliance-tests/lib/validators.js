'use strict';

// Structural validation helpers. The shape registry below mirrors the
// components/schemas section of the normative OpenAPI document
// (https://api.i3x.dev/v1/openapi.json) so validation failures can cite the
// exact component an implementation diverges from.

const QUALITIES = ['Good', 'GoodNoData', 'Bad', 'Uncertain'];

// RFC 3339, UTC only — the guide requires "UTC with no timezone offset".
const UTC_TS_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/;

function isUtcTimestamp(s) {
  return typeof s === 'string' && UTC_TS_RE.test(s) && !Number.isNaN(Date.parse(s));
}

function elementIdProblems(id) {
  const problems = [];
  if (typeof id !== 'string' || id.length === 0) {
    problems.push('must be a non-empty string');
    return problems;
  }
  if (id !== id.trim()) problems.push('has leading or trailing whitespace');
  // eslint-disable-next-line no-control-regex
  if (/[\x00-\x1f\x7f]/.test(id)) problems.push('contains non-printable characters');
  return problems;
}

function typeOf(v) {
  if (v === null) return 'null';
  if (Array.isArray(v)) return 'array';
  return typeof v; // string | number | boolean | object | undefined
}

/**
 * Minimal JSON Schema validator covering the subset used by the i3X OpenAPI
 * components and by typical ObjectType schemas: type (incl. unions),
 * properties, required, items, enum, const, allOf/anyOf/oneOf,
 * additionalProperties (schema form), $ref into a local registry.
 * Unknown keywords are ignored (lenient by design — we only fail on
 * violations we can be sure about).
 *
 * Returns an array of error strings ("$.path: message").
 */
function validateSchema(schema, data, opts = {}) {
  const errors = [];
  const registry = opts.registry || {};
  const maxErrors = opts.maxErrors || 20;

  function resolve(s, depth) {
    if (s && s.$ref && depth < 16) {
      const name = String(s.$ref).split('/').pop();
      if (registry[name]) return resolve(registry[name], depth + 1);
      return null; // unresolvable ref — skip validation of this branch
    }
    return s;
  }

  function check(s, value, path, depth) {
    if (errors.length >= maxErrors || depth > 32) return;
    s = resolve(s, 0);
    if (!s || typeof s !== 'object') return;

    if (s.allOf) for (const sub of s.allOf) check(sub, value, path, depth + 1);

    if (s.anyOf || s.oneOf) {
      const subs = s.anyOf || s.oneOf;
      const matched = subs.some((sub) => {
        const trial = validateSchema(sub, value, { registry, maxErrors: 1 });
        return trial.length === 0;
      });
      if (!matched) {
        const types = subs.map((sub) => (resolve(sub, 0) || {}).type || 'object').flat();
        errors.push(`${path}: expected one of [${types.join(', ')}], got ${typeOf(value)}`);
      }
      return;
    }

    if (s.enum && !s.enum.some((e) => JSON.stringify(e) === JSON.stringify(value))) {
      errors.push(`${path}: value ${JSON.stringify(value)} is not one of ${JSON.stringify(s.enum)}`);
      return;
    }
    if ('const' in s && JSON.stringify(s.const) !== JSON.stringify(value)) {
      errors.push(`${path}: expected constant ${JSON.stringify(s.const)}, got ${JSON.stringify(value)}`);
      return;
    }

    if (s.type) {
      const allowed = Array.isArray(s.type) ? s.type : [s.type];
      const actual = typeOf(value);
      const ok = allowed.some((t) => {
        if (t === 'integer') return typeof value === 'number' && Number.isInteger(value);
        if (t === 'number') return typeof value === 'number';
        return t === actual;
      });
      if (!ok) {
        errors.push(`${path}: expected ${allowed.join('|')}, got ${actual}${actual === 'string' || actual === 'number' || actual === 'boolean' ? ` (${JSON.stringify(value)})` : ''}`);
        return;
      }
    }

    if (typeOf(value) === 'object') {
      if (s.required) {
        for (const key of s.required) {
          if (!(key in value)) errors.push(`${path}: missing required field "${key}"`);
        }
      }
      if (s.properties) {
        for (const [key, sub] of Object.entries(s.properties)) {
          if (key in value) check(sub, value[key], `${path}.${key}`, depth + 1);
        }
      }
      if (s.additionalProperties && typeof s.additionalProperties === 'object') {
        const declared = new Set(Object.keys(s.properties || {}));
        for (const [key, v] of Object.entries(value)) {
          if (!declared.has(key)) check(s.additionalProperties, v, `${path}.${key}`, depth + 1);
        }
      }
    }

    if (typeOf(value) === 'array' && s.items) {
      value.forEach((item, i) => check(s.items, item, `${path}[${i}]`, depth + 1));
    }
  }

  check(schema, data, opts.path || '$', 0);
  return errors;
}

// ---------------------------------------------------------------------------
// Shape registry mirroring the OpenAPI components (normative response shapes)
// ---------------------------------------------------------------------------

const nullable = (t) => ({ type: [t, 'null'] });

const SHAPES = {
  Namespace: {
    type: 'object',
    required: ['uri', 'displayName'],
    properties: { uri: { type: 'string' }, displayName: { type: 'string' } }
  },
  ObjectTypeResponse: {
    type: 'object',
    required: ['elementId', 'displayName', 'namespaceUri', 'sourceTypeId', 'schema'],
    properties: {
      elementId: { type: 'string' },
      displayName: { type: 'string' },
      namespaceUri: { type: 'string' },
      sourceTypeId: { type: 'string' },
      version: nullable('string'),
      schema: { type: 'object' },
      related: { type: ['object', 'null'] }
    }
  },
  RelationshipType: {
    type: 'object',
    required: ['elementId', 'displayName', 'namespaceUri', 'relationshipId', 'reverseOf'],
    properties: {
      elementId: { type: 'string' },
      displayName: { type: 'string' },
      namespaceUri: { type: 'string' },
      relationshipId: { type: 'string' },
      reverseOf: { type: 'string' }
    }
  },
  ObjectInstanceResponse: {
    type: 'object',
    required: ['elementId', 'displayName', 'typeElementId', 'isComposition'],
    properties: {
      elementId: { type: 'string' },
      displayName: { type: 'string' },
      typeElementId: { type: 'string' },
      parentId: nullable('string'),
      isComposition: { type: 'boolean' },
      isExtended: { type: 'boolean' },
      metadata: { $ref: '#/ObjectInstanceMetadata' }
    }
  },
  ObjectInstanceMetadata: {
    type: ['object', 'null'],
    properties: {
      typeNamespaceUri: nullable('string'),
      sourceTypeId: nullable('string'),
      description: nullable('string'),
      relationships: { type: ['object', 'null'] },
      schemaExtensions: { type: ['object', 'null'] },
      system: { type: ['object', 'null'] }
    }
  },
  VQT: {
    type: 'object',
    required: ['value', 'quality', 'timestamp'],
    properties: { quality: { type: 'string' }, timestamp: { type: 'string' } }
  },
  CurrentValueResult: {
    type: 'object',
    required: ['isComposition', 'value', 'quality', 'timestamp'],
    properties: {
      isComposition: { type: 'boolean' },
      quality: { type: 'string' },
      timestamp: { type: 'string' },
      components: { type: ['object', 'null'], additionalProperties: { $ref: '#/VQT' } }
    }
  },
  HistoricalValueResult: {
    type: 'object',
    required: ['isComposition', 'values'],
    properties: {
      isComposition: { type: 'boolean' },
      values: { type: 'array', items: { $ref: '#/VQT' } }
    }
  },
  SyncUpdateEntry: {
    type: 'object',
    required: ['elementId', 'value', 'quality', 'timestamp'],
    properties: {
      elementId: { type: 'string' },
      quality: { type: 'string' },
      timestamp: { type: 'string' }
    }
  },
  SyncBatch: {
    type: 'object',
    required: ['sequenceNumber', 'updates'],
    properties: {
      sequenceNumber: { type: 'integer' },
      updates: { type: 'array', items: { $ref: '#/SyncUpdateEntry' } }
    }
  },
  ErrorDetail: {
    type: 'object',
    required: ['title', 'status', 'detail'],
    properties: {
      title: { type: 'string' },
      status: { type: 'number' },
      detail: { type: 'string' }
    }
  },
  CreateSubscriptionResponse: {
    type: 'object',
    required: ['subscriptionId'],
    properties: {
      subscriptionId: { type: 'string' },
      clientId: nullable('string'),
      displayName: nullable('string')
    }
  },
  SubscriptionDetail: {
    type: 'object',
    required: ['subscriptionId', 'monitoredObjects'],
    properties: {
      subscriptionId: { type: 'string' },
      displayName: nullable('string'),
      monitoredObjects: { type: 'array', items: { type: 'object' } }
    }
  },
  RelatedObjectResult: {
    type: 'object',
    required: ['sourceRelationship', 'object'],
    properties: {
      sourceRelationship: { type: 'string' },
      object: { $ref: '#/ObjectInstanceResponse' }
    }
  },
  ServerInfo: {
    type: 'object',
    required: ['specVersion', 'capabilities'],
    properties: {
      specVersion: { type: 'string' },
      serverVersion: nullable('string'),
      serverName: nullable('string'),
      capabilities: {
        type: 'object',
        required: ['query', 'update', 'subscribe'],
        properties: {
          query: { type: 'object', required: ['history'], properties: { history: { type: 'boolean' } } },
          update: {
            type: 'object',
            required: ['current', 'history'],
            properties: { current: { type: 'boolean' }, history: { type: 'boolean' } }
          },
          subscribe: { type: 'object', required: ['stream'], properties: { stream: { type: 'boolean' } } }
        }
      }
    }
  }
};

function validateShape(shapeName, data, path = '$') {
  return validateSchema({ $ref: `#/${shapeName}` }, data, { registry: SHAPES, path });
}

// ---------------------------------------------------------------------------
// Envelope checks (Implementation Guide § Response Format)
// ---------------------------------------------------------------------------

/** {success: true, result: <data>} */
function successEnvelopeProblems(body) {
  const problems = [];
  if (typeOf(body) !== 'object') return [`response body is ${typeOf(body)}, expected a JSON object`];
  if (body.success !== true) problems.push(`"success" must be true on a successful response (got ${JSON.stringify(body.success)})`);
  if (!('result' in body)) problems.push('missing required "result" field');
  return problems;
}

/** {success: false, responseDetail: {title, status, detail}} */
function errorEnvelopeProblems(body, expectedStatus) {
  const problems = [];
  if (typeOf(body) !== 'object') return [`error body is ${typeOf(body)}, expected a JSON object`];
  if (body.success !== false) problems.push(`"success" must be false on an error response (got ${JSON.stringify(body.success)})`);
  if (!body.responseDetail) {
    problems.push('missing required "responseDetail" field (RFC 9457 problem details)');
  } else {
    problems.push(...validateShape('ErrorDetail', body.responseDetail, '$.responseDetail'));
    if (expectedStatus && body.responseDetail.status !== expectedStatus) {
      problems.push(`responseDetail.status is ${body.responseDetail.status}, expected ${expectedStatus}`);
    }
  }
  return problems;
}

/**
 * Bulk response: {success, results: [{success, elementId|subscriptionId, result|responseDetail}]}.
 * requestedIds, when given, enforces same-order/same-size.
 */
function bulkEnvelopeProblems(body, { requestedIds, keyField = 'elementId', itemShape } = {}) {
  const problems = [];
  if (typeOf(body) !== 'object') return [`response body is ${typeOf(body)}, expected a JSON object`];
  if (typeof body.success !== 'boolean') problems.push('top-level "success" must be a boolean');
  if (!Array.isArray(body.results)) {
    problems.push('missing or non-array "results" field — bulk endpoints must return {success, results: [...]}');
    return problems;
  }
  if (requestedIds) {
    if (body.results.length !== requestedIds.length) {
      problems.push(`results has ${body.results.length} entries but ${requestedIds.length} ids were requested — bulk responses MUST be the same size and order as the request`);
    } else {
      requestedIds.forEach((id, i) => {
        if (body.results[i] && body.results[i][keyField] !== id) {
          problems.push(`results[${i}].${keyField} is ${JSON.stringify(body.results[i][keyField])}, expected ${JSON.stringify(id)} — bulk responses MUST preserve request order`);
        }
      });
    }
  }
  body.results.forEach((item, i) => {
    if (typeOf(item) !== 'object') {
      problems.push(`results[${i}] is ${typeOf(item)}, expected an object`);
      return;
    }
    if (typeof item.success !== 'boolean') problems.push(`results[${i}].success must be a boolean`);
    if (item.success === false) {
      if (!item.responseDetail) {
        problems.push(`results[${i}] failed but has no responseDetail — failed bulk items MUST carry {title, status, detail}`);
      } else {
        problems.push(...validateShape('ErrorDetail', item.responseDetail, `$.results[${i}].responseDetail`));
      }
    } else if (item.success === true && itemShape && item.result !== null && item.result !== undefined) {
      problems.push(...validateShape(itemShape, item.result, `$.results[${i}].result`));
    }
  });
  const anyFailed = body.results.some((r) => r && r.success === false);
  if (anyFailed && body.success !== false) {
    problems.push('top-level "success" must be false when any bulk item failed');
  }
  if (!anyFailed && body.success !== true && body.results.length > 0) {
    problems.push('top-level "success" should be true when every bulk item succeeded');
  }
  return problems.slice(0, 25);
}

/**
 * VQT semantic rules (§ Query Methods, § Null Value Handling):
 * quality enum, UTC timestamp, null-value/quality pairing.
 */
function vqtProblems(vqt, path = 'value') {
  const problems = [];
  if (typeOf(vqt) !== 'object') return [`${path}: expected a VQT object, got ${typeOf(vqt)}`];
  if (!QUALITIES.includes(vqt.quality)) {
    problems.push(`${path}.quality is ${JSON.stringify(vqt.quality)} — must be one of Good, GoodNoData, Bad, Uncertain`);
  }
  if (!isUtcTimestamp(vqt.timestamp)) {
    problems.push(`${path}.timestamp is ${JSON.stringify(vqt.timestamp)} — must be RFC 3339 UTC with no timezone offset (e.g. "2025-01-08T10:30:00Z")`);
  }
  if (vqt.value === null && (vqt.quality === 'Good' || vqt.quality === 'Uncertain')) {
    problems.push(`${path}: value is null but quality is "${vqt.quality}" — a null value MUST carry quality "Bad" or "GoodNoData"`);
  }
  if (vqt.value !== null && vqt.value !== undefined && (vqt.quality === 'Bad' || vqt.quality === 'GoodNoData')) {
    // Spec defines Bad/GoodNoData as "Value is null" — treat non-null as a violation.
    problems.push(`${path}: quality "${vqt.quality}" implies a null value, but value is ${JSON.stringify(vqt.value)?.slice(0, 80)}`);
  }
  return problems;
}

module.exports = {
  QUALITIES,
  isUtcTimestamp,
  elementIdProblems,
  typeOf,
  validateSchema,
  validateShape,
  SHAPES,
  successEnvelopeProblems,
  errorEnvelopeProblems,
  bulkEnvelopeProblems,
  vqtProblems
};
