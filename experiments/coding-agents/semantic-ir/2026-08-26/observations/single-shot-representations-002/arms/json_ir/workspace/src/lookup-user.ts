// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function lookupUser(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:let:trimmed */ (() => {
    const trimmedId: string = /* ir:call:trim */ (/* ir:var:raw-id */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:if:empty-check */ (/* ir:call:is-empty */ (/* ir:var:trimmed-id-empty-check */ trimmedId).length === 0)
      ? (/* ir:err:invalid-user-id */ { error: /* ir:str:invalid-user-id */ "invalid_user_id" })
      : (/* ir:let:lookup-result */ (() => {
          const lookupResult: User | undefined = /* ir:call:get-by-id */ capabilities.users.getById(/* ir:var:trimmed-id-lookup */ trimmedId);
          return /* ir:match:lookup-result */ (() => {
            const __semantic_ir_option_1 = /* ir:var:lookup-result-match */ lookupResult;
            if (__semantic_ir_option_1 === undefined) {
              return /* ir:err:not-found */ { error: /* ir:str:not-found */ "not_found" };
            }
            const foundUser: User = __semantic_ir_option_1;
            return /* ir:ok:found-user */ { ok: /* ir:var:found-user-ok */ foundUser };
          })();
        })());
  })();
}
