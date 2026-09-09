// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA17a1c3606fe16aaa(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-17a1c3606fe16aaa-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-17a1c3606fe16aaa-normalizer */ rawId;
    return /* ir:node:fresh-17a1c3606fe16aaa-validation */ (/* ir:node:fresh-17a1c3606fe16aaa-is-empty */ (/* ir:node:fresh-17a1c3606fe16aaa-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-17a1c3606fe16aaa-invalid */ { error: /* ir:node:fresh-17a1c3606fe16aaa-invalid-code */ "empty_identifier_17a1c3606fe16aaa" })
      : (/* ir:node:fresh-17a1c3606fe16aaa-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-17a1c3606fe16aaa-get-user */ capabilities.users.getById(/* ir:node:fresh-17a1c3606fe16aaa-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-17a1c3606fe16aaa-missing */ { error: /* ir:node:fresh-17a1c3606fe16aaa-missing-code */ "unknown_user_17a1c3606fe16aaa" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-17a1c3606fe16aaa-found */ { ok: /* ir:node:fresh-17a1c3606fe16aaa-user-ref */ user };
        })());
  })();
}
