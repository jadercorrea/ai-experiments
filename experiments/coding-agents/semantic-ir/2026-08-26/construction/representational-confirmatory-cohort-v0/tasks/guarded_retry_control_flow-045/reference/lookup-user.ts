// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA3a0137f91046caea(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-3a0137f91046caea-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-3a0137f91046caea-normalizer */ (/* ir:node:fresh-3a0137f91046caea-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-3a0137f91046caea-validation */ (/* ir:node:fresh-3a0137f91046caea-is-empty */ (/* ir:node:fresh-3a0137f91046caea-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-3a0137f91046caea-invalid */ { error: /* ir:node:fresh-3a0137f91046caea-invalid-code */ "invalid_input_3a0137f91046caea" })
      : (/* ir:node:fresh-3a0137f91046caea-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-3a0137f91046caea-get-user */ capabilities.users.getById(/* ir:node:fresh-3a0137f91046caea-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-3a0137f91046caea-retry-guard */ (/* ir:node:fresh-3a0137f91046caea-raw-equals-normalized */ (/* ir:node:fresh-3a0137f91046caea-raw-for-guard */ rawId) === (/* ir:node:fresh-3a0137f91046caea-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-3a0137f91046caea-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-3a0137f91046caea-retry-user */ capabilities.users.getById(/* ir:node:fresh-3a0137f91046caea-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-3a0137f91046caea-retry-missing */ { error: /* ir:node:fresh-3a0137f91046caea-retry-missing-code */ "not_found_3a0137f91046caea" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-3a0137f91046caea-retry-found */ { ok: /* ir:node:fresh-3a0137f91046caea-retry-user-ref */ retryUser };
                })())
              : (/* ir:node:fresh-3a0137f91046caea-missing */ { error: /* ir:node:fresh-3a0137f91046caea-missing-code */ "not_found_3a0137f91046caea" });
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-3a0137f91046caea-found */ { ok: /* ir:node:fresh-3a0137f91046caea-user-ref */ user };
        })());
  })();
}
