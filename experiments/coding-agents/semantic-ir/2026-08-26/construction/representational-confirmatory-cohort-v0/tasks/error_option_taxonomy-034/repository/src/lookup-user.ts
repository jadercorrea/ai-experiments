// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAb8162f682b4db1eb(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-b8162f682b4db1eb-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-b8162f682b4db1eb-normalizer */ (/* ir:node:fresh-b8162f682b4db1eb-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-b8162f682b4db1eb-validation */ (/* ir:node:fresh-b8162f682b4db1eb-is-empty */ (/* ir:node:fresh-b8162f682b4db1eb-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-b8162f682b4db1eb-invalid */ { error: /* ir:node:fresh-b8162f682b4db1eb-invalid-code */ "invalid_input_b8162f682b4db1eb" })
      : (/* ir:node:fresh-b8162f682b4db1eb-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-b8162f682b4db1eb-get-user */ capabilities.users.getById(/* ir:node:fresh-b8162f682b4db1eb-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-b8162f682b4db1eb-missing */ { error: /* ir:node:fresh-b8162f682b4db1eb-missing-code */ "not_found_b8162f682b4db1eb" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-b8162f682b4db1eb-found */ { ok: /* ir:node:fresh-b8162f682b4db1eb-user-ref */ user };
        })());
  })();
}
