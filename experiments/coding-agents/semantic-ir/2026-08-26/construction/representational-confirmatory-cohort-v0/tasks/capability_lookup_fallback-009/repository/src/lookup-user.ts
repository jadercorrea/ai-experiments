// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA66eaf2e59ec5e291(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-66eaf2e59ec5e291-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-66eaf2e59ec5e291-normalizer */ (/* ir:node:fresh-66eaf2e59ec5e291-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-66eaf2e59ec5e291-validation */ (/* ir:node:fresh-66eaf2e59ec5e291-is-empty */ (/* ir:node:fresh-66eaf2e59ec5e291-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-66eaf2e59ec5e291-invalid */ { error: /* ir:node:fresh-66eaf2e59ec5e291-invalid-code */ "invalid_input_66eaf2e59ec5e291" })
      : (/* ir:node:fresh-66eaf2e59ec5e291-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-66eaf2e59ec5e291-get-user */ capabilities.users.getById(/* ir:node:fresh-66eaf2e59ec5e291-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-66eaf2e59ec5e291-missing */ { error: /* ir:node:fresh-66eaf2e59ec5e291-missing-code */ "not_found_66eaf2e59ec5e291" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-66eaf2e59ec5e291-found */ { ok: /* ir:node:fresh-66eaf2e59ec5e291-user-ref */ user };
        })());
  })();
}
