// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAddbc2ba303488ef6(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-ddbc2ba303488ef6-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-ddbc2ba303488ef6-normalizer */ (/* ir:node:fresh-ddbc2ba303488ef6-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-ddbc2ba303488ef6-validation */ (/* ir:node:fresh-ddbc2ba303488ef6-is-empty */ (/* ir:node:fresh-ddbc2ba303488ef6-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-ddbc2ba303488ef6-invalid */ { error: /* ir:node:fresh-ddbc2ba303488ef6-invalid-code */ "invalid_input_ddbc2ba303488ef6" })
      : (/* ir:node:fresh-ddbc2ba303488ef6-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-ddbc2ba303488ef6-get-user */ capabilities.users.getById(/* ir:node:fresh-ddbc2ba303488ef6-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-ddbc2ba303488ef6-missing */ { error: /* ir:node:fresh-ddbc2ba303488ef6-missing-code */ "not_found_ddbc2ba303488ef6" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-ddbc2ba303488ef6-found */ { ok: /* ir:node:fresh-ddbc2ba303488ef6-user-ref */ user };
        })());
  })();
}
