// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAecc562249b742162(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-ecc562249b742162-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-ecc562249b742162-normalizer */ (/* ir:node:fresh-ecc562249b742162-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-ecc562249b742162-validation */ (/* ir:node:fresh-ecc562249b742162-is-empty */ (/* ir:node:fresh-ecc562249b742162-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-ecc562249b742162-invalid */ { error: /* ir:node:fresh-ecc562249b742162-invalid-code */ "invalid_input_ecc562249b742162" })
      : (/* ir:node:fresh-ecc562249b742162-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-ecc562249b742162-get-user */ capabilities.users.getById(/* ir:node:fresh-ecc562249b742162-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-ecc562249b742162-missing */ { error: /* ir:node:fresh-ecc562249b742162-missing-code */ "not_found_ecc562249b742162" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-ecc562249b742162-found */ { ok: /* ir:node:fresh-ecc562249b742162-user-ref */ user };
        })());
  })();
}
