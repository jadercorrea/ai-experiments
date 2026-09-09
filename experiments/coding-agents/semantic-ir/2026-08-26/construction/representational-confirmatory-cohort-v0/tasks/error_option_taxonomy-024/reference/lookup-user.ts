// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAad2eda5c39373af1(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-ad2eda5c39373af1-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-ad2eda5c39373af1-normalizer */ (/* ir:node:fresh-ad2eda5c39373af1-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-ad2eda5c39373af1-validation */ (/* ir:node:fresh-ad2eda5c39373af1-is-empty */ (/* ir:node:fresh-ad2eda5c39373af1-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-ad2eda5c39373af1-invalid */ { error: /* ir:node:fresh-ad2eda5c39373af1-invalid-code */ "empty_identifier_ad2eda5c39373af1" })
      : (/* ir:node:fresh-ad2eda5c39373af1-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-ad2eda5c39373af1-get-user */ capabilities.users.getById(/* ir:node:fresh-ad2eda5c39373af1-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-ad2eda5c39373af1-missing */ { error: /* ir:node:fresh-ad2eda5c39373af1-missing-code */ "unknown_user_ad2eda5c39373af1" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-ad2eda5c39373af1-found */ { ok: /* ir:node:fresh-ad2eda5c39373af1-user-ref */ user };
        })());
  })();
}
