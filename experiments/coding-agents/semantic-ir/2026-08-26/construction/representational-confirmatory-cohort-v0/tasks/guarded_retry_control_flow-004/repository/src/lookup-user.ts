// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA2e2e075a5fa7e8e2(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-2e2e075a5fa7e8e2-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-2e2e075a5fa7e8e2-normalizer */ (/* ir:node:fresh-2e2e075a5fa7e8e2-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-2e2e075a5fa7e8e2-validation */ (/* ir:node:fresh-2e2e075a5fa7e8e2-is-empty */ (/* ir:node:fresh-2e2e075a5fa7e8e2-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-2e2e075a5fa7e8e2-invalid */ { error: /* ir:node:fresh-2e2e075a5fa7e8e2-invalid-code */ "invalid_input_2e2e075a5fa7e8e2" })
      : (/* ir:node:fresh-2e2e075a5fa7e8e2-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-2e2e075a5fa7e8e2-get-user */ capabilities.users.getById(/* ir:node:fresh-2e2e075a5fa7e8e2-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-2e2e075a5fa7e8e2-missing */ { error: /* ir:node:fresh-2e2e075a5fa7e8e2-missing-code */ "not_found_2e2e075a5fa7e8e2" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-2e2e075a5fa7e8e2-found */ { ok: /* ir:node:fresh-2e2e075a5fa7e8e2-user-ref */ user };
        })());
  })();
}
