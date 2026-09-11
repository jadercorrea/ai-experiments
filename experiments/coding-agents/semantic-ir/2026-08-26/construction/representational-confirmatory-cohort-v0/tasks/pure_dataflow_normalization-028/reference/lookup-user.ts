// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAa9f801f3af619216(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-a9f801f3af619216-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-a9f801f3af619216-normalizer */ rawId;
    return /* ir:node:fresh-a9f801f3af619216-validation */ (/* ir:node:fresh-a9f801f3af619216-is-empty */ (/* ir:node:fresh-a9f801f3af619216-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-a9f801f3af619216-invalid */ { error: /* ir:node:fresh-a9f801f3af619216-invalid-code */ "invalid_input_a9f801f3af619216" })
      : (/* ir:node:fresh-a9f801f3af619216-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-a9f801f3af619216-get-user */ capabilities.users.getById(/* ir:node:fresh-a9f801f3af619216-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-a9f801f3af619216-missing */ { error: /* ir:node:fresh-a9f801f3af619216-missing-code */ "not_found_a9f801f3af619216" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-a9f801f3af619216-found */ { ok: /* ir:node:fresh-a9f801f3af619216-user-ref */ user };
        })());
  })();
}
