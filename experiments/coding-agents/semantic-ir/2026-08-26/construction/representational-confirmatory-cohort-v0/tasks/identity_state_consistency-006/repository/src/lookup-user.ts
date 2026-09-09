// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA9bf427349b1c322a(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-9bf427349b1c322a-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-9bf427349b1c322a-normalizer */ (/* ir:node:fresh-9bf427349b1c322a-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-9bf427349b1c322a-validation */ (/* ir:node:fresh-9bf427349b1c322a-is-empty */ (/* ir:node:fresh-9bf427349b1c322a-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-9bf427349b1c322a-invalid */ { error: /* ir:node:fresh-9bf427349b1c322a-invalid-code */ "invalid_input_9bf427349b1c322a" })
      : (/* ir:node:fresh-9bf427349b1c322a-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-9bf427349b1c322a-get-user */ capabilities.users.getById(/* ir:node:fresh-9bf427349b1c322a-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-9bf427349b1c322a-missing */ { error: /* ir:node:fresh-9bf427349b1c322a-missing-code */ "not_found_9bf427349b1c322a" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-9bf427349b1c322a-found */ { ok: /* ir:node:fresh-9bf427349b1c322a-user-ref */ user };
        })());
  })();
}
