// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAd175959d09f6ae62(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-d175959d09f6ae62-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-d175959d09f6ae62-normalizer */ rawId;
    return /* ir:node:fresh-d175959d09f6ae62-validation */ (/* ir:node:fresh-d175959d09f6ae62-is-empty */ (/* ir:node:fresh-d175959d09f6ae62-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-d175959d09f6ae62-invalid */ { error: /* ir:node:fresh-d175959d09f6ae62-invalid-code */ "invalid_input_d175959d09f6ae62" })
      : (/* ir:node:fresh-d175959d09f6ae62-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-d175959d09f6ae62-get-user */ capabilities.users.getById(/* ir:node:fresh-d175959d09f6ae62-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-d175959d09f6ae62-missing */ { error: /* ir:node:fresh-d175959d09f6ae62-missing-code */ "not_found_d175959d09f6ae62" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-d175959d09f6ae62-found */ { ok: /* ir:node:fresh-d175959d09f6ae62-user-ref */ user };
        })());
  })();
}
