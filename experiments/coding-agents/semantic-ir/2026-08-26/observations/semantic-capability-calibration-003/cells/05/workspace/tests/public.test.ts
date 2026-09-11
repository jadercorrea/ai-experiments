import { processWithRetry } from "../src/lookup-user.ts";

function assertEquals(actual: unknown, expected: unknown): void {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(
      `expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`,
    );
  }
}

Deno.test("retries the original identifier after normalized miss", () => {
  const calls: string[] = [];
  const capabilities = { users: { getById(id: string) { calls.push(id); return id === " 42 " ? { id, name: "Raw" } : undefined; } } };
  assertEquals(processWithRetry(" 42 ", capabilities), { ok: { id: " 42 ", name: "Raw" } });
  assertEquals(calls, ["42", " 42 "]);
});

Deno.test("does not retry a normalized hit", () => {
  const calls: string[] = [];
  const capabilities = { users: { getById(id: string) { calls.push(id); return { id, name: "Local" }; } } };
  assertEquals(processWithRetry(" 42 ", capabilities), { ok: { id: "42", name: "Local" } });
  assertEquals(calls, ["42"]);
});
