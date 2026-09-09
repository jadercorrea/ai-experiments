// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
  directory: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA1e56ace3123bffb3(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-1e56ace3123bffb3-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-1e56ace3123bffb3-normalizer */ (/* ir:node:fresh-1e56ace3123bffb3-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-1e56ace3123bffb3-validation */ (/* ir:node:fresh-1e56ace3123bffb3-is-empty */ (/* ir:node:fresh-1e56ace3123bffb3-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-1e56ace3123bffb3-invalid */ { error: /* ir:node:fresh-1e56ace3123bffb3-invalid-code */ "invalid_input_1e56ace3123bffb3" })
      : (/* ir:node:fresh-1e56ace3123bffb3-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-1e56ace3123bffb3-get-user */ capabilities.users.getById(/* ir:node:fresh-1e56ace3123bffb3-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-1e56ace3123bffb3-directory-match */ (() => {
              const __semantic_ir_option_2 = /* ir:node:fresh-1e56ace3123bffb3-get-directory-user */ capabilities.directory.getById(/* ir:node:fresh-1e56ace3123bffb3-identifier-for-directory */ normalizedId);
              if (__semantic_ir_option_2 === undefined) {
                return /* ir:node:fresh-1e56ace3123bffb3-missing */ { error: /* ir:node:fresh-1e56ace3123bffb3-missing-code */ "not_found_1e56ace3123bffb3" };
              }
              const directoryUser: User = __semantic_ir_option_2;
              return /* ir:node:fresh-1e56ace3123bffb3-directory-found */ { ok: /* ir:node:fresh-1e56ace3123bffb3-directory-user-ref */ directoryUser };
            })();
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-1e56ace3123bffb3-found */ { ok: /* ir:node:fresh-1e56ace3123bffb3-user-ref */ user };
        })());
  })();
}
