// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAf0ed7e89ec97f095(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-f0ed7e89ec97f095-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-f0ed7e89ec97f095-normalizer */ (/* ir:node:fresh-f0ed7e89ec97f095-raw-after-normalization-patch */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-f0ed7e89ec97f095-validation */ (/* ir:node:fresh-f0ed7e89ec97f095-is-empty */ (/* ir:node:fresh-f0ed7e89ec97f095-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-f0ed7e89ec97f095-invalid */ { error: /* ir:node:fresh-f0ed7e89ec97f095-invalid-code */ "invalid_input_f0ed7e89ec97f095" })
      : (/* ir:node:fresh-f0ed7e89ec97f095-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-f0ed7e89ec97f095-get-user */ capabilities.users.getById(/* ir:node:fresh-f0ed7e89ec97f095-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-f0ed7e89ec97f095-missing */ { error: /* ir:node:fresh-f0ed7e89ec97f095-missing-code */ "not_found_f0ed7e89ec97f095" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-f0ed7e89ec97f095-found */ { ok: /* ir:node:fresh-f0ed7e89ec97f095-user-ref */ user };
        })());
  })();
}
