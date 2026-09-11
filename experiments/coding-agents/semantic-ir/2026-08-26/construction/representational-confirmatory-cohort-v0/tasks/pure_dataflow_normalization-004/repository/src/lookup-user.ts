// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAc774c29a2a7d06e9(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-c774c29a2a7d06e9-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-c774c29a2a7d06e9-normalizer */ rawId;
    return /* ir:node:fresh-c774c29a2a7d06e9-validation */ (/* ir:node:fresh-c774c29a2a7d06e9-is-empty */ (/* ir:node:fresh-c774c29a2a7d06e9-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-c774c29a2a7d06e9-invalid */ { error: /* ir:node:fresh-c774c29a2a7d06e9-invalid-code */ "invalid_input_c774c29a2a7d06e9" })
      : (/* ir:node:fresh-c774c29a2a7d06e9-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-c774c29a2a7d06e9-get-user */ capabilities.users.getById(/* ir:node:fresh-c774c29a2a7d06e9-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-c774c29a2a7d06e9-missing */ { error: /* ir:node:fresh-c774c29a2a7d06e9-missing-code */ "not_found_c774c29a2a7d06e9" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-c774c29a2a7d06e9-found */ { ok: /* ir:node:fresh-c774c29a2a7d06e9-user-ref */ user };
        })());
  })();
}
