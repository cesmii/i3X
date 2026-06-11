'use strict';

const { SDK_DOCS } = require('./specrefs');

/**
 * Type system maturity: "rich" when at least one Object Type defines a
 * structured (object) schema with declared properties. A type registry made
 * up solely of primitive scalars (number/string/boolean/integer) is flagged
 * "Immature Type System" in the verdict.
 */
function isRichTypeSystem(objectTypes) {
  if (!objectTypes || !objectTypes.length) return false;
  return objectTypes.some((t) => {
    const s = t.schema;
    if (!s || typeof s !== 'object') return false;
    if (Array.isArray(s.allOf) && s.allOf.length) return true;
    const types = Array.isArray(s.type) ? s.type : [s.type];
    return types.includes('object') && s.properties && Object.keys(s.properties).length > 0;
  });
}

const FEATURE_LABELS = {
  'update.current': 'Update current values (PUT /objects/value)',
  'update.history': 'Update historical values (PUT /objects/history)',
  'subscribe.stream': 'SSE streaming (POST /subscriptions/stream)'
};

function computeSummary(results, ctx) {
  const counts = { pass: 0, fail: 0, warn: 0, skip: 0, total: results.length };
  for (const r of results) counts[r.status] = (counts[r.status] || 0) + 1;

  const mustFailures = results.filter((r) => r.status === 'fail' && r.level === 'MUST');
  const mayFailures = results.filter((r) => r.status === 'fail' && r.level === 'MAY');
  const warnings = results.filter((r) => r.status === 'warn');

  // Optional features the server chose not to implement (allowed).
  const omittedFeatures = [
    ...new Set(results.filter((r) => r.status === 'skip' && r.reason === 'omitted' && r.feature).map((r) => r.feature))
  ];
  // MAY tests the user disabled or that were untestable — they cap the ceiling at "verified with caveats".
  const unverifiedMay = results.filter(
    (r) => r.level === 'MAY' && r.status === 'skip' && r.reason !== 'omitted'
  );

  const typeSystemRich = isRichTypeSystem(ctx.objectTypes);
  const serverReached = Boolean(ctx.infoRes || ctx.namespaces);

  let verdict;
  let headline;
  const notes = [];

  if (!serverReached) {
    verdict = 'Not Compliant';
    headline = 'The server could not be reached or did not respond like an i3X server. Check the endpoint URL and credentials, then re-run.';
  } else if (mustFailures.length || mayFailures.length) {
    verdict = 'Not Compliant';
    const parts = [];
    if (mustFailures.length) parts.push(`${mustFailures.length} required (MUST) test(s) failed`);
    if (mayFailures.length) parts.push(`${mayFailures.length} declared optional feature(s) behaved incorrectly`);
    headline = `${parts.join(' and ')}. See the failure list below — each entry links to the relevant section of the Implementation Guide.`;
  } else if (omittedFeatures.length) {
    verdict = '1.0 Compatible';
    headline =
      'All required (MUST) behavior passed. Optional features were omitted: ' +
      omittedFeatures.map((f) => FEATURE_LABELS[f] || f).join('; ') +
      '. Implement and declare them to reach Full 1.0 Compliance.';
  } else if (typeSystemRich) {
    verdict = 'Full 1.0 Compliance';
    headline = 'All required and optional behavior passed, and the type system exposes rich structured types. 🎉';
  } else {
    verdict = '1.0 Compliance, Immature Type System';
    headline =
      'All required and optional behavior passed, but every Object Type schema is a primitive scalar. i3X is designed around schema-aware information models — define structured Object Types (JSON Schema "type": "object" with properties) to reach Full 1.0 Compliance.';
  }

  if (unverifiedMay.length && (verdict === 'Full 1.0 Compliance' || verdict === '1.0 Compliance, Immature Type System')) {
    notes.push(
      `${unverifiedMay.length} optional-feature test(s) could not be verified (${[...new Set(unverifiedMay.map((r) => r.id))].join(', ')}) — the verdict assumes the declared capabilities behave as specified.`
    );
  }
  // Warnings are itemized in summary.warnings and rendered by the CLI/web UI.
  // (Insecure-mode runs are flagged via the CORE-05 advisory warning.)

  return {
    verdict,
    headline,
    counts,
    mustFailures: mustFailures.map(slim),
    mayFailures: mayFailures.map(slim),
    warnings: warnings.map(slim),
    omittedFeatures,
    typeSystemRich,
    specVersion: ctx.info && ctx.info.specVersion,
    serverName: ctx.info && ctx.info.serverName,
    notes,
    docsUrl: SDK_DOCS,
    finishedAt: new Date().toISOString()
  };
}

function slim(r) {
  return { id: r.id, name: r.name, level: r.level, message: r.message, refTitle: r.refTitle, refUrl: r.refUrl };
}

module.exports = { computeSummary, isRichTypeSystem };
