// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA5a5ef5f1b5ea248a(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-5a5ef5f1b5ea248a-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-5a5ef5f1b5ea248a-normalizer */ (/* ir:node:fresh-5a5ef5f1b5ea248a-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-5a5ef5f1b5ea248a-validation */ (/* ir:node:fresh-5a5ef5f1b5ea248a-is-empty */ (/* ir:node:fresh-5a5ef5f1b5ea248a-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-5a5ef5f1b5ea248a-invalid */ { error: /* ir:node:fresh-5a5ef5f1b5ea248a-invalid-code */ "invalid_input_5a5ef5f1b5ea248a" })
      : (/* ir:node:fresh-5a5ef5f1b5ea248a-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-5a5ef5f1b5ea248a-get-user */ capabilities.users.getById(/* ir:node:fresh-5a5ef5f1b5ea248a-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-5a5ef5f1b5ea248a-missing */ { error: /* ir:node:fresh-5a5ef5f1b5ea248a-missing-code */ "not_found_5a5ef5f1b5ea248a" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-5a5ef5f1b5ea248a-found */ { ok: /* ir:node:fresh-5a5ef5f1b5ea248a-user-ref */ user };
        })());
  })();
}
