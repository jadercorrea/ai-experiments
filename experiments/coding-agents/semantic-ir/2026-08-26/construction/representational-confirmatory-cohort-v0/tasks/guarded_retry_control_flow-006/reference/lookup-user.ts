// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA828fe80ab9fb589c(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-828fe80ab9fb589c-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-828fe80ab9fb589c-normalizer */ (/* ir:node:fresh-828fe80ab9fb589c-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-828fe80ab9fb589c-validation */ (/* ir:node:fresh-828fe80ab9fb589c-is-empty */ (/* ir:node:fresh-828fe80ab9fb589c-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-828fe80ab9fb589c-invalid */ { error: /* ir:node:fresh-828fe80ab9fb589c-invalid-code */ "invalid_input_828fe80ab9fb589c" })
      : (/* ir:node:fresh-828fe80ab9fb589c-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-828fe80ab9fb589c-get-user */ capabilities.users.getById(/* ir:node:fresh-828fe80ab9fb589c-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-828fe80ab9fb589c-retry-guard */ (/* ir:node:fresh-828fe80ab9fb589c-raw-equals-normalized */ (/* ir:node:fresh-828fe80ab9fb589c-raw-for-guard */ rawId) === (/* ir:node:fresh-828fe80ab9fb589c-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-828fe80ab9fb589c-missing */ { error: /* ir:node:fresh-828fe80ab9fb589c-missing-code */ "not_found_828fe80ab9fb589c" })
              : (/* ir:node:fresh-828fe80ab9fb589c-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-828fe80ab9fb589c-retry-user */ capabilities.users.getById(/* ir:node:fresh-828fe80ab9fb589c-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-828fe80ab9fb589c-retry-missing */ { error: /* ir:node:fresh-828fe80ab9fb589c-retry-missing-code */ "not_found_828fe80ab9fb589c" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-828fe80ab9fb589c-retry-found */ { ok: /* ir:node:fresh-828fe80ab9fb589c-retry-user-ref */ retryUser };
                })());
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-828fe80ab9fb589c-found */ { ok: /* ir:node:fresh-828fe80ab9fb589c-user-ref */ user };
        })());
  })();
}
