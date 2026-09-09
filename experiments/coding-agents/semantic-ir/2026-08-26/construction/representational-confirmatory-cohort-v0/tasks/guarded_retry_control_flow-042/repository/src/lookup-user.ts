// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA4fe504cbda17ce6e(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-4fe504cbda17ce6e-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-4fe504cbda17ce6e-normalizer */ (/* ir:node:fresh-4fe504cbda17ce6e-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-4fe504cbda17ce6e-validation */ (/* ir:node:fresh-4fe504cbda17ce6e-is-empty */ (/* ir:node:fresh-4fe504cbda17ce6e-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-4fe504cbda17ce6e-invalid */ { error: /* ir:node:fresh-4fe504cbda17ce6e-invalid-code */ "invalid_input_4fe504cbda17ce6e" })
      : (/* ir:node:fresh-4fe504cbda17ce6e-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-4fe504cbda17ce6e-get-user */ capabilities.users.getById(/* ir:node:fresh-4fe504cbda17ce6e-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-4fe504cbda17ce6e-missing */ { error: /* ir:node:fresh-4fe504cbda17ce6e-missing-code */ "not_found_4fe504cbda17ce6e" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-4fe504cbda17ce6e-found */ { ok: /* ir:node:fresh-4fe504cbda17ce6e-user-ref */ user };
        })());
  })();
}
