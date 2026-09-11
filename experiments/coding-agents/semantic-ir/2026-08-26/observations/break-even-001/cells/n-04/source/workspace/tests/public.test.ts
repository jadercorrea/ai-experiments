import * as subject from "../src/lookups.ts";

const expectedNames = ["lookupUser01","lookupUser02","lookupUser03","lookupUser04"] as const;

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

for (const name of expectedNames) {
  const lookup = subject[name];
  Deno.test(`${name} rejects ASCII whitespace without I/O`, () => {
    let calls = 0;
    const result = lookup(" \t\n\v\f\r ", {
      users: { getById: () => { calls += 1; return undefined; } },
    });
    assert("error" in result && result.error === "invalid_user_id", name);
    assert(calls === 0, `${name} performed unexpected I/O`);
  });

  Deno.test(`${name} normalizes and returns a user`, () => {
    const seen: string[] = [];
    const result = lookup(" \t42\r ", {
      users: {
        getById: (id: string) => {
          seen.push(id);
          return id === "42" ? { id, name: "Ada" } : undefined;
        },
      },
    });
    assert("ok" in result && result.ok.id === "42", name);
    assert(JSON.stringify(seen) === '["42"]', `${name} lookup trace`);
  });
}
