// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAc20fe83af1dac373(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-c20fe83af1dac373-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-c20fe83af1dac373-normalizer */ (/* ir:node:fresh-c20fe83af1dac373-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-c20fe83af1dac373-validation */ (/* ir:node:fresh-c20fe83af1dac373-is-empty */ (/* ir:node:fresh-c20fe83af1dac373-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-c20fe83af1dac373-invalid */ { error: /* ir:node:fresh-c20fe83af1dac373-invalid-code */ "invalid_input_c20fe83af1dac373" })
      : (/* ir:node:fresh-c20fe83af1dac373-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-c20fe83af1dac373-get-user */ capabilities.users.getById(/* ir:node:fresh-c20fe83af1dac373-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-c20fe83af1dac373-missing */ { error: /* ir:node:fresh-c20fe83af1dac373-missing-code */ "not_found_c20fe83af1dac373" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-c20fe83af1dac373-found */ { ok: /* ir:node:fresh-c20fe83af1dac373-user-ref */ user };
        })());
  })();
}
