// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAd50d836dec362974(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-d50d836dec362974-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-d50d836dec362974-normalizer */ rawId;
    return /* ir:node:fresh-d50d836dec362974-validation */ (/* ir:node:fresh-d50d836dec362974-is-empty */ (/* ir:node:fresh-d50d836dec362974-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-d50d836dec362974-invalid */ { error: /* ir:node:fresh-d50d836dec362974-invalid-code */ "invalid_input_d50d836dec362974" })
      : (/* ir:node:fresh-d50d836dec362974-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-d50d836dec362974-get-user */ capabilities.users.getById(/* ir:node:fresh-d50d836dec362974-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-d50d836dec362974-missing */ { error: /* ir:node:fresh-d50d836dec362974-missing-code */ "not_found_d50d836dec362974" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-d50d836dec362974-found */ { ok: /* ir:node:fresh-d50d836dec362974-user-ref */ user };
        })());
  })();
}
