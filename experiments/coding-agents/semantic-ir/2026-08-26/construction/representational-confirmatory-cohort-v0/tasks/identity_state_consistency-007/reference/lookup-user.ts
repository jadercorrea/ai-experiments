// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA9c61b2dc41a4dae9(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-9c61b2dc41a4dae9-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-9c61b2dc41a4dae9-normalizer */ (/* ir:node:fresh-9c61b2dc41a4dae9-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-9c61b2dc41a4dae9-validation */ (/* ir:node:fresh-9c61b2dc41a4dae9-is-empty */ (/* ir:node:fresh-9c61b2dc41a4dae9-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-9c61b2dc41a4dae9-invalid */ { error: /* ir:node:fresh-9c61b2dc41a4dae9-invalid-code */ "invalid_input_9c61b2dc41a4dae9" })
      : (/* ir:node:fresh-9c61b2dc41a4dae9-user-match */ (/* ir:node:fresh-9c61b2dc41a4dae9-reserved-equals */ (/* ir:node:fresh-9c61b2dc41a4dae9-normalized-for-reserved */ normalizedId) === (/* ir:node:fresh-9c61b2dc41a4dae9-reserved-literal */ "reserved-9c61b2dc"))
          ? (/* ir:node:fresh-9c61b2dc41a4dae9-reserved-error */ { error: /* ir:node:fresh-9c61b2dc41a4dae9-reserved-error-code */ "reserved_identifier_9c61b2dc" })
          : (/* ir:node:fresh-9c61b2dc41a4dae9-user-match-after-guard */ (() => {
              const __semantic_ir_option_1 = /* ir:node:fresh-9c61b2dc41a4dae9-get-user */ capabilities.users.getById(/* ir:node:fresh-9c61b2dc41a4dae9-normalized-for-user */ normalizedId);
              if (__semantic_ir_option_1 === undefined) {
                return /* ir:node:fresh-9c61b2dc41a4dae9-missing */ { error: /* ir:node:fresh-9c61b2dc41a4dae9-missing-code */ "not_found_9c61b2dc41a4dae9" };
              }
              const user: User = __semantic_ir_option_1;
              return /* ir:node:fresh-9c61b2dc41a4dae9-found */ { ok: /* ir:node:fresh-9c61b2dc41a4dae9-user-ref */ user };
            })()));
  })();
}
