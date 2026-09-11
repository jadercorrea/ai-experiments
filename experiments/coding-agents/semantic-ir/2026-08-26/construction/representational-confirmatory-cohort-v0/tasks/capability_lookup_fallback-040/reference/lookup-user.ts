// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
  directory: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAc63bd239749f5f4d(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-c63bd239749f5f4d-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-c63bd239749f5f4d-normalizer */ (/* ir:node:fresh-c63bd239749f5f4d-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-c63bd239749f5f4d-validation */ (/* ir:node:fresh-c63bd239749f5f4d-is-empty */ (/* ir:node:fresh-c63bd239749f5f4d-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-c63bd239749f5f4d-invalid */ { error: /* ir:node:fresh-c63bd239749f5f4d-invalid-code */ "invalid_input_c63bd239749f5f4d" })
      : (/* ir:node:fresh-c63bd239749f5f4d-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-c63bd239749f5f4d-get-user */ capabilities.users.getById(/* ir:node:fresh-c63bd239749f5f4d-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-c63bd239749f5f4d-directory-match */ (() => {
              const __semantic_ir_option_2 = /* ir:node:fresh-c63bd239749f5f4d-get-directory-user */ capabilities.directory.getById(/* ir:node:fresh-c63bd239749f5f4d-identifier-for-directory */ normalizedId);
              if (__semantic_ir_option_2 === undefined) {
                return /* ir:node:fresh-c63bd239749f5f4d-missing */ { error: /* ir:node:fresh-c63bd239749f5f4d-missing-code */ "not_found_c63bd239749f5f4d" };
              }
              const directoryUser: User = __semantic_ir_option_2;
              return /* ir:node:fresh-c63bd239749f5f4d-directory-found */ { ok: /* ir:node:fresh-c63bd239749f5f4d-directory-user-ref */ directoryUser };
            })();
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-c63bd239749f5f4d-found */ { ok: /* ir:node:fresh-c63bd239749f5f4d-user-ref */ user };
        })());
  })();
}
