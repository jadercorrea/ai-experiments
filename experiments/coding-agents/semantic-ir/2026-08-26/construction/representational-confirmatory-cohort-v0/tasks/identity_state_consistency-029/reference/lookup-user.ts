// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA619358c7d2428a53(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-619358c7d2428a53-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-619358c7d2428a53-normalizer */ (/* ir:node:fresh-619358c7d2428a53-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-619358c7d2428a53-validation */ (/* ir:node:fresh-619358c7d2428a53-is-empty */ (/* ir:node:fresh-619358c7d2428a53-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-619358c7d2428a53-invalid */ { error: /* ir:node:fresh-619358c7d2428a53-invalid-code */ "invalid_input_619358c7d2428a53" })
      : (/* ir:node:fresh-619358c7d2428a53-user-match */ (/* ir:node:fresh-619358c7d2428a53-reserved-equals */ (/* ir:node:fresh-619358c7d2428a53-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-619358c7d2428a53-reserved-literal */ "reserved-619358c7"))
          ? (/* ir:node:fresh-619358c7d2428a53-reserved-error */ { error: /* ir:node:fresh-619358c7d2428a53-reserved-error-code */ "reserved_identifier_619358c7" })
          : (/* ir:node:fresh-619358c7d2428a53-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-619358c7d2428a53-get-user */ capabilities.users.getById(/* ir:node:fresh-619358c7d2428a53-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-619358c7d2428a53-missing */ { error: /* ir:node:fresh-619358c7d2428a53-missing-code */ "not_found_619358c7d2428a53" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-619358c7d2428a53-found */ { ok: /* ir:node:fresh-619358c7d2428a53-user-ref */ user };
            })()));
  })();
}
