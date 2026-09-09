// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA1afdad067eab3e0d(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-1afdad067eab3e0d-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-1afdad067eab3e0d-normalizer */ (/* ir:node:fresh-1afdad067eab3e0d-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-1afdad067eab3e0d-validation */ (/* ir:node:fresh-1afdad067eab3e0d-is-empty */ (/* ir:node:fresh-1afdad067eab3e0d-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-1afdad067eab3e0d-invalid */ { error: /* ir:node:fresh-1afdad067eab3e0d-invalid-code */ "invalid_input_1afdad067eab3e0d" })
      : (/* ir:node:fresh-1afdad067eab3e0d-user-match */ (/* ir:node:fresh-1afdad067eab3e0d-reserved-equals */ (/* ir:node:fresh-1afdad067eab3e0d-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-1afdad067eab3e0d-reserved-literal */ "reserved-1afdad06"))
          ? (/* ir:node:fresh-1afdad067eab3e0d-reserved-error */ { error: /* ir:node:fresh-1afdad067eab3e0d-reserved-error-code */ "reserved_identifier_1afdad06" })
          : (/* ir:node:fresh-1afdad067eab3e0d-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-1afdad067eab3e0d-get-user */ capabilities.users.getById(/* ir:node:fresh-1afdad067eab3e0d-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-1afdad067eab3e0d-missing */ { error: /* ir:node:fresh-1afdad067eab3e0d-missing-code */ "not_found_1afdad067eab3e0d" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-1afdad067eab3e0d-found */ { ok: /* ir:node:fresh-1afdad067eab3e0d-user-ref */ user };
            })()));
  })();
}
