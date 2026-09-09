// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA5ea075eef3a0befa(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-5ea075eef3a0befa-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-5ea075eef3a0befa-normalizer */ (/* ir:node:fresh-5ea075eef3a0befa-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-5ea075eef3a0befa-validation */ (/* ir:node:fresh-5ea075eef3a0befa-is-empty */ (/* ir:node:fresh-5ea075eef3a0befa-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-5ea075eef3a0befa-invalid */ { error: /* ir:node:fresh-5ea075eef3a0befa-invalid-code */ "invalid_input_5ea075eef3a0befa" })
      : (/* ir:node:fresh-5ea075eef3a0befa-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-5ea075eef3a0befa-get-user */ capabilities.users.getById(/* ir:node:fresh-5ea075eef3a0befa-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-5ea075eef3a0befa-missing */ { error: /* ir:node:fresh-5ea075eef3a0befa-missing-code */ "not_found_5ea075eef3a0befa" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-5ea075eef3a0befa-found */ { ok: /* ir:node:fresh-5ea075eef3a0befa-user-ref */ user };
        })());
  })();
}
