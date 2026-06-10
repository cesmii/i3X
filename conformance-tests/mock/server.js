'use strict';

// Compliant i3X 1.0 reference mock server.
//
// Serves the demo "pump station" model from the spec's relationship guide so
// implementers can see what a Full 1.0 Compliance result looks like, and so
// the test suite itself can be verified end to end.
//
// Env switches (for exercising the suite's failure reporting):
//   MOCK_TOKEN=secret          require "Authorization: Bearer secret" (except /info)
//   MOCK_BREAK=a,b,c           introduce deliberate spec violations:
//     reverseof     - drop a relationship type's reverse registration
//     nullgood      - report a null value with quality "Good"
//     nogzip        - ignore Accept-Encoding: gzip
//     badbulk       - return bulk results in reverse order
//     omit-updates  - declare update capabilities false (verdict: 1.0 Compatible)
//     primitive     - strip properties from object schemas (verdict: Immature Type System)
//     noclearall    - ignore lastSequenceNumber=-1 instead of clearing the queue
//     nosinglestream - leave an existing SSE stream open when a new one is opened
//     noscope       - accept subscription requests without clientId and skip ownership checks

const http = require('node:http');
const zlib = require('node:zlib');
const crypto = require('node:crypto');

const BREAK = new Set(String(process.env.MOCK_BREAK || '').split(',').map((s) => s.trim()).filter(Boolean));
const TOKEN = process.env.MOCK_TOKEN || null;

const nowIso = () => new Date().toISOString().replace(/\.\d+Z$/, 'Z');
const isoAgo = (ms) => new Date(Date.now() - ms).toISOString().replace(/\.\d+Z$/, 'Z');

// ---------------------------------------------------------------------- model

const NAMESPACES = [
  { uri: 'https://isa.org/isa95', displayName: 'ISA-95' },
  { uri: 'https://abelara.com/equipment', displayName: 'Abelara Equipment' },
  { uri: 'urn:i3x:relationships', displayName: 'i3X Relationships' }
];

function schemaFor(raw) {
  if (BREAK.has('primitive') && raw.type === 'object') return { type: 'object' };
  return raw;
}

const OBJECT_TYPES = [
  {
    elementId: 'work-center-type', displayName: 'Work Center', namespaceUri: 'https://isa.org/isa95',
    sourceTypeId: 'WorkCenter', version: '1.0.0',
    schema: { type: 'object', properties: { status: { type: 'string' } }, required: ['status'] }
  },
  {
    elementId: 'work-unit-type', displayName: 'Work Unit', namespaceUri: 'https://isa.org/isa95',
    sourceTypeId: 'WorkUnit', version: '1.0.0',
    schema: { type: 'object', properties: { level: { type: 'number' }, capacity: { type: 'number' } }, required: ['level'] }
  },
  {
    elementId: 'pump-type', displayName: 'Pump', namespaceUri: 'https://abelara.com/equipment',
    sourceTypeId: 'Pump', version: '1.2.0',
    schema: {
      type: 'object',
      properties: {
        status: { type: 'string', enum: ['running', 'stopped', 'fault'] },
        flowRate: { type: 'number' },
        outletTemp: { type: ['number', 'null'] }
      },
      required: ['status', 'flowRate']
    }
  },
  {
    elementId: 'sensor-type', displayName: 'Temperature Sensor', namespaceUri: 'https://abelara.com/equipment',
    sourceTypeId: 'TemperatureSensor', version: '1.0.0',
    schema: {
      type: 'object',
      properties: { temperature: { type: 'number' }, unit: { type: 'string', enum: ['C', 'F', 'K'] } },
      required: ['temperature', 'unit']
    }
  },
  {
    elementId: 'measurements-type', displayName: 'Measurements Group', namespaceUri: 'https://abelara.com/equipment',
    sourceTypeId: 'Measurements', version: '1.0.0',
    schema: { type: 'object', properties: { description: { type: 'string' } } }
  },
  {
    elementId: 'temperature-reading-type', displayName: 'Temperature Reading', namespaceUri: 'https://abelara.com/equipment',
    sourceTypeId: 'TemperatureReading', version: '1.0.0',
    schema: { type: 'number' }
  },
  {
    elementId: 'state-type', displayName: 'Equipment State', namespaceUri: 'https://abelara.com/equipment',
    sourceTypeId: 'EquipmentState', version: '1.0.0',
    schema: { type: 'string' }
  }
];

