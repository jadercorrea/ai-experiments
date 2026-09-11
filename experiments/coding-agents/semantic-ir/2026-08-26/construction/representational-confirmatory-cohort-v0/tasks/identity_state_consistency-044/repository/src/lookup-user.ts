// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAca1f028b59fda123(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-ca1f028b59fda123-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-ca1f028b59fda123-normalizer */ (/* ir:node:fresh-ca1f028b59fda123-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-ca1f028b59fda123-validation */ (/* ir:node:fresh-ca1f028b59fda123-is-empty */ (/* ir:node:fresh-ca1f028b59fda123-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-ca1f028b59fda123-invalid */ { error: /* ir:node:fresh-ca1f028b59fda123-invalid-code */ "invalid_input_ca1f028b59fda123" })
      : (/* ir:node:fresh-ca1f028b59fda123-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-ca1f028b59fda123-get-user */ capabilities.users.getById(/* ir:node:fresh-ca1f028b59fda123-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-ca1f028b59fda123-missing */ { error: /* ir:node:fresh-ca1f028b59fda123-missing-code */ "not_found_ca1f028b59fda123" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-ca1f028b59fda123-found */ { ok: /* ir:node:fresh-ca1f028b59fda123-user-ref */ user };
        })());
  })();
}
