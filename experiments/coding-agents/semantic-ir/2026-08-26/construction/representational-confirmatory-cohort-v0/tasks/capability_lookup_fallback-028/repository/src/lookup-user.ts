// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA3cddfcae2261b7ba(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-3cddfcae2261b7ba-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-3cddfcae2261b7ba-normalizer */ (/* ir:node:fresh-3cddfcae2261b7ba-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-3cddfcae2261b7ba-validation */ (/* ir:node:fresh-3cddfcae2261b7ba-is-empty */ (/* ir:node:fresh-3cddfcae2261b7ba-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-3cddfcae2261b7ba-invalid */ { error: /* ir:node:fresh-3cddfcae2261b7ba-invalid-code */ "invalid_input_3cddfcae2261b7ba" })
      : (/* ir:node:fresh-3cddfcae2261b7ba-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-3cddfcae2261b7ba-get-user */ capabilities.users.getById(/* ir:node:fresh-3cddfcae2261b7ba-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-3cddfcae2261b7ba-missing */ { error: /* ir:node:fresh-3cddfcae2261b7ba-missing-code */ "not_found_3cddfcae2261b7ba" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-3cddfcae2261b7ba-found */ { ok: /* ir:node:fresh-3cddfcae2261b7ba-user-ref */ user };
        })());
  })();
}
