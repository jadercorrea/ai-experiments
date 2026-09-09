// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAff9f854f1bc9e975(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-ff9f854f1bc9e975-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-ff9f854f1bc9e975-normalizer */ (/* ir:node:fresh-ff9f854f1bc9e975-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-ff9f854f1bc9e975-validation */ (/* ir:node:fresh-ff9f854f1bc9e975-is-empty */ (/* ir:node:fresh-ff9f854f1bc9e975-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-ff9f854f1bc9e975-invalid */ { error: /* ir:node:fresh-ff9f854f1bc9e975-invalid-code */ "invalid_input_ff9f854f1bc9e975" })
      : (/* ir:node:fresh-ff9f854f1bc9e975-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-ff9f854f1bc9e975-get-user */ capabilities.users.getById(/* ir:node:fresh-ff9f854f1bc9e975-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-ff9f854f1bc9e975-missing */ { error: /* ir:node:fresh-ff9f854f1bc9e975-missing-code */ "not_found_ff9f854f1bc9e975" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-ff9f854f1bc9e975-found */ { ok: /* ir:node:fresh-ff9f854f1bc9e975-user-ref */ user };
        })());
  })();
}
