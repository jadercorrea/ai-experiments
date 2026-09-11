import { resolveRawIdentifier } from "../src/lookup-user.ts";

function assertEquals(actual: unknown, expected: unknown): void {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(
      `expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`,
    );
  }
}

Deno.test("uses raw identifier and exact empty", () => {
  const calls: string[] = [];
  const raw = " 42 ";
  const capabilities = { users: { getById(id: string) { calls.push(id); return id === raw ? { id, name: "Raw" } : undefined; } } };
  assertEquals(resolveRawIdentifier(raw, capabilities), { ok: { id: raw, name: "Raw" } });
  assertEquals(calls, [raw]);
  calls.length = 0;
  assertEquals(resolveRawIdentifier("", capabilities), { error: "invalid_user_id" });
  assertEquals(calls, []);
});
