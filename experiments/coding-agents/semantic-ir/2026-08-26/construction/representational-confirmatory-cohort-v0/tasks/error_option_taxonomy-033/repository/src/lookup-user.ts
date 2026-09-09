// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAe650f280979d9148(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-e650f280979d9148-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-e650f280979d9148-normalizer */ (/* ir:node:fresh-e650f280979d9148-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-e650f280979d9148-validation */ (/* ir:node:fresh-e650f280979d9148-is-empty */ (/* ir:node:fresh-e650f280979d9148-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-e650f280979d9148-invalid */ { error: /* ir:node:fresh-e650f280979d9148-invalid-code */ "invalid_input_e650f280979d9148" })
      : (/* ir:node:fresh-e650f280979d9148-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-e650f280979d9148-get-user */ capabilities.users.getById(/* ir:node:fresh-e650f280979d9148-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-e650f280979d9148-missing */ { error: /* ir:node:fresh-e650f280979d9148-missing-code */ "not_found_e650f280979d9148" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-e650f280979d9148-found */ { ok: /* ir:node:fresh-e650f280979d9148-user-ref */ user };
        })());
  })();
}
