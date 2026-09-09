// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA53c1a1b8d518f1fd(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-53c1a1b8d518f1fd-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-53c1a1b8d518f1fd-normalizer */ (/* ir:node:fresh-53c1a1b8d518f1fd-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-53c1a1b8d518f1fd-validation */ (/* ir:node:fresh-53c1a1b8d518f1fd-is-empty */ (/* ir:node:fresh-53c1a1b8d518f1fd-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-53c1a1b8d518f1fd-invalid */ { error: /* ir:node:fresh-53c1a1b8d518f1fd-invalid-code */ "invalid_input_53c1a1b8d518f1fd" })
      : (/* ir:node:fresh-53c1a1b8d518f1fd-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-53c1a1b8d518f1fd-get-user */ capabilities.users.getById(/* ir:node:fresh-53c1a1b8d518f1fd-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-53c1a1b8d518f1fd-missing */ { error: /* ir:node:fresh-53c1a1b8d518f1fd-missing-code */ "not_found_53c1a1b8d518f1fd" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-53c1a1b8d518f1fd-found */ { ok: /* ir:node:fresh-53c1a1b8d518f1fd-user-ref */ user };
        })());
  })();
}
