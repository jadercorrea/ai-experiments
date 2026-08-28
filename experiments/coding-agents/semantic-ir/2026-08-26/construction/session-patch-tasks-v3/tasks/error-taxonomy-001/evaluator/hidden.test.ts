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
const subject = await import(subjectUrl) as { executeErrorCase: Lookup };
const lookup = subject.executeErrorCase;

Deno.test("changes missing error after one normalized lookup", () => {
  const calls: string[] = [];
  const capabilities = { users: { getById(id: string) { calls.push(id); return undefined; } } };
  assertEquals(lookup(" missing ", capabilities), { error: "unknown_user" });
  assertEquals(calls, ["missing"]);
});

Deno.test("retains ASCII-only normalization", () => {
  const id = " 42 ";
  const capabilities = { users: { getById(value: string) { return value === id ? { id, name: "NBSP" } : undefined; } } };
  assertEquals(lookup(id, capabilities), { ok: { id, name: "NBSP" } });
});
