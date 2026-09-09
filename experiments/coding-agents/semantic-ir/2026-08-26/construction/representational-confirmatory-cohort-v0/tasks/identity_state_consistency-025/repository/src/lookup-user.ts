// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA0bfc53b4c112e88b(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-0bfc53b4c112e88b-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-0bfc53b4c112e88b-normalizer */ (/* ir:node:fresh-0bfc53b4c112e88b-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-0bfc53b4c112e88b-validation */ (/* ir:node:fresh-0bfc53b4c112e88b-is-empty */ (/* ir:node:fresh-0bfc53b4c112e88b-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-0bfc53b4c112e88b-invalid */ { error: /* ir:node:fresh-0bfc53b4c112e88b-invalid-code */ "invalid_input_0bfc53b4c112e88b" })
      : (/* ir:node:fresh-0bfc53b4c112e88b-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-0bfc53b4c112e88b-get-user */ capabilities.users.getById(/* ir:node:fresh-0bfc53b4c112e88b-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-0bfc53b4c112e88b-missing */ { error: /* ir:node:fresh-0bfc53b4c112e88b-missing-code */ "not_found_0bfc53b4c112e88b" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-0bfc53b4c112e88b-found */ { ok: /* ir:node:fresh-0bfc53b4c112e88b-user-ref */ user };
        })());
  })();
}
