// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA8ff1bdc86f6116ba(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-8ff1bdc86f6116ba-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-8ff1bdc86f6116ba-normalizer */ (/* ir:node:fresh-8ff1bdc86f6116ba-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-8ff1bdc86f6116ba-validation */ (/* ir:node:fresh-8ff1bdc86f6116ba-is-empty */ (/* ir:node:fresh-8ff1bdc86f6116ba-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-8ff1bdc86f6116ba-invalid */ { error: /* ir:node:fresh-8ff1bdc86f6116ba-invalid-code */ "empty_identifier_8ff1bdc86f6116ba" })
      : (/* ir:node:fresh-8ff1bdc86f6116ba-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-8ff1bdc86f6116ba-get-user */ capabilities.users.getById(/* ir:node:fresh-8ff1bdc86f6116ba-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-8ff1bdc86f6116ba-missing */ { error: /* ir:node:fresh-8ff1bdc86f6116ba-missing-code */ "unknown_user_8ff1bdc86f6116ba" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-8ff1bdc86f6116ba-found */ { ok: /* ir:node:fresh-8ff1bdc86f6116ba-user-ref */ user };
        })());
  })();
}
