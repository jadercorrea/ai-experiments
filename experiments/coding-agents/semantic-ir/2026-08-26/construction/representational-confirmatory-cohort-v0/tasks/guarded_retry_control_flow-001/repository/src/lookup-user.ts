// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA1125da7c23f64f7e(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-1125da7c23f64f7e-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-1125da7c23f64f7e-normalizer */ (/* ir:node:fresh-1125da7c23f64f7e-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-1125da7c23f64f7e-validation */ (/* ir:node:fresh-1125da7c23f64f7e-is-empty */ (/* ir:node:fresh-1125da7c23f64f7e-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-1125da7c23f64f7e-invalid */ { error: /* ir:node:fresh-1125da7c23f64f7e-invalid-code */ "invalid_input_1125da7c23f64f7e" })
      : (/* ir:node:fresh-1125da7c23f64f7e-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-1125da7c23f64f7e-get-user */ capabilities.users.getById(/* ir:node:fresh-1125da7c23f64f7e-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-1125da7c23f64f7e-missing */ { error: /* ir:node:fresh-1125da7c23f64f7e-missing-code */ "not_found_1125da7c23f64f7e" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-1125da7c23f64f7e-found */ { ok: /* ir:node:fresh-1125da7c23f64f7e-user-ref */ user };
        })());
  })();
}
