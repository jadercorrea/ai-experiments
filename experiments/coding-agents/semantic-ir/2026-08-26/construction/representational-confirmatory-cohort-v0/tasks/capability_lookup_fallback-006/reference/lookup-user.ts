// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
  directory: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA0f399ec07c367dde(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-0f399ec07c367dde-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-0f399ec07c367dde-normalizer */ (/* ir:node:fresh-0f399ec07c367dde-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-0f399ec07c367dde-validation */ (/* ir:node:fresh-0f399ec07c367dde-is-empty */ (/* ir:node:fresh-0f399ec07c367dde-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-0f399ec07c367dde-invalid */ { error: /* ir:node:fresh-0f399ec07c367dde-invalid-code */ "invalid_input_0f399ec07c367dde" })
      : (/* ir:node:fresh-0f399ec07c367dde-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-0f399ec07c367dde-get-user */ capabilities.users.getById(/* ir:node:fresh-0f399ec07c367dde-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-0f399ec07c367dde-directory-match */ (() => {
              const __semantic_ir_option_2 = /* ir:node:fresh-0f399ec07c367dde-get-directory-user */ capabilities.directory.getById(/* ir:node:fresh-0f399ec07c367dde-identifier-for-directory */ normalizedId);
              if (__semantic_ir_option_2 === undefined) {
                return /* ir:node:fresh-0f399ec07c367dde-missing */ { error: /* ir:node:fresh-0f399ec07c367dde-missing-code */ "not_found_0f399ec07c367dde" };
              }
              const directoryUser: User = __semantic_ir_option_2;
              return /* ir:node:fresh-0f399ec07c367dde-directory-found */ { ok: /* ir:node:fresh-0f399ec07c367dde-directory-user-ref */ directoryUser };
            })();
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-0f399ec07c367dde-found */ { ok: /* ir:node:fresh-0f399ec07c367dde-user-ref */ user };
        })());
  })();
}
