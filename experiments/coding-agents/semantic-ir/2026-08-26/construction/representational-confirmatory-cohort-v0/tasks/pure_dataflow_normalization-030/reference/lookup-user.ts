// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA6f325f3f0098368a(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-6f325f3f0098368a-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-6f325f3f0098368a-normalizer */ rawId;
    return /* ir:node:fresh-6f325f3f0098368a-validation */ (/* ir:node:fresh-6f325f3f0098368a-is-empty */ (/* ir:node:fresh-6f325f3f0098368a-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-6f325f3f0098368a-invalid */ { error: /* ir:node:fresh-6f325f3f0098368a-invalid-code */ "invalid_input_6f325f3f0098368a" })
      : (/* ir:node:fresh-6f325f3f0098368a-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-6f325f3f0098368a-get-user */ capabilities.users.getById(/* ir:node:fresh-6f325f3f0098368a-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-6f325f3f0098368a-missing */ { error: /* ir:node:fresh-6f325f3f0098368a-missing-code */ "not_found_6f325f3f0098368a" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-6f325f3f0098368a-found */ { ok: /* ir:node:fresh-6f325f3f0098368a-user-ref */ user };
        })());
  })();
}
