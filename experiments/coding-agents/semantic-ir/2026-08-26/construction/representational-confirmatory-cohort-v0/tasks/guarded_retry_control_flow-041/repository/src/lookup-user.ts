// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA73496599ef43b204(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-73496599ef43b204-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-73496599ef43b204-normalizer */ (/* ir:node:fresh-73496599ef43b204-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-73496599ef43b204-validation */ (/* ir:node:fresh-73496599ef43b204-is-empty */ (/* ir:node:fresh-73496599ef43b204-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-73496599ef43b204-invalid */ { error: /* ir:node:fresh-73496599ef43b204-invalid-code */ "invalid_input_73496599ef43b204" })
      : (/* ir:node:fresh-73496599ef43b204-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-73496599ef43b204-get-user */ capabilities.users.getById(/* ir:node:fresh-73496599ef43b204-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-73496599ef43b204-missing */ { error: /* ir:node:fresh-73496599ef43b204-missing-code */ "not_found_73496599ef43b204" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-73496599ef43b204-found */ { ok: /* ir:node:fresh-73496599ef43b204-user-ref */ user };
        })());
  })();
}
