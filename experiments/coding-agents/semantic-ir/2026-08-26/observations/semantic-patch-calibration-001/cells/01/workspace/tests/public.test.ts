import { lookupErrorCase } from "../src/lookup-user.ts";

function assertEquals(actual: unknown, expected: unknown): void {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(
      `expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`,
    );
  }
}

Deno.test("changes empty error and preserves success", () => {
  const calls: string[] = [];
  const capabilities = { users: { getById(id: string) { calls.push(id); return id === "42" ? { id, name: "Ada" } : undefined; } } };
  assertEquals(lookupErrorCase(" \t ", capabilities), { error: "empty_identifier" });
  assertEquals(calls, []);
  assertEquals(lookupErrorCase(" 42 ", capabilities), { ok: { id: "42", name: "Ada" } });
});
