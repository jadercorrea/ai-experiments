// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA2f042f79b5d99fdf(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-2f042f79b5d99fdf-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-2f042f79b5d99fdf-normalizer */ (/* ir:node:fresh-2f042f79b5d99fdf-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-2f042f79b5d99fdf-validation */ (/* ir:node:fresh-2f042f79b5d99fdf-is-empty */ (/* ir:node:fresh-2f042f79b5d99fdf-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-2f042f79b5d99fdf-invalid */ { error: /* ir:node:fresh-2f042f79b5d99fdf-invalid-code */ "invalid_input_2f042f79b5d99fdf" })
      : (/* ir:node:fresh-2f042f79b5d99fdf-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-2f042f79b5d99fdf-get-user */ capabilities.users.getById(/* ir:node:fresh-2f042f79b5d99fdf-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-2f042f79b5d99fdf-retry-guard */ (/* ir:node:fresh-2f042f79b5d99fdf-raw-equals-normalized */ (/* ir:node:fresh-2f042f79b5d99fdf-raw-for-guard */ rawId) === (/* ir:node:fresh-2f042f79b5d99fdf-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-2f042f79b5d99fdf-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-2f042f79b5d99fdf-retry-user */ capabilities.users.getById(/* ir:node:fresh-2f042f79b5d99fdf-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-2f042f79b5d99fdf-retry-missing */ { error: /* ir:node:fresh-2f042f79b5d99fdf-retry-missing-code */ "not_found_2f042f79b5d99fdf" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-2f042f79b5d99fdf-retry-found */ { ok: /* ir:node:fresh-2f042f79b5d99fdf-retry-user-ref */ retryUser };
                })())
              : (/* ir:node:fresh-2f042f79b5d99fdf-missing */ { error: /* ir:node:fresh-2f042f79b5d99fdf-missing-code */ "not_found_2f042f79b5d99fdf" });
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-2f042f79b5d99fdf-found */ { ok: /* ir:node:fresh-2f042f79b5d99fdf-user-ref */ user };
        })());
  })();
}
