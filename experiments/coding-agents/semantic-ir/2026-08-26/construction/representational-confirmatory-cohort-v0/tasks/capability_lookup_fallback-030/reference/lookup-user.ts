// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
  directory: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAb983a23164516b47(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-b983a23164516b47-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-b983a23164516b47-normalizer */ (/* ir:node:fresh-b983a23164516b47-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-b983a23164516b47-validation */ (/* ir:node:fresh-b983a23164516b47-is-empty */ (/* ir:node:fresh-b983a23164516b47-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-b983a23164516b47-invalid */ { error: /* ir:node:fresh-b983a23164516b47-invalid-code */ "invalid_input_b983a23164516b47" })
      : (/* ir:node:fresh-b983a23164516b47-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-b983a23164516b47-get-user */ capabilities.users.getById(/* ir:node:fresh-b983a23164516b47-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-b983a23164516b47-directory-match */ (() => {
              const __semantic_ir_option_2 = /* ir:node:fresh-b983a23164516b47-get-directory-user */ capabilities.directory.getById(/* ir:node:fresh-b983a23164516b47-identifier-for-directory */ rawId);
              if (__semantic_ir_option_2 === undefined) {
                return /* ir:node:fresh-b983a23164516b47-missing */ { error: /* ir:node:fresh-b983a23164516b47-missing-code */ "not_found_b983a23164516b47" };
              }
              const directoryUser: User = __semantic_ir_option_2;
              return /* ir:node:fresh-b983a23164516b47-directory-found */ { ok: /* ir:node:fresh-b983a23164516b47-directory-user-ref */ directoryUser };
            })();
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-b983a23164516b47-found */ { ok: /* ir:node:fresh-b983a23164516b47-user-ref */ user };
        })());
  })();
}