const RELATIONSHIP_TYPES = [
  ['HasParent', 'HasChildren'], ['HasChildren', 'HasParent'],
  ['HasComponent', 'ComponentOf'], ['ComponentOf', 'HasComponent'],
  ['Monitors', 'MonitoredBy'], ['MonitoredBy', 'Monitors'],
  ['SuppliesTo', 'SuppliedBy'], ['SuppliedBy', 'SuppliesTo']
].map(([id, rev]) => ({
  elementId: id, displayName: id, namespaceUri: 'urn:i3x:relationships', relationshipId: id, reverseOf: rev
})).filter((r) => !(BREAK.has('reverseof') && r.elementId === 'SuppliedBy'));

const OBJECTS = [
  {
    elementId: 'pump-station', displayName: 'Pump Station', typeElementId: 'work-center-type',
    parentId: null, isComposition: false, isExtended: false,
    description: 'Root work center organizing the demo pump loop.',
    relationships: { HasChildren: ['pump-101', 'tank-201', 'sensor-001'] }
  },
  {
    elementId: 'pump-101', displayName: 'Pump 101', typeElementId: 'pump-type',
    parentId: 'pump-station', isComposition: true, isExtended: false,
    description: 'Primary transfer pump.',
    relationships: {
      HasParent: ['pump-station'],
      HasComponent: ['pump-101-measurements', 'pump-101-state'],
      SuppliesTo: ['tank-201']
    }
  },
  {
    elementId: 'tank-201', displayName: 'Tank 201', typeElementId: 'work-unit-type',
    parentId: 'pump-station', isComposition: false, isExtended: false,
    description: 'Receiving tank.',
    relationships: { HasParent: ['pump-station'], SuppliedBy: ['pump-101'], MonitoredBy: ['sensor-001'] }
  },
  {
    elementId: 'sensor-001', displayName: 'TempSensor 101', typeElementId: 'sensor-type',
    parentId: 'pump-station', isComposition: false, isExtended: false,
    description: 'Ambient temperature sensor watching tank-201.',
    relationships: { HasParent: ['pump-station'], Monitors: ['tank-201'] }
  },
  {
    elementId: 'pump-101-measurements', displayName: 'Pump 101 Measurements', typeElementId: 'measurements-type',
    parentId: 'pump-101', isComposition: true, isExtended: false,
    description: 'Composition group encapsulating pump measurement points.',
    relationships: { ComponentOf: ['pump-101'], HasComponent: ['pump-101-bearing-temperature'] }
  },
  {
    elementId: 'pump-101-bearing-temperature', displayName: 'Bearing Temperature', typeElementId: 'temperature-reading-type',
    parentId: 'pump-101-measurements', isComposition: false, isExtended: false,
    description: 'Leaf measurement point (°C).',
    relationships: { ComponentOf: ['pump-101-measurements'] }
  },
  {
    elementId: 'pump-101-state', displayName: 'Pump 101 State', typeElementId: 'state-type',
    parentId: 'pump-101', isComposition: false, isExtended: false,
    description: 'Run state of pump-101.',
    relationships: { ComponentOf: ['pump-101'] }
  }
];

const typesById = new Map(OBJECT_TYPES.map((t) => [t.elementId, t]));
const relById = new Map(RELATIONSHIP_TYPES.map((r) => [r.elementId, r]));
const objectsById = new Map(OBJECTS.map((o) => [o.elementId, o]));

// current values
const VALUES = new Map([
  ['pump-station', { value: { status: 'running' }, quality: 'Good', timestamp: nowIso() }],
  ['pump-101', { value: { status: 'running', flowRate: 12.5, outletTemp: 44.2 }, quality: 'Good', timestamp: nowIso() }],
  ['tank-201', { value: { level: 0.62, capacity: 5000 }, quality: 'Good', timestamp: nowIso() }],
  ['sensor-001', { value: { temperature: 21.4, unit: 'C' }, quality: 'Good', timestamp: nowIso() }],
  ['pump-101-measurements', { value: null, quality: 'GoodNoData', timestamp: nowIso() }],
  ['pump-101-bearing-temperature', { value: 70.34, quality: 'Good', timestamp: nowIso() }],
  ['pump-101-state', { value: 'running', quality: 'Good', timestamp: nowIso() }]
]);
if (BREAK.has('nullgood')) VALUES.set('pump-101-state', { value: null, quality: 'Good', timestamp: nowIso() });

