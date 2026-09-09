// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA5d549445f9938e1c(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-5d549445f9938e1c-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-5d549445f9938e1c-normalizer */ (/* ir:node:fresh-5d549445f9938e1c-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-5d549445f9938e1c-validation */ (/* ir:node:fresh-5d549445f9938e1c-is-empty */ (/* ir:node:fresh-5d549445f9938e1c-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-5d549445f9938e1c-invalid */ { error: /* ir:node:fresh-5d549445f9938e1c-invalid-code */ "invalid_input_5d549445f9938e1c" })
      : (/* ir:node:fresh-5d549445f9938e1c-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-5d549445f9938e1c-get-user */ capabilities.users.getById(/* ir:node:fresh-5d549445f9938e1c-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-5d549445f9938e1c-missing */ { error: /* ir:node:fresh-5d549445f9938e1c-missing-code */ "not_found_5d549445f9938e1c" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-5d549445f9938e1c-found */ { ok: /* ir:node:fresh-5d549445f9938e1c-user-ref */ user };
        })());
  })();
}
