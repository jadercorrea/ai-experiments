// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA44d129f9016a0595(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-44d129f9016a0595-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-44d129f9016a0595-normalizer */ (/* ir:node:fresh-44d129f9016a0595-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-44d129f9016a0595-validation */ (/* ir:node:fresh-44d129f9016a0595-is-empty */ (/* ir:node:fresh-44d129f9016a0595-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-44d129f9016a0595-invalid */ { error: /* ir:node:fresh-44d129f9016a0595-invalid-code */ "invalid_input_44d129f9016a0595" })
      : (/* ir:node:fresh-44d129f9016a0595-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-44d129f9016a0595-get-user */ capabilities.users.getById(/* ir:node:fresh-44d129f9016a0595-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-44d129f9016a0595-missing */ { error: /* ir:node:fresh-44d129f9016a0595-missing-code */ "not_found_44d129f9016a0595" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-44d129f9016a0595-found */ { ok: /* ir:node:fresh-44d129f9016a0595-user-ref */ user };
        })());
  })();
}