// seeded history: three hourly points per element
const HISTORY = new Map();
for (const [id, vqt] of VALUES) {
  HISTORY.set(
    id,
    [3, 2, 1].map((h) => ({ value: vqt.value, quality: vqt.quality, timestamp: isoAgo(h * 3600 * 1000) }))
  );
}

// subscriptions
const SUBSCRIPTIONS = new Map(); // id -> {clientId, displayName, monitored: Map, batches: [], nextSeq, streamRes}

// ------------------------------------------------------------------ plumbing

function send(req, res, status, obj) {
  const body = Buffer.from(JSON.stringify(obj));
  const wantsGzip = String(req.headers['accept-encoding'] || '').includes('gzip') && !BREAK.has('nogzip');
  const headers = { 'Content-Type': 'application/json' };
  let payload = body;
  if (wantsGzip) {
    payload = zlib.gzipSync(body);
    headers['Content-Encoding'] = 'gzip';
  }
  headers['Content-Length'] = payload.length;
  res.writeHead(status, headers);
  res.end(payload);
}

function sendError(req, res, status, title, detail) {
  send(req, res, status, { success: false, responseDetail: { title, status, detail } });
}

function readJson(req) {
  return new Promise((resolve) => {
    const chunks = [];
    req.on('data', (c) => chunks.push(c));
    req.on('end', () => {
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}'));
      } catch {
        resolve(null);
      }
    });
  });
}

function maybeReverse(arr) {
  return BREAK.has('badbulk') ? [...arr].reverse() : arr;
}

function bulk(items) {
  const results = maybeReverse(items);
  return { success: results.every((r) => r.success), results };
}

function objectResponse(o, includeMetadata) {
  const base = {
    elementId: o.elementId,
    displayName: o.displayName,
    typeElementId: o.typeElementId,
    parentId: o.parentId,
    isComposition: o.isComposition,
    isExtended: o.isExtended
  };
  if (includeMetadata) {
    const type = typesById.get(o.typeElementId);
    base.metadata = {
      description: o.description,
      typeNamespaceUri: type ? type.namespaceUri : 'urn:i3x:unknown',
      sourceTypeId: type ? type.sourceTypeId : 'UnknownType',
      relationships: o.relationships
    };
  }
  return base;
}

function typeResponse(t) {
  return { ...t, schema: schemaFor(t.schema) };
}

function componentIds(id, depthBudget) {
  // Flat map of all HasComponent descendants reachable within the budget.
  const out = [];
  const walk = (elementId, remaining) => {
    if (remaining === 0) return;
    const obj = objectsById.get(elementId);
    const children = (obj && obj.relationships && obj.relationships.HasComponent) || [];
    for (const child of children) {
      out.push(child);
      walk(child, remaining < 0 ? remaining : remaining - 1);
    }
  };
  walk(id, depthBudget);
  return out;
}

function stageBatch(sub) {
  if (!sub.monitored.size) return;
  const updates = [];
  for (const elementId of sub.monitored.keys()) {
    const vqt = VALUES.get(elementId);
    if (vqt) updates.push({ elementId, value: vqt.value, quality: vqt.quality, timestamp: vqt.timestamp });
  }
  if (updates.length) sub.batches.push({ sequenceNumber: sub.nextSeq++, updates });
}

// Strict client scoping: clientId is required on every subscription endpoint,
// and a subscription owned by another client behaves exactly like a
// nonexistent one (404). MOCK_BREAK=noscope reverts to lenient behavior.
function clientIdMissing(body) {
  return !BREAK.has('noscope') && !(body && typeof body.clientId === 'string' && body.clientId);
}

function ownedSub(body, id) {
  const sub = SUBSCRIPTIONS.get(id);
  if (!sub) return null;
  if (BREAK.has('noscope')) return sub;
  return sub.clientId === body.clientId ? sub : null;
}

// ------------------------------------------------------------------- handlers

