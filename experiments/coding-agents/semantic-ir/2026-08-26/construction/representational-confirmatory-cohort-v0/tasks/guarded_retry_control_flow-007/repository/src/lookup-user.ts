// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA15b44f3ca18eabaa(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-15b44f3ca18eabaa-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-15b44f3ca18eabaa-normalizer */ (/* ir:node:fresh-15b44f3ca18eabaa-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-15b44f3ca18eabaa-validation */ (/* ir:node:fresh-15b44f3ca18eabaa-is-empty */ (/* ir:node:fresh-15b44f3ca18eabaa-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-15b44f3ca18eabaa-invalid */ { error: /* ir:node:fresh-15b44f3ca18eabaa-invalid-code */ "invalid_input_15b44f3ca18eabaa" })
      : (/* ir:node:fresh-15b44f3ca18eabaa-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-15b44f3ca18eabaa-get-user */ capabilities.users.getById(/* ir:node:fresh-15b44f3ca18eabaa-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-15b44f3ca18eabaa-missing */ { error: /* ir:node:fresh-15b44f3ca18eabaa-missing-code */ "not_found_15b44f3ca18eabaa" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-15b44f3ca18eabaa-found */ { ok: /* ir:node:fresh-15b44f3ca18eabaa-user-ref */ user };
        })());
  })();
}
