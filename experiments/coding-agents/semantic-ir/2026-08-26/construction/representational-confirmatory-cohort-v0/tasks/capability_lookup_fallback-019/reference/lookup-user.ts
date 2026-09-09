// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
  directory: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA126c76386a7df64f(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-126c76386a7df64f-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-126c76386a7df64f-normalizer */ (/* ir:node:fresh-126c76386a7df64f-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-126c76386a7df64f-validation */ (/* ir:node:fresh-126c76386a7df64f-is-empty */ (/* ir:node:fresh-126c76386a7df64f-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-126c76386a7df64f-invalid */ { error: /* ir:node:fresh-126c76386a7df64f-invalid-code */ "invalid_input_126c76386a7df64f" })
      : (/* ir:node:fresh-126c76386a7df64f-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-126c76386a7df64f-get-user */ capabilities.users.getById(/* ir:node:fresh-126c76386a7df64f-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-126c76386a7df64f-directory-match */ (() => {
              const __semantic_ir_option_2 = /* ir:node:fresh-126c76386a7df64f-get-directory-user */ capabilities.directory.getById(/* ir:node:fresh-126c76386a7df64f-identifier-for-directory */ normalizedId);
              if (__semantic_ir_option_2 === undefined) {
                return /* ir:node:fresh-126c76386a7df64f-missing */ { error: /* ir:node:fresh-126c76386a7df64f-missing-code */ "not_found_126c76386a7df64f" };
              }
              const directoryUser: User = __semantic_ir_option_2;
              return /* ir:node:fresh-126c76386a7df64f-directory-found */ { ok: /* ir:node:fresh-126c76386a7df64f-directory-user-ref */ directoryUser };
            })();
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-126c76386a7df64f-found */ { ok: /* ir:node:fresh-126c76386a7df64f-user-ref */ user };
        })());
  })();
}
