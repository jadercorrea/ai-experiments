// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
  directory: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA043b9a5ca1d05e27(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-043b9a5ca1d05e27-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-043b9a5ca1d05e27-normalizer */ (/* ir:node:fresh-043b9a5ca1d05e27-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-043b9a5ca1d05e27-validation */ (/* ir:node:fresh-043b9a5ca1d05e27-is-empty */ (/* ir:node:fresh-043b9a5ca1d05e27-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-043b9a5ca1d05e27-invalid */ { error: /* ir:node:fresh-043b9a5ca1d05e27-invalid-code */ "invalid_input_043b9a5ca1d05e27" })
      : (/* ir:node:fresh-043b9a5ca1d05e27-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-043b9a5ca1d05e27-get-user */ capabilities.users.getById(/* ir:node:fresh-043b9a5ca1d05e27-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-043b9a5ca1d05e27-directory-match */ (() => {
              const __semantic_ir_option_2 = /* ir:node:fresh-043b9a5ca1d05e27-get-directory-user */ capabilities.directory.getById(/* ir:node:fresh-043b9a5ca1d05e27-identifier-for-directory */ rawId);
              if (__semantic_ir_option_2 === undefined) {
                return /* ir:node:fresh-043b9a5ca1d05e27-missing */ { error: /* ir:node:fresh-043b9a5ca1d05e27-missing-code */ "not_found_043b9a5ca1d05e27" };
              }
              const directoryUser: User = __semantic_ir_option_2;
              return /* ir:node:fresh-043b9a5ca1d05e27-directory-found */ { ok: /* ir:node:fresh-043b9a5ca1d05e27-directory-user-ref */ directoryUser };
            })();
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-043b9a5ca1d05e27-found */ { ok: /* ir:node:fresh-043b9a5ca1d05e27-user-ref */ user };
        })());
  })();
}
