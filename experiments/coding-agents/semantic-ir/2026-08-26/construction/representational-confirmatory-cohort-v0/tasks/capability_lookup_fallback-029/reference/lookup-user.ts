// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
  directory: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA022fe552ea402daa(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-022fe552ea402daa-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-022fe552ea402daa-normalizer */ (/* ir:node:fresh-022fe552ea402daa-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-022fe552ea402daa-validation */ (/* ir:node:fresh-022fe552ea402daa-is-empty */ (/* ir:node:fresh-022fe552ea402daa-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-022fe552ea402daa-invalid */ { error: /* ir:node:fresh-022fe552ea402daa-invalid-code */ "invalid_input_022fe552ea402daa" })
      : (/* ir:node:fresh-022fe552ea402daa-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-022fe552ea402daa-get-user */ capabilities.users.getById(/* ir:node:fresh-022fe552ea402daa-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-022fe552ea402daa-directory-match */ (() => {
              const __semantic_ir_option_2 = /* ir:node:fresh-022fe552ea402daa-get-directory-user */ capabilities.directory.getById(/* ir:node:fresh-022fe552ea402daa-identifier-for-directory */ rawId);
              if (__semantic_ir_option_2 === undefined) {
                return /* ir:node:fresh-022fe552ea402daa-missing */ { error: /* ir:node:fresh-022fe552ea402daa-missing-code */ "not_found_022fe552ea402daa" };
              }
              const directoryUser: User = __semantic_ir_option_2;
              return /* ir:node:fresh-022fe552ea402daa-directory-found */ { ok: /* ir:node:fresh-022fe552ea402daa-directory-user-ref */ directoryUser };
            })();
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-022fe552ea402daa-found */ { ok: /* ir:node:fresh-022fe552ea402daa-user-ref */ user };
        })());
  })();
}
