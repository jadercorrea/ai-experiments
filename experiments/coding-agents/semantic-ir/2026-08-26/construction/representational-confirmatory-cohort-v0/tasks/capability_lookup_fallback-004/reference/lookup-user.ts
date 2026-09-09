// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
  directory: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA8ae959dd212e7b59(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-8ae959dd212e7b59-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-8ae959dd212e7b59-normalizer */ (/* ir:node:fresh-8ae959dd212e7b59-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-8ae959dd212e7b59-validation */ (/* ir:node:fresh-8ae959dd212e7b59-is-empty */ (/* ir:node:fresh-8ae959dd212e7b59-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-8ae959dd212e7b59-invalid */ { error: /* ir:node:fresh-8ae959dd212e7b59-invalid-code */ "invalid_input_8ae959dd212e7b59" })
      : (/* ir:node:fresh-8ae959dd212e7b59-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-8ae959dd212e7b59-get-user */ capabilities.users.getById(/* ir:node:fresh-8ae959dd212e7b59-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-8ae959dd212e7b59-directory-match */ (() => {
              const __semantic_ir_option_2 = /* ir:node:fresh-8ae959dd212e7b59-get-directory-user */ capabilities.directory.getById(/* ir:node:fresh-8ae959dd212e7b59-identifier-for-directory */ normalizedId);
              if (__semantic_ir_option_2 === undefined) {
                return /* ir:node:fresh-8ae959dd212e7b59-missing */ { error: /* ir:node:fresh-8ae959dd212e7b59-missing-code */ "not_found_8ae959dd212e7b59" };
              }
              const directoryUser: User = __semantic_ir_option_2;
              return /* ir:node:fresh-8ae959dd212e7b59-directory-found */ { ok: /* ir:node:fresh-8ae959dd212e7b59-directory-user-ref */ directoryUser };
            })();
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-8ae959dd212e7b59-found */ { ok: /* ir:node:fresh-8ae959dd212e7b59-user-ref */ user };
        })());
  })();
}
