interface User { readonly id: string; readonly name: string; }
interface Capabilities {
  readonly users: { getById(id: string): User | undefined };
  readonly directory: { getById(id: string): User | undefined };
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
const subject = await import(subjectUrl) as { lookupWithDirectory: Lookup };
const lookup = subject.lookupWithDirectory;

Deno.test("local hit never calls directory", () => {
  const calls: string[] = [];
  const capabilities = {
    users: { getById(id: string) { calls.push(`users:${id}`); return { id, name: "Local" }; } },
    directory: { getById(id: string) { calls.push(`directory:${id}`); return undefined; } },
  };
  assertEquals(lookup("42", capabilities), { ok: { id: "42", name: "Local" } });
  assertEquals(calls, ["users:42"]);
});

Deno.test("double miss is ordered and preserves not found", () => {
  const calls: string[] = [];
  const capabilities = {
    users: { getById(id: string) { calls.push(`users:${id}`); return undefined; } },
    directory: { getById(id: string) { calls.push(`directory:${id}`); return undefined; } },
  };
  assertEquals(lookup(" 404 ", capabilities), { error: "not_found" });
  assertEquals(calls, ["users:404", "directory:404"]);
});

Deno.test("empty input performs no effect", () => {
  const calls: string[] = [];
  const capabilities = {
    users: { getById(id: string) { calls.push(`users:${id}`); return undefined; } },
    directory: { getById(id: string) { calls.push(`directory:${id}`); return undefined; } },
  };
  assertEquals(lookup(" ", capabilities), { error: "invalid_user_id" });
  assertEquals(calls, []);
});