const routes = {
  'GET /info': (req, res) => {
    send(req, res, 200, {
      success: true,
      result: {
        specVersion: '1.0',
        serverVersion: '1.0.0',
        serverName: 'i3X Test Suite Reference Mock',
        capabilities: {
          query: { history: true },
          update: BREAK.has('omit-updates') ? { current: false, history: false } : { current: true, history: true },
          subscribe: { stream: true }
        }
      }
    });
  },

  'GET /namespaces': (req, res) => send(req, res, 200, { success: true, result: NAMESPACES }),

  'GET /objecttypes': (req, res, url) => {
    const ns = url.searchParams.get('namespaceUri');
    const list = OBJECT_TYPES.filter((t) => !ns || t.namespaceUri === ns).map(typeResponse);
    send(req, res, 200, { success: true, result: list });
  },

  'POST /objecttypes/query': async (req, res) => {
    const body = await readJson(req);
    if (!body || !Array.isArray(body.elementIds)) return sendError(req, res, 400, 'Bad Request', 'elementIds array is required');
    send(req, res, 200, bulk(body.elementIds.map((id) => {
      const t = typesById.get(id);
      return t
        ? { success: true, elementId: id, result: typeResponse(t) }
        : { success: false, elementId: id, responseDetail: { title: 'Not Found', status: 404, detail: `Object type not found: ${id}` } };
    })));
  },

  'GET /relationshiptypes': (req, res, url) => {
    const ns = url.searchParams.get('namespaceUri');
    send(req, res, 200, { success: true, result: RELATIONSHIP_TYPES.filter((t) => !ns || t.namespaceUri === ns) });
  },

  'POST /relationshiptypes/query': async (req, res) => {
    const body = await readJson(req);
    if (!body || !Array.isArray(body.elementIds)) return sendError(req, res, 400, 'Bad Request', 'elementIds array is required');
    send(req, res, 200, bulk(body.elementIds.map((id) => {
      const t = relById.get(id);
      return t
        ? { success: true, elementId: id, result: t }
        : { success: false, elementId: id, responseDetail: { title: 'Not Found', status: 404, detail: `Relationship type not found: ${id}` } };
    })));
  },

  'GET /objects': (req, res, url) => {
    const typeId = url.searchParams.get('typeElementId');
    const root = url.searchParams.get('root');
    const includeMetadata = url.searchParams.get('includeMetadata') === 'true';
    let list = OBJECTS;
    if (typeId) list = list.filter((o) => o.typeElementId === typeId);
    if (root === 'true') list = list.filter((o) => o.parentId === null);
    send(req, res, 200, { success: true, result: list.map((o) => objectResponse(o, includeMetadata)) });
  },

  'POST /objects/list': async (req, res) => {
    const body = await readJson(req);
    if (!body || !Array.isArray(body.elementIds)) return sendError(req, res, 400, 'Bad Request', 'elementIds array is required');
    send(req, res, 200, bulk(body.elementIds.map((id) => {
      const o = objectsById.get(id);
      return o
        ? { success: true, elementId: id, result: objectResponse(o, body.includeMetadata === true) }
        : { success: false, elementId: id, responseDetail: { title: 'Not Found', status: 404, detail: `Element not found: ${id}` } };
    })));
  },

  'POST /objects/related': async (req, res) => {
    const body = await readJson(req);
    if (!body || !Array.isArray(body.elementIds)) return sendError(req, res, 400, 'Bad Request', 'elementIds array is required');
    send(req, res, 200, bulk(body.elementIds.map((id) => {
      const o = objectsById.get(id);
      if (!o) return { success: false, elementId: id, responseDetail: { title: 'Not Found', status: 404, detail: `Element not found: ${id}` } };
      const edges = [];
      for (const [relType, targets] of Object.entries(o.relationships || {})) {
        if (body.relationshipType && relType !== body.relationshipType) continue;
        for (const target of targets) {
          const t = objectsById.get(target);
          if (t) edges.push({ sourceRelationship: relType, object: objectResponse(t, body.includeMetadata === true) });
        }
      }
      return { success: true, elementId: id, result: edges };
    })));
  },

  'POST /objects/value': async (req, res) => {
    const body = await readJson(req);
    if (!body || !Array.isArray(body.elementIds)) return sendError(req, res, 400, 'Bad Request', 'elementIds array is required');
    const maxDepth = body.maxDepth === undefined ? 1 : body.maxDepth;
    send(req, res, 200, bulk(body.elementIds.map((id) => {
      const o = objectsById.get(id);
      const vqt = VALUES.get(id);
      if (!o || !vqt) return { success: false, elementId: id, responseDetail: { title: 'Not Found', status: 404, detail: `Element not found: ${id}` } };
      const result = { isComposition: o.isComposition, value: vqt.value, quality: vqt.quality, timestamp: vqt.timestamp };
      if (o.isComposition && maxDepth !== 1) {
        const budget = maxDepth === 0 ? -1 : maxDepth - 1;
        const components = {};
        for (const childId of componentIds(id, budget)) {
          const cv = VALUES.get(childId);
          if (cv) components[childId] = { value: cv.value, quality: cv.quality, timestamp: cv.timestamp };
        }
        result.components = components;
      }
      return { success: true, elementId: id, result };
    })));
  },

  'PUT /objects/value': async (req, res) => {
    if (BREAK.has('omit-updates')) return sendError(req, res, 501, 'Not Implemented', 'This server does not support current value updates');
    const body = await readJson(req);
    if (!body || !Array.isArray(body.updates)) return sendError(req, res, 400, 'Bad Request', 'updates array is required');
    send(req, res, 200, bulk(body.updates.map((u) => {
      const o = objectsById.get(u.elementId);
      if (!o) return { success: false, elementId: u.elementId, responseDetail: { title: 'Not Found', status: 404, detail: `Element not found: ${u.elementId}` } };
      if (!u.value || !('value' in u.value)) {
        return { success: false, elementId: u.elementId, responseDetail: { title: 'Bad Request', status: 400, detail: 'updates[].value.value is required' } };
      }
      const vqt = { value: u.value.value, quality: u.value.quality || 'Good', timestamp: u.value.timestamp || nowIso() };
      VALUES.set(u.elementId, vqt);
      HISTORY.get(u.elementId)?.push({ ...vqt });
      return { success: true, elementId: u.elementId, result: null };
    })));
  },

  'POST /objects/history': async (req, res) => {
    const body = await readJson(req);
    if (!body || !Array.isArray(body.elementIds)) return sendError(req, res, 400, 'Bad Request', 'elementIds array is required');
    const start = body.startTime ? Date.parse(body.startTime) : -Infinity;
    const end = body.endTime ? Date.parse(body.endTime) : Infinity;
    send(req, res, 200, bulk(body.elementIds.map((id) => {
      const o = objectsById.get(id);
      if (!o) return { success: false, elementId: id, responseDetail: { title: 'Not Found', status: 404, detail: `Element not found: ${id}` } };
      const values = (HISTORY.get(id) || []).filter((v) => {
        const t = Date.parse(v.timestamp);
        return t >= start && t <= end;
      });
      return { success: true, elementId: id, result: { isComposition: o.isComposition, values } };
    })));
  },

  'PUT /objects/history': async (req, res) => {
    if (BREAK.has('omit-updates')) return sendError(req, res, 501, 'Not Implemented', 'This server does not support historical updates');
    const body = await readJson(req);
    if (!body || !Array.isArray(body.updates)) return sendError(req, res, 400, 'Bad Request', 'updates array is required');
    send(req, res, 200, bulk(body.updates.map((u) => {
      const o = objectsById.get(u.elementId);
      if (!o) return { success: false, elementId: u.elementId, responseDetail: { title: 'Not Found', status: 404, detail: `Element not found: ${u.elementId}` } };
      const v = u.value || {};
      if (!('value' in v) || !v.timestamp) {
        return { success: false, elementId: u.elementId, responseDetail: { title: 'Bad Request', status: 400, detail: 'value and timestamp are required for historical writes' } };
      }
      const hist = HISTORY.get(u.elementId) || [];
      const replaced = hist.findIndex((h) => h.timestamp === v.timestamp);
      const rec = { value: v.value, quality: v.quality || 'Good', timestamp: v.timestamp };
      if (replaced >= 0) hist[replaced] = rec;
      else hist.push(rec);
      hist.sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp));
      HISTORY.set(u.elementId, hist);
      return { success: true, elementId: u.elementId, result: null };
    })));
  },

  'POST /subscriptions': async (req, res) => {
    const body = await readJson(req);
    if (clientIdMissing(body)) return sendError(req, res, 400, 'Bad Request', 'clientId is required');
    const subscriptionId = crypto.randomBytes(24).toString('base64url');
    SUBSCRIPTIONS.set(subscriptionId, {
      subscriptionId,
      clientId: (body && body.clientId) || null,
      displayName: (body && body.displayName) || null,
      monitored: new Map(),
      batches: [],
      nextSeq: 1,
      streamRes: null
    });
    send(req, res, 200, {
      success: true,
      result: { clientId: (body && body.clientId) || null, subscriptionId, displayName: (body && body.displayName) || null }
    });
  },

  'POST /subscriptions/list': async (req, res) => {
    const body = await readJson(req);
    if (clientIdMissing(body)) return sendError(req, res, 400, 'Bad Request', 'clientId is required');
    if (!body || !Array.isArray(body.subscriptionIds)) return sendError(req, res, 400, 'Bad Request', 'subscriptionIds array is required');
    send(req, res, 200, bulk(body.subscriptionIds.map((id) => {
      const sub = ownedSub(body, id);
      if (!sub) {
        return { success: false, subscriptionId: id, responseDetail: { title: 'Not Found', status: 404, detail: `Subscription not found: ${id}` } };
      }
      return {
        success: true,
        subscriptionId: id,
        result: {
          subscriptionId: id,
          displayName: sub.displayName,
          monitoredObjects: [...sub.monitored.entries()].map(([elementId, cfg]) => ({ elementId, maxDepth: cfg.maxDepth }))
        }
      };
    })));
  },

  'POST /subscriptions/delete': async (req, res) => {
    const body = await readJson(req);
    if (clientIdMissing(body)) return sendError(req, res, 400, 'Bad Request', 'clientId is required');
    if (!body || !Array.isArray(body.subscriptionIds)) return sendError(req, res, 400, 'Bad Request', 'subscriptionIds array is required');
    send(req, res, 200, bulk(body.subscriptionIds.map((id) => {
      const sub = ownedSub(body, id);
      if (!sub) {
        return { success: false, subscriptionId: id, responseDetail: { title: 'Not Found', status: 404, detail: `Subscription not found: ${id}` } };
      }
      if (sub.streamRes) {
        try { sub.streamRes.end(); } catch { /* already closed */ }
      }
      SUBSCRIPTIONS.delete(id);
      return { success: true, subscriptionId: id, result: null };
    })));
  },

  'POST /subscriptions/register': async (req, res) => {
    const body = await readJson(req);
    if (clientIdMissing(body)) return sendError(req, res, 400, 'Bad Request', 'clientId is required');
    if (!body || !body.subscriptionId || !Array.isArray(body.elementIds)) {
      return sendError(req, res, 400, 'Bad Request', 'subscriptionId and elementIds are required');
    }
    const sub = ownedSub(body, body.subscriptionId);
    if (!sub) return sendError(req, res, 404, 'Not Found', `Subscription not found: ${body.subscriptionId}`);
    send(req, res, 200, bulk(body.elementIds.map((id) => {
      if (!objectsById.has(id)) {
        return { success: false, elementId: id, responseDetail: { title: 'Not Found', status: 404, detail: `Element not found: ${id}` } };
      }
      sub.monitored.set(id, { maxDepth: body.maxDepth === undefined ? 1 : body.maxDepth });
      return { success: true, elementId: id, result: null };
    })));
  },

  'POST /subscriptions/unregister': async (req, res) => {
    const body = await readJson(req);
    if (clientIdMissing(body)) return sendError(req, res, 400, 'Bad Request', 'clientId is required');
    if (!body || !body.subscriptionId || !Array.isArray(body.elementIds)) {
      return sendError(req, res, 400, 'Bad Request', 'subscriptionId and elementIds are required');
    }
    const sub = ownedSub(body, body.subscriptionId);
    if (!sub) return sendError(req, res, 404, 'Not Found', `Subscription not found: ${body.subscriptionId}`);
    send(req, res, 200, bulk(body.elementIds.map((id) => {
      if (!sub.monitored.has(id)) {
        return { success: false, elementId: id, responseDetail: { title: 'Not Found', status: 404, detail: `Element not registered: ${id}` } };
      }
      sub.monitored.delete(id);
      return { success: true, elementId: id, result: null };
    })));
  },

  'POST /subscriptions/sync': async (req, res) => {
    const body = await readJson(req);
    if (clientIdMissing(body)) return sendError(req, res, 400, 'Bad Request', 'clientId is required');
    if (!body || !body.subscriptionId) return sendError(req, res, 400, 'Bad Request', 'subscriptionId is required');
    const sub = ownedSub(body, body.subscriptionId);
    if (!sub) {
      return sendError(req, res, 404, 'Not Found', `Subscription not found: ${body.subscriptionId}`);
    }
    if (sub.streamRes) return sendError(req, res, 400, 'Bad Request', 'Subscription has an open SSE stream; close it before calling sync');
    const last = body.lastSequenceNumber;
    if (last === -1 && !BREAK.has('noclearall')) sub.batches = [];
    else if (typeof last === 'number' && last >= 0) sub.batches = sub.batches.filter((b) => b.sequenceNumber > last);
    // Poll-style capture: stage the latest values of monitored objects as a new batch.
    stageBatch(sub);
    send(req, res, 200, { success: true, result: sub.batches });
  },

  'POST /subscriptions/stream': async (req, res) => {
    const body = await readJson(req);
    if (clientIdMissing(body)) return sendError(req, res, 400, 'Bad Request', 'clientId is required');
    if (!body || !body.subscriptionId) return sendError(req, res, 400, 'Bad Request', 'subscriptionId is required');
    const sub = ownedSub(body, body.subscriptionId);
    if (!sub) {
      return sendError(req, res, 404, 'Not Found', `Subscription not found: ${body.subscriptionId}`);
    }
    if (sub.streamRes && !BREAK.has('nosinglestream')) {
      try { sub.streamRes.end(); } catch { /* prior stream */ }
      sub.streamRes = null;
    }
    res.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', Connection: 'keep-alive' });
    sub.streamRes = res;
    // Send queued updates immediately, then current values on an interval.
    const pending = sub.batches.flatMap((b) => b.updates);
    if (pending.length) res.write(`data: ${JSON.stringify(pending)}\n\n`);
    const timer = setInterval(() => {
      const updates = [...sub.monitored.keys()]
        .map((id) => ({ elementId: id, ...VALUES.get(id) }))
        .filter((u) => u.timestamp);
      if (updates.length) res.write(`data: ${JSON.stringify(updates)}\n\n`);
    }, 2000);
    req.on('close', () => {
      clearInterval(timer);
      if (sub.streamRes === res) sub.streamRes = null;
    });
  }
};

