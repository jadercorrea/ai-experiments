interface User {
  readonly id: string;
  readonly name: string;
}

interface SemanticCapabilities {
  readonly users: {
    getById(id: string): User | undefined;
  };
}

type Lookup = (
  rawId: string,
  capabilities: SemanticCapabilities,
) => { ok: User } | { error: string };

function assertEquals(actual: unknown, expected: unknown): void {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(
      `expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`,
    );
  }
}

const subjectUrl = Deno.env.get("SEMANTIC_IR_SUBJECT");
if (subjectUrl === undefined) {
  throw new Error("SEMANTIC_IR_SUBJECT is required");
}
const subject = await import(subjectUrl) as { lookupUser: Lookup };

Deno.test("uses the new missing-user error after exactly one lookup", () => {
  const calls: string[] = [];
  const capabilities: SemanticCapabilities = {
    users: {
      getById(id: string): User | undefined {
        calls.push(id);
        return undefined;
      },
    },
  };

  assertEquals(subject.lookupUser(" missing ", capabilities), {
    error: "user_not_found",
  });
  assertEquals(calls, ["missing"]);
});

Deno.test("preserves ASCII-only normalization", () => {
  const identifier = "\u00a042\u00a0";
  const user: User = { id: identifier, name: "Grace" };
  const calls: string[] = [];
  const capabilities: SemanticCapabilities = {
    users: {
      getById(id: string): User | undefined {
        calls.push(id);
        return id === identifier ? user : undefined;
      },
    },
  };

  assertEquals(subject.lookupUser(identifier, capabilities), { ok: user });
  assertEquals(calls, [identifier]);
});

Deno.test("uses the new empty error for every ASCII representation", () => {
  for (const rawId of ["", " ", "\t", "\n", "\v", "\f", "\r"]) {
    let callCount = 0;
    const capabilities: SemanticCapabilities = {
      users: {
        getById(): User | undefined {
          callCount += 1;
          return undefined;
        },
      },
    };

    assertEquals(subject.lookupUser(rawId, capabilities), {
      error: "empty_user_id",
    });
    assertEquals(callCount, 0);
  }
});
