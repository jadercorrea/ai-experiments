// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA374e6f1e3f9c4ee2(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-374e6f1e3f9c4ee2-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-374e6f1e3f9c4ee2-normalizer */ (/* ir:node:fresh-374e6f1e3f9c4ee2-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-374e6f1e3f9c4ee2-validation */ (/* ir:node:fresh-374e6f1e3f9c4ee2-is-empty */ (/* ir:node:fresh-374e6f1e3f9c4ee2-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-374e6f1e3f9c4ee2-invalid */ { error: /* ir:node:fresh-374e6f1e3f9c4ee2-invalid-code */ "invalid_input_374e6f1e3f9c4ee2" })
      : (/* ir:node:fresh-374e6f1e3f9c4ee2-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-374e6f1e3f9c4ee2-get-user */ capabilities.users.getById(/* ir:node:fresh-374e6f1e3f9c4ee2-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-374e6f1e3f9c4ee2-retry-guard */ (/* ir:node:fresh-374e6f1e3f9c4ee2-raw-equals-normalized */ (/* ir:node:fresh-374e6f1e3f9c4ee2-raw-for-guard */ rawId) === (/* ir:node:fresh-374e6f1e3f9c4ee2-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-374e6f1e3f9c4ee2-missing */ { error: /* ir:node:fresh-374e6f1e3f9c4ee2-missing-code */ "not_found_374e6f1e3f9c4ee2" })
              : (/* ir:node:fresh-374e6f1e3f9c4ee2-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-374e6f1e3f9c4ee2-retry-user */ capabilities.users.getById(/* ir:node:fresh-374e6f1e3f9c4ee2-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-374e6f1e3f9c4ee2-retry-missing */ { error: /* ir:node:fresh-374e6f1e3f9c4ee2-retry-missing-code */ "not_found_374e6f1e3f9c4ee2" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-374e6f1e3f9c4ee2-retry-found */ { ok: /* ir:node:fresh-374e6f1e3f9c4ee2-retry-user-ref */ retryUser };
                })());
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-374e6f1e3f9c4ee2-found */ { ok: /* ir:node:fresh-374e6f1e3f9c4ee2-user-ref */ user };
        })());
  })();
}
