// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA9eb44b2030ede259(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-9eb44b2030ede259-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-9eb44b2030ede259-normalizer */ (/* ir:node:fresh-9eb44b2030ede259-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-9eb44b2030ede259-validation */ (/* ir:node:fresh-9eb44b2030ede259-is-empty */ (/* ir:node:fresh-9eb44b2030ede259-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-9eb44b2030ede259-invalid */ { error: /* ir:node:fresh-9eb44b2030ede259-invalid-code */ "invalid_input_9eb44b2030ede259" })
      : (/* ir:node:fresh-9eb44b2030ede259-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-9eb44b2030ede259-get-user */ capabilities.users.getById(/* ir:node:fresh-9eb44b2030ede259-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-9eb44b2030ede259-missing */ { error: /* ir:node:fresh-9eb44b2030ede259-missing-code */ "not_found_9eb44b2030ede259" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-9eb44b2030ede259-found */ { ok: /* ir:node:fresh-9eb44b2030ede259-user-ref */ user };
        })());
  })();
}
