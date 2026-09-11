// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA942e2fb865b3fa81(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-942e2fb865b3fa81-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-942e2fb865b3fa81-normalizer */ (/* ir:node:fresh-942e2fb865b3fa81-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-942e2fb865b3fa81-validation */ (/* ir:node:fresh-942e2fb865b3fa81-is-empty */ (/* ir:node:fresh-942e2fb865b3fa81-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-942e2fb865b3fa81-invalid */ { error: /* ir:node:fresh-942e2fb865b3fa81-invalid-code */ "invalid_input_942e2fb865b3fa81" })
      : (/* ir:node:fresh-942e2fb865b3fa81-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-942e2fb865b3fa81-get-user */ capabilities.users.getById(/* ir:node:fresh-942e2fb865b3fa81-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-942e2fb865b3fa81-missing */ { error: /* ir:node:fresh-942e2fb865b3fa81-missing-code */ "not_found_942e2fb865b3fa81" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-942e2fb865b3fa81-found */ { ok: /* ir:node:fresh-942e2fb865b3fa81-user-ref */ user };
        })());
  })();
}
