// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
  directory: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAa6c6bce4180ecdab(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-a6c6bce4180ecdab-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-a6c6bce4180ecdab-normalizer */ (/* ir:node:fresh-a6c6bce4180ecdab-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-a6c6bce4180ecdab-validation */ (/* ir:node:fresh-a6c6bce4180ecdab-is-empty */ (/* ir:node:fresh-a6c6bce4180ecdab-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-a6c6bce4180ecdab-invalid */ { error: /* ir:node:fresh-a6c6bce4180ecdab-invalid-code */ "invalid_input_a6c6bce4180ecdab" })
      : (/* ir:node:fresh-a6c6bce4180ecdab-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-a6c6bce4180ecdab-get-user */ capabilities.users.getById(/* ir:node:fresh-a6c6bce4180ecdab-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-a6c6bce4180ecdab-directory-match */ (() => {
              const __semantic_ir_option_2 = /* ir:node:fresh-a6c6bce4180ecdab-get-directory-user */ capabilities.directory.getById(/* ir:node:fresh-a6c6bce4180ecdab-identifier-for-directory */ normalizedId);
              if (__semantic_ir_option_2 === undefined) {
                return /* ir:node:fresh-a6c6bce4180ecdab-missing */ { error: /* ir:node:fresh-a6c6bce4180ecdab-missing-code */ "not_found_a6c6bce4180ecdab" };
              }
              const directoryUser: User = __semantic_ir_option_2;
              return /* ir:node:fresh-a6c6bce4180ecdab-directory-found */ { ok: /* ir:node:fresh-a6c6bce4180ecdab-directory-user-ref */ directoryUser };
            })();
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-a6c6bce4180ecdab-found */ { ok: /* ir:node:fresh-a6c6bce4180ecdab-user-ref */ user };
        })());
  })();
}
