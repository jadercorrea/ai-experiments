// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA8e22082951cf97d8(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-8e22082951cf97d8-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-8e22082951cf97d8-normalizer */ (/* ir:node:fresh-8e22082951cf97d8-raw-after-normalization-patch */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-8e22082951cf97d8-validation */ (/* ir:node:fresh-8e22082951cf97d8-is-empty */ (/* ir:node:fresh-8e22082951cf97d8-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-8e22082951cf97d8-invalid */ { error: /* ir:node:fresh-8e22082951cf97d8-invalid-code */ "invalid_input_8e22082951cf97d8" })
      : (/* ir:node:fresh-8e22082951cf97d8-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-8e22082951cf97d8-get-user */ capabilities.users.getById(/* ir:node:fresh-8e22082951cf97d8-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-8e22082951cf97d8-missing */ { error: /* ir:node:fresh-8e22082951cf97d8-missing-code */ "not_found_8e22082951cf97d8" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-8e22082951cf97d8-found */ { ok: /* ir:node:fresh-8e22082951cf97d8-user-ref */ user };
        })());
  })();
}
