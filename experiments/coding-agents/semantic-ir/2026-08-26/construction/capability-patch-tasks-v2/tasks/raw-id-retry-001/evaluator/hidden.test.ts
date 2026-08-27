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
const subject = await import(subjectUrl) as { processWithRetry: Lookup };
const lookup = subject.processWithRetry;

Deno.test("retries even when normalized and raw values match", () => {
  const calls: string[] = [];
  const capabilities = { users: { getById(id: string) { calls.push(id); return undefined; } } };
  assertEquals(lookup("404", capabilities), { error: "not_found" });
  assertEquals(calls, ["404", "404"]);
});

Deno.test("empty input performs no lookup", () => {
  let calls = 0;
  const capabilities = { users: { getById(_id: string) { calls += 1; return undefined; } } };
  assertEquals(lookup(" ", capabilities), { error: "invalid_user_id" });
  assertEquals(calls, 0);
});
