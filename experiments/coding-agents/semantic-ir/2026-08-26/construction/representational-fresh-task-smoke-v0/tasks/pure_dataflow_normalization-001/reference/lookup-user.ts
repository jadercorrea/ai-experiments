// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAf238ecac0f8db33c(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-f238ecac0f8db33c-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-f238ecac0f8db33c-normalizer */ (/* ir:node:fresh-f238ecac0f8db33c-raw-after-normalization-patch */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-f238ecac0f8db33c-validation */ (/* ir:node:fresh-f238ecac0f8db33c-is-empty */ (/* ir:node:fresh-f238ecac0f8db33c-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-f238ecac0f8db33c-invalid */ { error: /* ir:node:fresh-f238ecac0f8db33c-invalid-code */ "invalid_input_f238ecac0f8db33c" })
      : (/* ir:node:fresh-f238ecac0f8db33c-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-f238ecac0f8db33c-get-user */ capabilities.users.getById(/* ir:node:fresh-f238ecac0f8db33c-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-f238ecac0f8db33c-missing */ { error: /* ir:node:fresh-f238ecac0f8db33c-missing-code */ "not_found_f238ecac0f8db33c" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-f238ecac0f8db33c-found */ { ok: /* ir:node:fresh-f238ecac0f8db33c-user-ref */ user };
        })());
  })();
}
