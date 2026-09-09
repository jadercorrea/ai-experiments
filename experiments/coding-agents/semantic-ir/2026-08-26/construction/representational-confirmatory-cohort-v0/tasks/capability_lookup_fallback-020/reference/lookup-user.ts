// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
  directory: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA712d4f0470b2d817(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-712d4f0470b2d817-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-712d4f0470b2d817-normalizer */ (/* ir:node:fresh-712d4f0470b2d817-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-712d4f0470b2d817-validation */ (/* ir:node:fresh-712d4f0470b2d817-is-empty */ (/* ir:node:fresh-712d4f0470b2d817-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-712d4f0470b2d817-invalid */ { error: /* ir:node:fresh-712d4f0470b2d817-invalid-code */ "invalid_input_712d4f0470b2d817" })
      : (/* ir:node:fresh-712d4f0470b2d817-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-712d4f0470b2d817-get-user */ capabilities.users.getById(/* ir:node:fresh-712d4f0470b2d817-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-712d4f0470b2d817-directory-match */ (() => {
              const __semantic_ir_option_2 = /* ir:node:fresh-712d4f0470b2d817-get-directory-user */ capabilities.directory.getById(/* ir:node:fresh-712d4f0470b2d817-identifier-for-directory */ normalizedId);
              if (__semantic_ir_option_2 === undefined) {
                return /* ir:node:fresh-712d4f0470b2d817-missing */ { error: /* ir:node:fresh-712d4f0470b2d817-missing-code */ "not_found_712d4f0470b2d817" };
              }
              const directoryUser: User = __semantic_ir_option_2;
              return /* ir:node:fresh-712d4f0470b2d817-directory-found */ { ok: /* ir:node:fresh-712d4f0470b2d817-directory-user-ref */ directoryUser };
            })();
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-712d4f0470b2d817-found */ { ok: /* ir:node:fresh-712d4f0470b2d817-user-ref */ user };
        })());
  })();
}