// --------------------------------------------------------------------- server

function startMock(port = 8331, host = '0.0.0.0') {
  const server = http.createServer((req, res) => {
    const url = new URL(req.url, 'http://localhost');
    if (!url.pathname.startsWith('/v1/')) {
      return sendError(req, res, 404, 'Not Found', `Unknown path ${url.pathname} — endpoints are prefixed with /v1`);
    }
    const route = `${req.method} ${url.pathname.slice(3)}`;
    const handler = routes[route];
    if (!handler) return sendError(req, res, 404, 'Not Found', `No such endpoint: ${route}`);
    if (TOKEN && route !== 'GET /info') {
      const got = String(req.headers.authorization || '');
      if (got !== `Bearer ${TOKEN}`) return sendError(req, res, 401, 'Unauthorized', 'Missing or invalid bearer token');
    }
    Promise.resolve(handler(req, res, url)).catch((e) => {
      if (!res.headersSent) sendError(req, res, 500, 'Internal Server Error', e.message);
    });
  });
  server.listen(port, host, () => {
    console.log(`i3X reference mock server listening on http://localhost:${port}/v1`);
    if (TOKEN) console.log('  auth: Bearer token required (MOCK_TOKEN)');
    if (BREAK.size) console.log(`  deliberate spec violations: ${[...BREAK].join(', ')}`);
  });
  return server;
}

module.exports = { startMock };

if (require.main === module) startMock(parseInt(process.env.PORT || '8331', 10));
