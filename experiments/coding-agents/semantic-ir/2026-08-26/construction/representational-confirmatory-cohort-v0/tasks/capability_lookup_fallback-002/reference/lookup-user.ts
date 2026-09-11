// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
  directory: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA6ecf91efc91e07ae(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-6ecf91efc91e07ae-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-6ecf91efc91e07ae-normalizer */ (/* ir:node:fresh-6ecf91efc91e07ae-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-6ecf91efc91e07ae-validation */ (/* ir:node:fresh-6ecf91efc91e07ae-is-empty */ (/* ir:node:fresh-6ecf91efc91e07ae-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-6ecf91efc91e07ae-invalid */ { error: /* ir:node:fresh-6ecf91efc91e07ae-invalid-code */ "invalid_input_6ecf91efc91e07ae" })
      : (/* ir:node:fresh-6ecf91efc91e07ae-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-6ecf91efc91e07ae-get-user */ capabilities.users.getById(/* ir:node:fresh-6ecf91efc91e07ae-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-6ecf91efc91e07ae-directory-match */ (() => {
              const __semantic_ir_option_2 = /* ir:node:fresh-6ecf91efc91e07ae-get-directory-user */ capabilities.directory.getById(/* ir:node:fresh-6ecf91efc91e07ae-identifier-for-directory */ normalizedId);
              if (__semantic_ir_option_2 === undefined) {
                return /* ir:node:fresh-6ecf91efc91e07ae-missing */ { error: /* ir:node:fresh-6ecf91efc91e07ae-missing-code */ "not_found_6ecf91efc91e07ae" };
              }
              const directoryUser: User = __semantic_ir_option_2;
              return /* ir:node:fresh-6ecf91efc91e07ae-directory-found */ { ok: /* ir:node:fresh-6ecf91efc91e07ae-directory-user-ref */ directoryUser };
            })();
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-6ecf91efc91e07ae-found */ { ok: /* ir:node:fresh-6ecf91efc91e07ae-user-ref */ user };
        })());
  })();
}
