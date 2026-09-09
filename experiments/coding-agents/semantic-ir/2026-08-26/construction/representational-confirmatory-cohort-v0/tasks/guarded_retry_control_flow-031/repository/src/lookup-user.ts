// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA0979fee1bb963267(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-0979fee1bb963267-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-0979fee1bb963267-normalizer */ (/* ir:node:fresh-0979fee1bb963267-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-0979fee1bb963267-validation */ (/* ir:node:fresh-0979fee1bb963267-is-empty */ (/* ir:node:fresh-0979fee1bb963267-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-0979fee1bb963267-invalid */ { error: /* ir:node:fresh-0979fee1bb963267-invalid-code */ "invalid_input_0979fee1bb963267" })
      : (/* ir:node:fresh-0979fee1bb963267-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-0979fee1bb963267-get-user */ capabilities.users.getById(/* ir:node:fresh-0979fee1bb963267-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-0979fee1bb963267-missing */ { error: /* ir:node:fresh-0979fee1bb963267-missing-code */ "not_found_0979fee1bb963267" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-0979fee1bb963267-found */ { ok: /* ir:node:fresh-0979fee1bb963267-user-ref */ user };
        })());
  })();
}
