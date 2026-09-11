// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAc755db46706f64c1(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-c755db46706f64c1-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-c755db46706f64c1-normalizer */ (/* ir:node:fresh-c755db46706f64c1-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-c755db46706f64c1-validation */ (/* ir:node:fresh-c755db46706f64c1-is-empty */ (/* ir:node:fresh-c755db46706f64c1-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-c755db46706f64c1-invalid */ { error: /* ir:node:fresh-c755db46706f64c1-invalid-code */ "invalid_input_c755db46706f64c1" })
      : (/* ir:node:fresh-c755db46706f64c1-user-match */ (/* ir:node:fresh-c755db46706f64c1-reserved-equals */ (/* ir:node:fresh-c755db46706f64c1-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-c755db46706f64c1-reserved-literal */ "reserved-c755db46"))
          ? (/* ir:node:fresh-c755db46706f64c1-reserved-error */ { error: /* ir:node:fresh-c755db46706f64c1-reserved-error-code */ "reserved_identifier_c755db46" })
          : (/* ir:node:fresh-c755db46706f64c1-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-c755db46706f64c1-get-user */ capabilities.users.getById(/* ir:node:fresh-c755db46706f64c1-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-c755db46706f64c1-missing */ { error: /* ir:node:fresh-c755db46706f64c1-missing-code */ "not_found_c755db46706f64c1" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-c755db46706f64c1-found */ { ok: /* ir:node:fresh-c755db46706f64c1-user-ref */ user };
            })()));
  })();
}
