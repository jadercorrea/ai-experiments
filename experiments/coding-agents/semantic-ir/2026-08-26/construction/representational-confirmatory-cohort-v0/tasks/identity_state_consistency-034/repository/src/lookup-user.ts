// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA87a4d5afea056c7a(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-87a4d5afea056c7a-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-87a4d5afea056c7a-normalizer */ (/* ir:node:fresh-87a4d5afea056c7a-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-87a4d5afea056c7a-validation */ (/* ir:node:fresh-87a4d5afea056c7a-is-empty */ (/* ir:node:fresh-87a4d5afea056c7a-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-87a4d5afea056c7a-invalid */ { error: /* ir:node:fresh-87a4d5afea056c7a-invalid-code */ "invalid_input_87a4d5afea056c7a" })
      : (/* ir:node:fresh-87a4d5afea056c7a-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-87a4d5afea056c7a-get-user */ capabilities.users.getById(/* ir:node:fresh-87a4d5afea056c7a-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-87a4d5afea056c7a-missing */ { error: /* ir:node:fresh-87a4d5afea056c7a-missing-code */ "not_found_87a4d5afea056c7a" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-87a4d5afea056c7a-found */ { ok: /* ir:node:fresh-87a4d5afea056c7a-user-ref */ user };
        })());
  })();
}
