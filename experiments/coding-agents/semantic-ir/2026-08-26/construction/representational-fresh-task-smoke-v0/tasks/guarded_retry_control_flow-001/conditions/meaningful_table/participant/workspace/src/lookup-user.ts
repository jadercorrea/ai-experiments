// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAd1096c48c01ec6e6(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-d1096c48c01ec6e6-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-d1096c48c01ec6e6-normalizer */ (/* ir:node:fresh-d1096c48c01ec6e6-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-d1096c48c01ec6e6-validation */ (/* ir:node:fresh-d1096c48c01ec6e6-is-empty */ (/* ir:node:fresh-d1096c48c01ec6e6-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-d1096c48c01ec6e6-invalid */ { error: /* ir:node:fresh-d1096c48c01ec6e6-invalid-code */ "invalid_input_d1096c48c01ec6e6" })
      : (/* ir:node:fresh-d1096c48c01ec6e6-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-d1096c48c01ec6e6-get-user */ capabilities.users.getById(/* ir:node:fresh-d1096c48c01ec6e6-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-d1096c48c01ec6e6-missing */ { error: /* ir:node:fresh-d1096c48c01ec6e6-missing-code */ "not_found_d1096c48c01ec6e6" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-d1096c48c01ec6e6-found */ { ok: /* ir:node:fresh-d1096c48c01ec6e6-user-ref */ user };
        })());
  })();
}
