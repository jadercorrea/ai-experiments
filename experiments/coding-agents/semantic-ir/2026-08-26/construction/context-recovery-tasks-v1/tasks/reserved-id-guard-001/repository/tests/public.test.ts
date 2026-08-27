import { resolveGuardedUser } from "../src/lookup-user.ts";

function assertEquals(actual: unknown, expected: unknown): void {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(
      `expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`,
    );
  }
}

Deno.test("rejects normalized root before lookup", () => {
  const calls: string[] = [];
  const capabilities = { users: { getById(id: string) { calls.push(id); return undefined; } } };
  assertEquals(resolveGuardedUser(" root ", capabilities), { error: "reserved_user_id" });
  assertEquals(calls, []);
});

Deno.test("preserves an ordinary local hit", () => {
  const capabilities = { users: { getById(id: string) { return { id, name: "Ada" }; } } };
  assertEquals(resolveGuardedUser("42", capabilities), { ok: { id: "42", name: "Ada" } });
});
