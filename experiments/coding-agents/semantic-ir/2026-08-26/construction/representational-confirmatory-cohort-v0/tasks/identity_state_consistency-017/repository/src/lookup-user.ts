// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAf60b559cf864e2c4(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-f60b559cf864e2c4-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-f60b559cf864e2c4-normalizer */ (/* ir:node:fresh-f60b559cf864e2c4-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-f60b559cf864e2c4-validation */ (/* ir:node:fresh-f60b559cf864e2c4-is-empty */ (/* ir:node:fresh-f60b559cf864e2c4-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-f60b559cf864e2c4-invalid */ { error: /* ir:node:fresh-f60b559cf864e2c4-invalid-code */ "invalid_input_f60b559cf864e2c4" })
      : (/* ir:node:fresh-f60b559cf864e2c4-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-f60b559cf864e2c4-get-user */ capabilities.users.getById(/* ir:node:fresh-f60b559cf864e2c4-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-f60b559cf864e2c4-missing */ { error: /* ir:node:fresh-f60b559cf864e2c4-missing-code */ "not_found_f60b559cf864e2c4" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-f60b559cf864e2c4-found */ { ok: /* ir:node:fresh-f60b559cf864e2c4-user-ref */ user };
        })());
  })();
}
