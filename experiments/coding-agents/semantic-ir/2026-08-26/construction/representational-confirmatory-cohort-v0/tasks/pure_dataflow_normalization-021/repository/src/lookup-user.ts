// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA024d72b66a5a9d5d(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-024d72b66a5a9d5d-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-024d72b66a5a9d5d-normalizer */ rawId;
    return /* ir:node:fresh-024d72b66a5a9d5d-validation */ (/* ir:node:fresh-024d72b66a5a9d5d-is-empty */ (/* ir:node:fresh-024d72b66a5a9d5d-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-024d72b66a5a9d5d-invalid */ { error: /* ir:node:fresh-024d72b66a5a9d5d-invalid-code */ "invalid_input_024d72b66a5a9d5d" })
      : (/* ir:node:fresh-024d72b66a5a9d5d-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-024d72b66a5a9d5d-get-user */ capabilities.users.getById(/* ir:node:fresh-024d72b66a5a9d5d-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-024d72b66a5a9d5d-missing */ { error: /* ir:node:fresh-024d72b66a5a9d5d-missing-code */ "not_found_024d72b66a5a9d5d" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-024d72b66a5a9d5d-found */ { ok: /* ir:node:fresh-024d72b66a5a9d5d-user-ref */ user };
        })());
  })();
}
