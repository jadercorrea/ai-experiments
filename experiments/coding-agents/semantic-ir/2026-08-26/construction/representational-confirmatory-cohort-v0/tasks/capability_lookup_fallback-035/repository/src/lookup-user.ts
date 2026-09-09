// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA06dde0b33277176e(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-06dde0b33277176e-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-06dde0b33277176e-normalizer */ (/* ir:node:fresh-06dde0b33277176e-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-06dde0b33277176e-validation */ (/* ir:node:fresh-06dde0b33277176e-is-empty */ (/* ir:node:fresh-06dde0b33277176e-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-06dde0b33277176e-invalid */ { error: /* ir:node:fresh-06dde0b33277176e-invalid-code */ "invalid_input_06dde0b33277176e" })
      : (/* ir:node:fresh-06dde0b33277176e-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-06dde0b33277176e-get-user */ capabilities.users.getById(/* ir:node:fresh-06dde0b33277176e-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-06dde0b33277176e-missing */ { error: /* ir:node:fresh-06dde0b33277176e-missing-code */ "not_found_06dde0b33277176e" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-06dde0b33277176e-found */ { ok: /* ir:node:fresh-06dde0b33277176e-user-ref */ user };
        })());
  })();
}
