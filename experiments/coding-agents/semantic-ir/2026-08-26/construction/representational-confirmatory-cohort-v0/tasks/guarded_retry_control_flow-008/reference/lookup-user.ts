// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAc66152e5cebd429f(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-c66152e5cebd429f-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-c66152e5cebd429f-normalizer */ (/* ir:node:fresh-c66152e5cebd429f-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-c66152e5cebd429f-validation */ (/* ir:node:fresh-c66152e5cebd429f-is-empty */ (/* ir:node:fresh-c66152e5cebd429f-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-c66152e5cebd429f-invalid */ { error: /* ir:node:fresh-c66152e5cebd429f-invalid-code */ "invalid_input_c66152e5cebd429f" })
      : (/* ir:node:fresh-c66152e5cebd429f-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-c66152e5cebd429f-get-user */ capabilities.users.getById(/* ir:node:fresh-c66152e5cebd429f-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-c66152e5cebd429f-retry-guard */ (/* ir:node:fresh-c66152e5cebd429f-raw-equals-normalized */ (/* ir:node:fresh-c66152e5cebd429f-raw-for-guard */ rawId) === (/* ir:node:fresh-c66152e5cebd429f-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-c66152e5cebd429f-missing */ { error: /* ir:node:fresh-c66152e5cebd429f-missing-code */ "not_found_c66152e5cebd429f" })
              : (/* ir:node:fresh-c66152e5cebd429f-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-c66152e5cebd429f-retry-user */ capabilities.users.getById(/* ir:node:fresh-c66152e5cebd429f-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-c66152e5cebd429f-retry-missing */ { error: /* ir:node:fresh-c66152e5cebd429f-retry-missing-code */ "not_found_c66152e5cebd429f" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-c66152e5cebd429f-retry-found */ { ok: /* ir:node:fresh-c66152e5cebd429f-retry-user-ref */ retryUser };
                })());
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-c66152e5cebd429f-found */ { ok: /* ir:node:fresh-c66152e5cebd429f-user-ref */ user };
        })());
  })();
}
