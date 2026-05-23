#!/usr/bin/env node
/**
 * Smoke tests for Lighthouse env resolution (empty GitHub secret guard).
 */

import assert from "node:assert/strict";

import { resolveThreadCardId } from "./lighthouse.mjs";

const DEFAULT = "e708b82c-f7c7-45e7-a59b-6b66dac8927a";

assert.equal(resolveThreadCardId({}), DEFAULT);
assert.equal(resolveThreadCardId({ LIGHTHOUSE_THREAD_CARD_ID: "" }), DEFAULT);
assert.equal(resolveThreadCardId({ LIGHTHOUSE_THREAD_CARD_ID: "  " }), DEFAULT);
assert.equal(resolveThreadCardId({ LIGHTHOUSE_THREAD_CARD_ID: "custom-id" }), "custom-id");

console.log("lighthouse-resolve.test.mjs: all assertions passed");
