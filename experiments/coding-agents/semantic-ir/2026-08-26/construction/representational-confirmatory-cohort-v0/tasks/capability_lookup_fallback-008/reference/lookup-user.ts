// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
  directory: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAd2816a3c4735e140(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-d2816a3c4735e140-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-d2816a3c4735e140-normalizer */ (/* ir:node:fresh-d2816a3c4735e140-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-d2816a3c4735e140-validation */ (/* ir:node:fresh-d2816a3c4735e140-is-empty */ (/* ir:node:fresh-d2816a3c4735e140-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-d2816a3c4735e140-invalid */ { error: /* ir:node:fresh-d2816a3c4735e140-invalid-code */ "invalid_input_d2816a3c4735e140" })
      : (/* ir:node:fresh-d2816a3c4735e140-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-d2816a3c4735e140-get-user */ capabilities.users.getById(/* ir:node:fresh-d2816a3c4735e140-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-d2816a3c4735e140-directory-match */ (() => {
              const __semantic_ir_option_2 = /* ir:node:fresh-d2816a3c4735e140-get-directory-user */ capabilities.directory.getById(/* ir:node:fresh-d2816a3c4735e140-identifier-for-directory */ normalizedId);
              if (__semantic_ir_option_2 === undefined) {
                return /* ir:node:fresh-d2816a3c4735e140-missing */ { error: /* ir:node:fresh-d2816a3c4735e140-missing-code */ "not_found_d2816a3c4735e140" };
              }
              const directoryUser: User = __semantic_ir_option_2;
              return /* ir:node:fresh-d2816a3c4735e140-directory-found */ { ok: /* ir:node:fresh-d2816a3c4735e140-directory-user-ref */ directoryUser };
            })();
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-d2816a3c4735e140-found */ { ok: /* ir:node:fresh-d2816a3c4735e140-user-ref */ user };
        })());
  })();
}
