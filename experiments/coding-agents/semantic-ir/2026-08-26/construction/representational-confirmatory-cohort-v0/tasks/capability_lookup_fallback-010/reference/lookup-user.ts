// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
  directory: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAc38019fbd742d04b(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-c38019fbd742d04b-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-c38019fbd742d04b-normalizer */ (/* ir:node:fresh-c38019fbd742d04b-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-c38019fbd742d04b-validation */ (/* ir:node:fresh-c38019fbd742d04b-is-empty */ (/* ir:node:fresh-c38019fbd742d04b-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-c38019fbd742d04b-invalid */ { error: /* ir:node:fresh-c38019fbd742d04b-invalid-code */ "invalid_input_c38019fbd742d04b" })
      : (/* ir:node:fresh-c38019fbd742d04b-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-c38019fbd742d04b-get-user */ capabilities.users.getById(/* ir:node:fresh-c38019fbd742d04b-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-c38019fbd742d04b-directory-match */ (() => {
              const __semantic_ir_option_2 = /* ir:node:fresh-c38019fbd742d04b-get-directory-user */ capabilities.directory.getById(/* ir:node:fresh-c38019fbd742d04b-identifier-for-directory */ rawId);
              if (__semantic_ir_option_2 === undefined) {
                return /* ir:node:fresh-c38019fbd742d04b-missing */ { error: /* ir:node:fresh-c38019fbd742d04b-missing-code */ "not_found_c38019fbd742d04b" };
              }
              const directoryUser: User = __semantic_ir_option_2;
              return /* ir:node:fresh-c38019fbd742d04b-directory-found */ { ok: /* ir:node:fresh-c38019fbd742d04b-directory-user-ref */ directoryUser };
            })();
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-c38019fbd742d04b-found */ { ok: /* ir:node:fresh-c38019fbd742d04b-user-ref */ user };
        })());
  })();
}
