// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA48241fc07030bbe9(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-48241fc07030bbe9-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-48241fc07030bbe9-normalizer */ rawId;
    return /* ir:node:fresh-48241fc07030bbe9-validation */ (/* ir:node:fresh-48241fc07030bbe9-is-empty */ (/* ir:node:fresh-48241fc07030bbe9-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-48241fc07030bbe9-invalid */ { error: /* ir:node:fresh-48241fc07030bbe9-invalid-code */ "invalid_input_48241fc07030bbe9" })
      : (/* ir:node:fresh-48241fc07030bbe9-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-48241fc07030bbe9-get-user */ capabilities.users.getById(/* ir:node:fresh-48241fc07030bbe9-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-48241fc07030bbe9-missing */ { error: /* ir:node:fresh-48241fc07030bbe9-missing-code */ "not_found_48241fc07030bbe9" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-48241fc07030bbe9-found */ { ok: /* ir:node:fresh-48241fc07030bbe9-user-ref */ user };
        })());
  })();
}
