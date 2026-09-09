// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAbd9eebff3bf94707(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-bd9eebff3bf94707-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-bd9eebff3bf94707-normalizer */ (/* ir:node:fresh-bd9eebff3bf94707-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-bd9eebff3bf94707-validation */ (/* ir:node:fresh-bd9eebff3bf94707-is-empty */ (/* ir:node:fresh-bd9eebff3bf94707-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-bd9eebff3bf94707-invalid */ { error: /* ir:node:fresh-bd9eebff3bf94707-invalid-code */ "empty_identifier_bd9eebff3bf94707" })
      : (/* ir:node:fresh-bd9eebff3bf94707-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-bd9eebff3bf94707-get-user */ capabilities.users.getById(/* ir:node:fresh-bd9eebff3bf94707-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-bd9eebff3bf94707-missing */ { error: /* ir:node:fresh-bd9eebff3bf94707-missing-code */ "unknown_user_bd9eebff3bf94707" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-bd9eebff3bf94707-found */ { ok: /* ir:node:fresh-bd9eebff3bf94707-user-ref */ user };
        })());
  })();
}
