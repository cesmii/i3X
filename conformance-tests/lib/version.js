'use strict';

// Single source of truth for the version strings shown in the CLI and web UI.
//
// SPEC_VERSION  — the i3X specification this suite validates against. Keep it in
//                 lock-step with the spec (spec/IMPLEMENTATION_GUIDE.md). It is a
//                 MAJOR.MINOR string because the spec versions that way.
// BUILD         — the revision of the test suite *itself*. Bump this whenever the
//                 tests change (added/removed/retuned checks) without the spec
//                 version moving, so a result can be traced to an exact suite rev.
const SPEC_VERSION = '1.0';
const BUILD = 3;

// e.g. "i3X 1.0 Conformance Test Suite"
const SUITE_NAME = `i3X ${SPEC_VERSION} Conformance Test Suite`;
// e.g. "v1.0 · build 1"  (compact badge for headers/banners)
const VERSION_BADGE = `v${SPEC_VERSION} · build ${BUILD}`;

module.exports = { SPEC_VERSION, BUILD, SUITE_NAME, VERSION_BADGE };
