// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA06250b8cf398caf6(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-06250b8cf398caf6-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-06250b8cf398caf6-normalizer */ rawId;
    return /* ir:node:fresh-06250b8cf398caf6-validation */ (/* ir:node:fresh-06250b8cf398caf6-is-empty */ (/* ir:node:fresh-06250b8cf398caf6-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-06250b8cf398caf6-invalid */ { error: /* ir:node:fresh-06250b8cf398caf6-invalid-code */ "invalid_input_06250b8cf398caf6" })
      : (/* ir:node:fresh-06250b8cf398caf6-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-06250b8cf398caf6-get-user */ capabilities.users.getById(/* ir:node:fresh-06250b8cf398caf6-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-06250b8cf398caf6-missing */ { error: /* ir:node:fresh-06250b8cf398caf6-missing-code */ "not_found_06250b8cf398caf6" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-06250b8cf398caf6-found */ { ok: /* ir:node:fresh-06250b8cf398caf6-user-ref */ user };
        })());
  })();
}
