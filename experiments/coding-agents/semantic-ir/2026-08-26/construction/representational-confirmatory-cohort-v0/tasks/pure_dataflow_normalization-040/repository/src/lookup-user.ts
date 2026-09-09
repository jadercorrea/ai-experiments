// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAa4313fc1025f298b(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-a4313fc1025f298b-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-a4313fc1025f298b-normalizer */ rawId;
    return /* ir:node:fresh-a4313fc1025f298b-validation */ (/* ir:node:fresh-a4313fc1025f298b-is-empty */ (/* ir:node:fresh-a4313fc1025f298b-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-a4313fc1025f298b-invalid */ { error: /* ir:node:fresh-a4313fc1025f298b-invalid-code */ "invalid_input_a4313fc1025f298b" })
      : (/* ir:node:fresh-a4313fc1025f298b-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-a4313fc1025f298b-get-user */ capabilities.users.getById(/* ir:node:fresh-a4313fc1025f298b-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-a4313fc1025f298b-missing */ { error: /* ir:node:fresh-a4313fc1025f298b-missing-code */ "not_found_a4313fc1025f298b" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-a4313fc1025f298b-found */ { ok: /* ir:node:fresh-a4313fc1025f298b-user-ref */ user };
        })());
  })();
}
