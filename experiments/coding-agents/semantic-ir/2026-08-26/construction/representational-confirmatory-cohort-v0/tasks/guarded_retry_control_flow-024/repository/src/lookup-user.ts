// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAca56afe2f70afb8b(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-ca56afe2f70afb8b-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-ca56afe2f70afb8b-normalizer */ (/* ir:node:fresh-ca56afe2f70afb8b-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-ca56afe2f70afb8b-validation */ (/* ir:node:fresh-ca56afe2f70afb8b-is-empty */ (/* ir:node:fresh-ca56afe2f70afb8b-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-ca56afe2f70afb8b-invalid */ { error: /* ir:node:fresh-ca56afe2f70afb8b-invalid-code */ "invalid_input_ca56afe2f70afb8b" })
      : (/* ir:node:fresh-ca56afe2f70afb8b-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-ca56afe2f70afb8b-get-user */ capabilities.users.getById(/* ir:node:fresh-ca56afe2f70afb8b-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-ca56afe2f70afb8b-missing */ { error: /* ir:node:fresh-ca56afe2f70afb8b-missing-code */ "not_found_ca56afe2f70afb8b" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-ca56afe2f70afb8b-found */ { ok: /* ir:node:fresh-ca56afe2f70afb8b-user-ref */ user };
        })());
  })();
}
