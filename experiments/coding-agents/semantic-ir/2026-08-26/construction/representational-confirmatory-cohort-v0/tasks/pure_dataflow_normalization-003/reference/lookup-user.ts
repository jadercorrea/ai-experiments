// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA6a76cd75b5dfb053(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-6a76cd75b5dfb053-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-6a76cd75b5dfb053-normalizer */ (/* ir:node:fresh-6a76cd75b5dfb053-raw-after-normalization-patch */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-6a76cd75b5dfb053-validation */ (/* ir:node:fresh-6a76cd75b5dfb053-is-empty */ (/* ir:node:fresh-6a76cd75b5dfb053-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-6a76cd75b5dfb053-invalid */ { error: /* ir:node:fresh-6a76cd75b5dfb053-invalid-code */ "invalid_input_6a76cd75b5dfb053" })
      : (/* ir:node:fresh-6a76cd75b5dfb053-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-6a76cd75b5dfb053-get-user */ capabilities.users.getById(/* ir:node:fresh-6a76cd75b5dfb053-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-6a76cd75b5dfb053-missing */ { error: /* ir:node:fresh-6a76cd75b5dfb053-missing-code */ "not_found_6a76cd75b5dfb053" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-6a76cd75b5dfb053-found */ { ok: /* ir:node:fresh-6a76cd75b5dfb053-user-ref */ user };
        })());
  })();
}
