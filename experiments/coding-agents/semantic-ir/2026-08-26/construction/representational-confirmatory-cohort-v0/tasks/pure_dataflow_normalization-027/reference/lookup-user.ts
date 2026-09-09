// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA561290cb17fffdfa(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-561290cb17fffdfa-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-561290cb17fffdfa-normalizer */ rawId;
    return /* ir:node:fresh-561290cb17fffdfa-validation */ (/* ir:node:fresh-561290cb17fffdfa-is-empty */ (/* ir:node:fresh-561290cb17fffdfa-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-561290cb17fffdfa-invalid */ { error: /* ir:node:fresh-561290cb17fffdfa-invalid-code */ "invalid_input_561290cb17fffdfa" })
      : (/* ir:node:fresh-561290cb17fffdfa-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-561290cb17fffdfa-get-user */ capabilities.users.getById(/* ir:node:fresh-561290cb17fffdfa-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-561290cb17fffdfa-missing */ { error: /* ir:node:fresh-561290cb17fffdfa-missing-code */ "not_found_561290cb17fffdfa" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-561290cb17fffdfa-found */ { ok: /* ir:node:fresh-561290cb17fffdfa-user-ref */ user };
        })());
  })();
}
