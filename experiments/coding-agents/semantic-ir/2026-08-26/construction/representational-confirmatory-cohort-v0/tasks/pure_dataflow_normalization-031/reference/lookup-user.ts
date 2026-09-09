// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAc4204636cf8370a4(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-c4204636cf8370a4-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-c4204636cf8370a4-normalizer */ rawId;
    return /* ir:node:fresh-c4204636cf8370a4-validation */ (/* ir:node:fresh-c4204636cf8370a4-is-empty */ (/* ir:node:fresh-c4204636cf8370a4-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-c4204636cf8370a4-invalid */ { error: /* ir:node:fresh-c4204636cf8370a4-invalid-code */ "invalid_input_c4204636cf8370a4" })
      : (/* ir:node:fresh-c4204636cf8370a4-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-c4204636cf8370a4-get-user */ capabilities.users.getById(/* ir:node:fresh-c4204636cf8370a4-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-c4204636cf8370a4-missing */ { error: /* ir:node:fresh-c4204636cf8370a4-missing-code */ "not_found_c4204636cf8370a4" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-c4204636cf8370a4-found */ { ok: /* ir:node:fresh-c4204636cf8370a4-user-ref */ user };
        })());
  })();
}
