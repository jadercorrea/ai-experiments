// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
  directory: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAe6afe822adb4f7ad(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-e6afe822adb4f7ad-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-e6afe822adb4f7ad-normalizer */ (/* ir:node:fresh-e6afe822adb4f7ad-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-e6afe822adb4f7ad-validation */ (/* ir:node:fresh-e6afe822adb4f7ad-is-empty */ (/* ir:node:fresh-e6afe822adb4f7ad-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-e6afe822adb4f7ad-invalid */ { error: /* ir:node:fresh-e6afe822adb4f7ad-invalid-code */ "invalid_input_e6afe822adb4f7ad" })
      : (/* ir:node:fresh-e6afe822adb4f7ad-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-e6afe822adb4f7ad-get-user */ capabilities.users.getById(/* ir:node:fresh-e6afe822adb4f7ad-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-e6afe822adb4f7ad-directory-match */ (() => {
              const __semantic_ir_option_2 = /* ir:node:fresh-e6afe822adb4f7ad-get-directory-user */ capabilities.directory.getById(/* ir:node:fresh-e6afe822adb4f7ad-identifier-for-directory */ rawId);
              if (__semantic_ir_option_2 === undefined) {
                return /* ir:node:fresh-e6afe822adb4f7ad-missing */ { error: /* ir:node:fresh-e6afe822adb4f7ad-missing-code */ "not_found_e6afe822adb4f7ad" };
              }
              const directoryUser: User = __semantic_ir_option_2;
              return /* ir:node:fresh-e6afe822adb4f7ad-directory-found */ { ok: /* ir:node:fresh-e6afe822adb4f7ad-directory-user-ref */ directoryUser };
            })();
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-e6afe822adb4f7ad-found */ { ok: /* ir:node:fresh-e6afe822adb4f7ad-user-ref */ user };
        })());
  })();
}
