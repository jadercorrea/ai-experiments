// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA0fbe0fdcdc71ef9c(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-0fbe0fdcdc71ef9c-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-0fbe0fdcdc71ef9c-normalizer */ (/* ir:node:fresh-0fbe0fdcdc71ef9c-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-0fbe0fdcdc71ef9c-validation */ (/* ir:node:fresh-0fbe0fdcdc71ef9c-is-empty */ (/* ir:node:fresh-0fbe0fdcdc71ef9c-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-0fbe0fdcdc71ef9c-invalid */ { error: /* ir:node:fresh-0fbe0fdcdc71ef9c-invalid-code */ "invalid_input_0fbe0fdcdc71ef9c" })
      : (/* ir:node:fresh-0fbe0fdcdc71ef9c-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-0fbe0fdcdc71ef9c-get-user */ capabilities.users.getById(/* ir:node:fresh-0fbe0fdcdc71ef9c-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-0fbe0fdcdc71ef9c-missing */ { error: /* ir:node:fresh-0fbe0fdcdc71ef9c-missing-code */ "not_found_0fbe0fdcdc71ef9c" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-0fbe0fdcdc71ef9c-found */ { ok: /* ir:node:fresh-0fbe0fdcdc71ef9c-user-ref */ user };
        })());
  })();
}
