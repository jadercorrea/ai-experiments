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
const subject = await import(subjectUrl) as { resolveRawIdentifier: Lookup };
const lookup = subject.resolveRawIdentifier;

Deno.test("treats whitespace as a nonempty raw identifier", () => {
  const calls: string[] = [];
  const capabilities = { users: { getById(id: string) { calls.push(id); return { id, name: "Space" }; } } };
  assertEquals(lookup(" ", capabilities), { ok: { id: " ", name: "Space" } });
  assertEquals(calls, [" "]);
});

Deno.test("preserves ordinary exact lookup", () => {
  const capabilities = { users: { getById(id: string) { return { id, name: "Exact" }; } } };
  assertEquals(lookup("42", capabilities), { ok: { id: "42", name: "Exact" } });
});
