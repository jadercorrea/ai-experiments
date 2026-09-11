import { readUser } from "../src/mod.ts";
function assertEquals(actual: unknown, expected: unknown): void {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(
      `expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`,
    );
  }
}

Deno.test("exports the renamed lookup", () => {
  assertEquals(readUser("42"), { id: "42" });
});
