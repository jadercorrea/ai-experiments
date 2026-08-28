function assertEquals(actual: unknown, expected: unknown): void {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(
      `expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`,
    );
  }
}

const subjectUrl = Deno.env.get("SEMANTIC_IR_SUBJECT");
if (subjectUrl === undefined) throw new Error("SEMANTIC_IR_SUBJECT is required");
const subject = await import(subjectUrl) as Record<string, unknown>;

Deno.test("migrates the contract and removes the old export", () => {
  assertEquals(subject.EXECUTE_CONTRACT, "loadUser");
  assertEquals("executeUser" in subject, false);
  assertEquals(typeof subject.loadUser, "function");
});
