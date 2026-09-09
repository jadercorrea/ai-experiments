// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA84898cc4d74df945(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-84898cc4d74df945-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-84898cc4d74df945-normalizer */ (/* ir:node:fresh-84898cc4d74df945-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-84898cc4d74df945-validation */ (/* ir:node:fresh-84898cc4d74df945-is-empty */ (/* ir:node:fresh-84898cc4d74df945-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-84898cc4d74df945-invalid */ { error: /* ir:node:fresh-84898cc4d74df945-invalid-code */ "invalid_input_84898cc4d74df945" })
      : (/* ir:node:fresh-84898cc4d74df945-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-84898cc4d74df945-get-user */ capabilities.users.getById(/* ir:node:fresh-84898cc4d74df945-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-84898cc4d74df945-missing */ { error: /* ir:node:fresh-84898cc4d74df945-missing-code */ "not_found_84898cc4d74df945" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-84898cc4d74df945-found */ { ok: /* ir:node:fresh-84898cc4d74df945-user-ref */ user };
        })());
  })();
}
