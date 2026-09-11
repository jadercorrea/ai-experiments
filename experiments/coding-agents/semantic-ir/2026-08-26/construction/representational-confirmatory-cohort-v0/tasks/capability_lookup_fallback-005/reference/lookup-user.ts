// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
  directory: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAfbacfcb7658536a0(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-fbacfcb7658536a0-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-fbacfcb7658536a0-normalizer */ (/* ir:node:fresh-fbacfcb7658536a0-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-fbacfcb7658536a0-validation */ (/* ir:node:fresh-fbacfcb7658536a0-is-empty */ (/* ir:node:fresh-fbacfcb7658536a0-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-fbacfcb7658536a0-invalid */ { error: /* ir:node:fresh-fbacfcb7658536a0-invalid-code */ "invalid_input_fbacfcb7658536a0" })
      : (/* ir:node:fresh-fbacfcb7658536a0-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-fbacfcb7658536a0-get-user */ capabilities.users.getById(/* ir:node:fresh-fbacfcb7658536a0-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-fbacfcb7658536a0-directory-match */ (() => {
              const __semantic_ir_option_2 = /* ir:node:fresh-fbacfcb7658536a0-get-directory-user */ capabilities.directory.getById(/* ir:node:fresh-fbacfcb7658536a0-identifier-for-directory */ normalizedId);
              if (__semantic_ir_option_2 === undefined) {
                return /* ir:node:fresh-fbacfcb7658536a0-missing */ { error: /* ir:node:fresh-fbacfcb7658536a0-missing-code */ "not_found_fbacfcb7658536a0" };
              }
              const directoryUser: User = __semantic_ir_option_2;
              return /* ir:node:fresh-fbacfcb7658536a0-directory-found */ { ok: /* ir:node:fresh-fbacfcb7658536a0-directory-user-ref */ directoryUser };
            })();
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-fbacfcb7658536a0-found */ { ok: /* ir:node:fresh-fbacfcb7658536a0-user-ref */ user };
        })());
  })();
}
