// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA9d40540b73b3eb21(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-9d40540b73b3eb21-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-9d40540b73b3eb21-normalizer */ (/* ir:node:fresh-9d40540b73b3eb21-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-9d40540b73b3eb21-validation */ (/* ir:node:fresh-9d40540b73b3eb21-is-empty */ (/* ir:node:fresh-9d40540b73b3eb21-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-9d40540b73b3eb21-invalid */ { error: /* ir:node:fresh-9d40540b73b3eb21-invalid-code */ "invalid_input_9d40540b73b3eb21" })
      : (/* ir:node:fresh-9d40540b73b3eb21-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-9d40540b73b3eb21-get-user */ capabilities.users.getById(/* ir:node:fresh-9d40540b73b3eb21-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-9d40540b73b3eb21-missing */ { error: /* ir:node:fresh-9d40540b73b3eb21-missing-code */ "not_found_9d40540b73b3eb21" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-9d40540b73b3eb21-found */ { ok: /* ir:node:fresh-9d40540b73b3eb21-user-ref */ user };
        })());
  })();
}
