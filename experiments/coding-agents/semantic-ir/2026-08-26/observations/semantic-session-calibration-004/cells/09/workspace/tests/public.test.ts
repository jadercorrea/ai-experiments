import { executeWithDirectory } from "../src/lookup-user.ts";

function assertEquals(actual: unknown, expected: unknown): void {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(
      `expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`,
    );
  }
}

Deno.test("returns a directory hit after local miss", () => {
  const capabilities = {
    users: { getById(_id: string) { return undefined; } },
    directory: { getById(id: string) { return { id, name: "Directory" }; } },
  };
  assertEquals(executeWithDirectory(" 42 ", capabilities), { ok: { id: "42", name: "Directory" } });
});

Deno.test("preserves a local hit", () => {
  const capabilities = {
    users: { getById(id: string) { return { id, name: "Local" }; } },
    directory: { getById(_id: string) { return undefined; } },
  };
  assertEquals(executeWithDirectory("42", capabilities), { ok: { id: "42", name: "Local" } });
});
