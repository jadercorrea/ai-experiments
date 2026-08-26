import {
  lookupUser,
  type SemanticCapabilities,
  type User,
} from "../src/lookup-user.ts";

function assertEquals(actual: unknown, expected: unknown): void {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(
      `expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`,
    );
  }
}

function capability(
  users: Readonly<Record<string, User>>,
  calls: string[],
): SemanticCapabilities {
  return {
    users: {
      getById(id: string): User | undefined {
        calls.push(id);
        return users[id];
      },
    },
  };
}

Deno.test("rejects an ASCII-whitespace-only identifier without I/O", () => {
  const calls: string[] = [];
  const result = lookupUser(" \t\n\v\f\r ", capability({}, calls));

  assertEquals(result, { error: "invalid_user_id" });
  assertEquals(calls, []);
});

Deno.test("normalizes an identifier and returns the matching user", () => {
  const calls: string[] = [];
  const user: User = { id: "42", name: "Ada" };
  const result = lookupUser(" \t42\r ", capability({ "42": user }, calls));

  assertEquals(result, { ok: user });
  assertEquals(calls, ["42"]);
});
