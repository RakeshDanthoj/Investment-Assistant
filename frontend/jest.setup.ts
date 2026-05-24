import "@testing-library/jest-dom";
import { toHaveNoViolations } from "jest-axe";
import { webcrypto } from "crypto";
import { TextDecoder, TextEncoder } from "util";

expect.extend(toHaveNoViolations);

if (typeof globalThis.TextEncoder === "undefined") {
  globalThis.TextEncoder = TextEncoder as typeof globalThis.TextEncoder;
}
if (typeof globalThis.TextDecoder === "undefined") {
  globalThis.TextDecoder = TextDecoder as typeof globalThis.TextDecoder;
}
if (!globalThis.crypto?.subtle) {
  Object.defineProperty(globalThis, "crypto", {
    value: webcrypto,
    configurable: true,
  });
}
