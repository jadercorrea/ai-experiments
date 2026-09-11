// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAed794e3b960a0f1a(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-ed794e3b960a0f1a-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-ed794e3b960a0f1a-normalizer */ (/* ir:node:fresh-ed794e3b960a0f1a-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-ed794e3b960a0f1a-validation */ (/* ir:node:fresh-ed794e3b960a0f1a-is-empty */ (/* ir:node:fresh-ed794e3b960a0f1a-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-ed794e3b960a0f1a-invalid */ { error: /* ir:node:fresh-ed794e3b960a0f1a-invalid-code */ "invalid_input_ed794e3b960a0f1a" })
      : (/* ir:node:fresh-ed794e3b960a0f1a-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-ed794e3b960a0f1a-get-user */ capabilities.users.getById(/* ir:node:fresh-ed794e3b960a0f1a-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-ed794e3b960a0f1a-missing */ { error: /* ir:node:fresh-ed794e3b960a0f1a-missing-code */ "not_found_ed794e3b960a0f1a" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-ed794e3b960a0f1a-found */ { ok: /* ir:node:fresh-ed794e3b960a0f1a-user-ref */ user };
        })());
  })();
}
