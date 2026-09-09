// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA0fb99c86099e4493(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-0fb99c86099e4493-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-0fb99c86099e4493-normalizer */ (/* ir:node:fresh-0fb99c86099e4493-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-0fb99c86099e4493-validation */ (/* ir:node:fresh-0fb99c86099e4493-is-empty */ (/* ir:node:fresh-0fb99c86099e4493-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-0fb99c86099e4493-invalid */ { error: /* ir:node:fresh-0fb99c86099e4493-invalid-code */ "invalid_input_0fb99c86099e4493" })
      : (/* ir:node:fresh-0fb99c86099e4493-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-0fb99c86099e4493-get-user */ capabilities.users.getById(/* ir:node:fresh-0fb99c86099e4493-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-0fb99c86099e4493-retry-guard */ (/* ir:node:fresh-0fb99c86099e4493-raw-equals-normalized */ (/* ir:node:fresh-0fb99c86099e4493-raw-for-guard */ rawId) === (/* ir:node:fresh-0fb99c86099e4493-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-0fb99c86099e4493-missing */ { error: /* ir:node:fresh-0fb99c86099e4493-missing-code */ "not_found_0fb99c86099e4493" })
              : (/* ir:node:fresh-0fb99c86099e4493-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-0fb99c86099e4493-retry-user */ capabilities.users.getById(/* ir:node:fresh-0fb99c86099e4493-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-0fb99c86099e4493-retry-missing */ { error: /* ir:node:fresh-0fb99c86099e4493-retry-missing-code */ "not_found_0fb99c86099e4493" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-0fb99c86099e4493-retry-found */ { ok: /* ir:node:fresh-0fb99c86099e4493-retry-user-ref */ retryUser };
                })());
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-0fb99c86099e4493-found */ { ok: /* ir:node:fresh-0fb99c86099e4493-user-ref */ user };
        })());
  })();
}
