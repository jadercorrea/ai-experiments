// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAcd4d573939202935(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-cd4d573939202935-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-cd4d573939202935-normalizer */ (/* ir:node:fresh-cd4d573939202935-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-cd4d573939202935-validation */ (/* ir:node:fresh-cd4d573939202935-is-empty */ (/* ir:node:fresh-cd4d573939202935-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-cd4d573939202935-invalid */ { error: /* ir:node:fresh-cd4d573939202935-invalid-code */ "invalid_input_cd4d573939202935" })
      : (/* ir:node:fresh-cd4d573939202935-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-cd4d573939202935-get-user */ capabilities.users.getById(/* ir:node:fresh-cd4d573939202935-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-cd4d573939202935-missing */ { error: /* ir:node:fresh-cd4d573939202935-missing-code */ "not_found_cd4d573939202935" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-cd4d573939202935-found */ { ok: /* ir:node:fresh-cd4d573939202935-user-ref */ user };
        })());
  })();
}
