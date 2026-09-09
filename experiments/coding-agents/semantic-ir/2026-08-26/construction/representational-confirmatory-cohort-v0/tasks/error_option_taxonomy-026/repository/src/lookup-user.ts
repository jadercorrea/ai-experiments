// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAb3a1159c23313775(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-b3a1159c23313775-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-b3a1159c23313775-normalizer */ rawId;
    return /* ir:node:fresh-b3a1159c23313775-validation */ (/* ir:node:fresh-b3a1159c23313775-is-empty */ (/* ir:node:fresh-b3a1159c23313775-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-b3a1159c23313775-invalid */ { error: /* ir:node:fresh-b3a1159c23313775-invalid-code */ "invalid_input_b3a1159c23313775" })
      : (/* ir:node:fresh-b3a1159c23313775-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-b3a1159c23313775-get-user */ capabilities.users.getById(/* ir:node:fresh-b3a1159c23313775-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-b3a1159c23313775-missing */ { error: /* ir:node:fresh-b3a1159c23313775-missing-code */ "not_found_b3a1159c23313775" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-b3a1159c23313775-found */ { ok: /* ir:node:fresh-b3a1159c23313775-user-ref */ user };
        })());
  })();
}
