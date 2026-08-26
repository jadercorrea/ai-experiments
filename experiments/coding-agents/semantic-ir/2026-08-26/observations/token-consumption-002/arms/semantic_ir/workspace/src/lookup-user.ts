// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function lookupUser(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:let-trimmed */ (() => {
    const trimmedId: string = /* ir:node:call-trim */ (/* ir:node:var-raw-id */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:if-empty */ (/* ir:node:call-is-empty */ (/* ir:node:var-trimmed-id */ trimmedId).length === 0)
      ? (/* ir:node:err-invalid */ { error: /* ir:node:str-invalid-user-id */ "invalid_user_id" })
      : (/* ir:node:option-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:call-get-by-id */ capabilities.users.getById(/* ir:node:var-trimmed-id2 */ trimmedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:err-not-found */ { error: /* ir:node:str-not-found */ "not_found" };
          }
          const foundUser: User = __semantic_ir_option_1;
          return /* ir:node:ok-user */ { ok: /* ir:node:var-found-user */ foundUser };
        })());
  })();
}
