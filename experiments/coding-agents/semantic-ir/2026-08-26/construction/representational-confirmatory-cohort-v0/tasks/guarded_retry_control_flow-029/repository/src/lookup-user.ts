// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA4fc1d738cad4dd0c(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-4fc1d738cad4dd0c-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-4fc1d738cad4dd0c-normalizer */ (/* ir:node:fresh-4fc1d738cad4dd0c-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-4fc1d738cad4dd0c-validation */ (/* ir:node:fresh-4fc1d738cad4dd0c-is-empty */ (/* ir:node:fresh-4fc1d738cad4dd0c-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-4fc1d738cad4dd0c-invalid */ { error: /* ir:node:fresh-4fc1d738cad4dd0c-invalid-code */ "invalid_input_4fc1d738cad4dd0c" })
      : (/* ir:node:fresh-4fc1d738cad4dd0c-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-4fc1d738cad4dd0c-get-user */ capabilities.users.getById(/* ir:node:fresh-4fc1d738cad4dd0c-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-4fc1d738cad4dd0c-missing */ { error: /* ir:node:fresh-4fc1d738cad4dd0c-missing-code */ "not_found_4fc1d738cad4dd0c" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-4fc1d738cad4dd0c-found */ { ok: /* ir:node:fresh-4fc1d738cad4dd0c-user-ref */ user };
        })());
  })();
}
