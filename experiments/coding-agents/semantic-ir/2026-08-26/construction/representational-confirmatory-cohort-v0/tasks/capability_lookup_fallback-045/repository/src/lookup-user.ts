// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAa856a51cee090977(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-a856a51cee090977-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-a856a51cee090977-normalizer */ (/* ir:node:fresh-a856a51cee090977-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-a856a51cee090977-validation */ (/* ir:node:fresh-a856a51cee090977-is-empty */ (/* ir:node:fresh-a856a51cee090977-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-a856a51cee090977-invalid */ { error: /* ir:node:fresh-a856a51cee090977-invalid-code */ "invalid_input_a856a51cee090977" })
      : (/* ir:node:fresh-a856a51cee090977-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-a856a51cee090977-get-user */ capabilities.users.getById(/* ir:node:fresh-a856a51cee090977-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-a856a51cee090977-missing */ { error: /* ir:node:fresh-a856a51cee090977-missing-code */ "not_found_a856a51cee090977" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-a856a51cee090977-found */ { ok: /* ir:node:fresh-a856a51cee090977-user-ref */ user };
        })());
  })();
}
