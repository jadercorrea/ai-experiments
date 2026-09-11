interface User { readonly id: string; readonly name: string; }
interface Capabilities {
  readonly users: { getById(id: string): User | undefined };
}
type Lookup = (rawId: string, capabilities: Capabilities) => { ok: User } | { error: string };
function assertEquals(actual: unknown, expected: unknown): void {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(
      `expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`,
    );
  }
}

const subjectUrl = Deno.env.get("SEMANTIC_IR_SUBJECT");
if (subjectUrl === undefined) throw new Error("SEMANTIC_IR_SUBJECT is required");
const subject = await import(subjectUrl) as { processGuardedUser: Lookup };
const lookup = subject.processGuardedUser;

Deno.test("rejects the exact reserved identifier", () => {
  const calls: string[] = [];
  const capabilities = { users: { getById(id: string) { calls.push(id); return { id, name: "Forbidden" }; } } };
  assertEquals(lookup("root", capabilities), { error: "reserved_user_id" });
  assertEquals(calls, []);
});

Deno.test("guard is exact and case-sensitive", () => {
  const calls: string[] = [];
  const capabilities = { users: { getById(id: string) { calls.push(id); return { id, name: "Upper" }; } } };
  assertEquals(lookup("ROOT", capabilities), { ok: { id: "ROOT", name: "Upper" } });
  assertEquals(calls, ["ROOT"]);
});

Deno.test("rooted is not reserved", () => {
  const calls: string[] = [];
  const capabilities = { users: { getById(id: string) { calls.push(id); return undefined; } } };
  assertEquals(lookup("rooted", capabilities), { error: "not_found" });
  assertEquals(calls, ["rooted"]);
});
