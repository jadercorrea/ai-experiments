// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
  directory: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAeae14f95119af178(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-eae14f95119af178-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-eae14f95119af178-normalizer */ (/* ir:node:fresh-eae14f95119af178-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-eae14f95119af178-validation */ (/* ir:node:fresh-eae14f95119af178-is-empty */ (/* ir:node:fresh-eae14f95119af178-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-eae14f95119af178-invalid */ { error: /* ir:node:fresh-eae14f95119af178-invalid-code */ "invalid_input_eae14f95119af178" })
      : (/* ir:node:fresh-eae14f95119af178-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-eae14f95119af178-get-user */ capabilities.users.getById(/* ir:node:fresh-eae14f95119af178-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-eae14f95119af178-directory-match */ (() => {
              const __semantic_ir_option_2 = /* ir:node:fresh-eae14f95119af178-get-directory-user */ capabilities.directory.getById(/* ir:node:fresh-eae14f95119af178-identifier-for-directory */ rawId);
              if (__semantic_ir_option_2 === undefined) {
                return /* ir:node:fresh-eae14f95119af178-missing */ { error: /* ir:node:fresh-eae14f95119af178-missing-code */ "not_found_eae14f95119af178" };
              }
              const directoryUser: User = __semantic_ir_option_2;
              return /* ir:node:fresh-eae14f95119af178-directory-found */ { ok: /* ir:node:fresh-eae14f95119af178-directory-user-ref */ directoryUser };
            })();
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-eae14f95119af178-found */ { ok: /* ir:node:fresh-eae14f95119af178-user-ref */ user };
        })());
  })();
}
