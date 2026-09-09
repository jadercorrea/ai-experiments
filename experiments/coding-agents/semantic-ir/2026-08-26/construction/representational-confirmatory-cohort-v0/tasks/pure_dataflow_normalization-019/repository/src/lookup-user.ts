// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA3859e21be7968baf(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-3859e21be7968baf-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-3859e21be7968baf-normalizer */ rawId;
    return /* ir:node:fresh-3859e21be7968baf-validation */ (/* ir:node:fresh-3859e21be7968baf-is-empty */ (/* ir:node:fresh-3859e21be7968baf-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-3859e21be7968baf-invalid */ { error: /* ir:node:fresh-3859e21be7968baf-invalid-code */ "invalid_input_3859e21be7968baf" })
      : (/* ir:node:fresh-3859e21be7968baf-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-3859e21be7968baf-get-user */ capabilities.users.getById(/* ir:node:fresh-3859e21be7968baf-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-3859e21be7968baf-missing */ { error: /* ir:node:fresh-3859e21be7968baf-missing-code */ "not_found_3859e21be7968baf" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-3859e21be7968baf-found */ { ok: /* ir:node:fresh-3859e21be7968baf-user-ref */ user };
        })());
  })();
}
