// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
  directory: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA59fcda8c0421037b(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-59fcda8c0421037b-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-59fcda8c0421037b-normalizer */ (/* ir:node:fresh-59fcda8c0421037b-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-59fcda8c0421037b-validation */ (/* ir:node:fresh-59fcda8c0421037b-is-empty */ (/* ir:node:fresh-59fcda8c0421037b-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-59fcda8c0421037b-invalid */ { error: /* ir:node:fresh-59fcda8c0421037b-invalid-code */ "invalid_input_59fcda8c0421037b" })
      : (/* ir:node:fresh-59fcda8c0421037b-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-59fcda8c0421037b-get-user */ capabilities.users.getById(/* ir:node:fresh-59fcda8c0421037b-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-59fcda8c0421037b-directory-match */ (() => {
              const __semantic_ir_option_2 = /* ir:node:fresh-59fcda8c0421037b-get-directory-user */ capabilities.directory.getById(/* ir:node:fresh-59fcda8c0421037b-identifier-for-directory */ normalizedId);
              if (__semantic_ir_option_2 === undefined) {
                return /* ir:node:fresh-59fcda8c0421037b-missing */ { error: /* ir:node:fresh-59fcda8c0421037b-missing-code */ "not_found_59fcda8c0421037b" };
              }
              const directoryUser: User = __semantic_ir_option_2;
              return /* ir:node:fresh-59fcda8c0421037b-directory-found */ { ok: /* ir:node:fresh-59fcda8c0421037b-directory-user-ref */ directoryUser };
            })();
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-59fcda8c0421037b-found */ { ok: /* ir:node:fresh-59fcda8c0421037b-user-ref */ user };
        })());
  })();
}
