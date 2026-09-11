// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAa4652ff83a4ab611(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-a4652ff83a4ab611-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-a4652ff83a4ab611-normalizer */ (/* ir:node:fresh-a4652ff83a4ab611-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-a4652ff83a4ab611-validation */ (/* ir:node:fresh-a4652ff83a4ab611-is-empty */ (/* ir:node:fresh-a4652ff83a4ab611-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-a4652ff83a4ab611-invalid */ { error: /* ir:node:fresh-a4652ff83a4ab611-invalid-code */ "invalid_input_a4652ff83a4ab611" })
      : (/* ir:node:fresh-a4652ff83a4ab611-user-match */ (/* ir:node:fresh-a4652ff83a4ab611-reserved-equals */ (/* ir:node:fresh-a4652ff83a4ab611-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-a4652ff83a4ab611-reserved-literal */ "reserved-a4652ff8"))
          ? (/* ir:node:fresh-a4652ff83a4ab611-reserved-error */ { error: /* ir:node:fresh-a4652ff83a4ab611-reserved-error-code */ "reserved_identifier_a4652ff8" })
          : (/* ir:node:fresh-a4652ff83a4ab611-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-a4652ff83a4ab611-get-user */ capabilities.users.getById(/* ir:node:fresh-a4652ff83a4ab611-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-a4652ff83a4ab611-missing */ { error: /* ir:node:fresh-a4652ff83a4ab611-missing-code */ "not_found_a4652ff83a4ab611" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-a4652ff83a4ab611-found */ { ok: /* ir:node:fresh-a4652ff83a4ab611-user-ref */ user };
            })()));
  })();
}
