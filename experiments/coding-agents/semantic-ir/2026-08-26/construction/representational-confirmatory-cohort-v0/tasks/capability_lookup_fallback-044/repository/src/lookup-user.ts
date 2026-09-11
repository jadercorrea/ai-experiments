// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAfcb935bd2517224a(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-fcb935bd2517224a-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-fcb935bd2517224a-normalizer */ (/* ir:node:fresh-fcb935bd2517224a-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-fcb935bd2517224a-validation */ (/* ir:node:fresh-fcb935bd2517224a-is-empty */ (/* ir:node:fresh-fcb935bd2517224a-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-fcb935bd2517224a-invalid */ { error: /* ir:node:fresh-fcb935bd2517224a-invalid-code */ "invalid_input_fcb935bd2517224a" })
      : (/* ir:node:fresh-fcb935bd2517224a-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-fcb935bd2517224a-get-user */ capabilities.users.getById(/* ir:node:fresh-fcb935bd2517224a-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-fcb935bd2517224a-missing */ { error: /* ir:node:fresh-fcb935bd2517224a-missing-code */ "not_found_fcb935bd2517224a" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-fcb935bd2517224a-found */ { ok: /* ir:node:fresh-fcb935bd2517224a-user-ref */ user };
        })());
  })();
}
