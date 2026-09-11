// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA3146e7c2f805ea07(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-3146e7c2f805ea07-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-3146e7c2f805ea07-normalizer */ (/* ir:node:fresh-3146e7c2f805ea07-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-3146e7c2f805ea07-validation */ (/* ir:node:fresh-3146e7c2f805ea07-is-empty */ (/* ir:node:fresh-3146e7c2f805ea07-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-3146e7c2f805ea07-invalid */ { error: /* ir:node:fresh-3146e7c2f805ea07-invalid-code */ "invalid_input_3146e7c2f805ea07" })
      : (/* ir:node:fresh-3146e7c2f805ea07-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-3146e7c2f805ea07-get-user */ capabilities.users.getById(/* ir:node:fresh-3146e7c2f805ea07-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-3146e7c2f805ea07-missing */ { error: /* ir:node:fresh-3146e7c2f805ea07-missing-code */ "not_found_3146e7c2f805ea07" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-3146e7c2f805ea07-found */ { ok: /* ir:node:fresh-3146e7c2f805ea07-user-ref */ user };
        })());
  })();
}
