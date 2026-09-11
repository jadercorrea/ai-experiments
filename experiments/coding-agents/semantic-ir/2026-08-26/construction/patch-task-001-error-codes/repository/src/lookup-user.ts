// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function lookupUser(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:normalize-let */ (() => {
    const normalizedId: string = /* ir:node:trim */ (/* ir:node:raw-id-ref */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:validity-if */ (/* ir:node:is-empty */ (/* ir:node:normalized-ref-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:invalid-id */ { error: /* ir:node:invalid-id-code */ "invalid_user_id" })
      : (/* ir:node:user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:get-user */ capabilities.users.getById(/* ir:node:normalized-ref-for-lookup */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:not-found */ { error: /* ir:node:not-found-code */ "not_found" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:found */ { ok: /* ir:node:user-ref */ user };
        })());
  })();
}
