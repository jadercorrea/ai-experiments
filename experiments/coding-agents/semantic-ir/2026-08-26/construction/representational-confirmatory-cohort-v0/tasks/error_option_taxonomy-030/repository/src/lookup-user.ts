// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAa2f088ab7148e27f(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-a2f088ab7148e27f-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-a2f088ab7148e27f-normalizer */ rawId;
    return /* ir:node:fresh-a2f088ab7148e27f-validation */ (/* ir:node:fresh-a2f088ab7148e27f-is-empty */ (/* ir:node:fresh-a2f088ab7148e27f-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-a2f088ab7148e27f-invalid */ { error: /* ir:node:fresh-a2f088ab7148e27f-invalid-code */ "invalid_input_a2f088ab7148e27f" })
      : (/* ir:node:fresh-a2f088ab7148e27f-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-a2f088ab7148e27f-get-user */ capabilities.users.getById(/* ir:node:fresh-a2f088ab7148e27f-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-a2f088ab7148e27f-missing */ { error: /* ir:node:fresh-a2f088ab7148e27f-missing-code */ "not_found_a2f088ab7148e27f" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-a2f088ab7148e27f-found */ { ok: /* ir:node:fresh-a2f088ab7148e27f-user-ref */ user };
        })());
  })();
}
