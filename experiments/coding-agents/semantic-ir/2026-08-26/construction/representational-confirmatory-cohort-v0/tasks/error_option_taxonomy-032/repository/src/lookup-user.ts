// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA9d3154da95a8d3a7(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-9d3154da95a8d3a7-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-9d3154da95a8d3a7-normalizer */ rawId;
    return /* ir:node:fresh-9d3154da95a8d3a7-validation */ (/* ir:node:fresh-9d3154da95a8d3a7-is-empty */ (/* ir:node:fresh-9d3154da95a8d3a7-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-9d3154da95a8d3a7-invalid */ { error: /* ir:node:fresh-9d3154da95a8d3a7-invalid-code */ "invalid_input_9d3154da95a8d3a7" })
      : (/* ir:node:fresh-9d3154da95a8d3a7-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-9d3154da95a8d3a7-get-user */ capabilities.users.getById(/* ir:node:fresh-9d3154da95a8d3a7-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-9d3154da95a8d3a7-missing */ { error: /* ir:node:fresh-9d3154da95a8d3a7-missing-code */ "not_found_9d3154da95a8d3a7" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-9d3154da95a8d3a7-found */ { ok: /* ir:node:fresh-9d3154da95a8d3a7-user-ref */ user };
        })());
  })();
}
