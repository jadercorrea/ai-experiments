// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAf2031407aa98b9a5(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-f2031407aa98b9a5-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-f2031407aa98b9a5-normalizer */ (/* ir:node:fresh-f2031407aa98b9a5-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-f2031407aa98b9a5-validation */ (/* ir:node:fresh-f2031407aa98b9a5-is-empty */ (/* ir:node:fresh-f2031407aa98b9a5-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-f2031407aa98b9a5-invalid */ { error: /* ir:node:fresh-f2031407aa98b9a5-invalid-code */ "invalid_input_f2031407aa98b9a5" })
      : (/* ir:node:fresh-f2031407aa98b9a5-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-f2031407aa98b9a5-get-user */ capabilities.users.getById(/* ir:node:fresh-f2031407aa98b9a5-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-f2031407aa98b9a5-missing */ { error: /* ir:node:fresh-f2031407aa98b9a5-missing-code */ "not_found_f2031407aa98b9a5" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-f2031407aa98b9a5-found */ { ok: /* ir:node:fresh-f2031407aa98b9a5-user-ref */ user };
        })());
  })();
}
