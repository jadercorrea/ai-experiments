// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA6bc84ae424af1a10(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-6bc84ae424af1a10-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-6bc84ae424af1a10-normalizer */ rawId;
    return /* ir:node:fresh-6bc84ae424af1a10-validation */ (/* ir:node:fresh-6bc84ae424af1a10-is-empty */ (/* ir:node:fresh-6bc84ae424af1a10-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-6bc84ae424af1a10-invalid */ { error: /* ir:node:fresh-6bc84ae424af1a10-invalid-code */ "invalid_input_6bc84ae424af1a10" })
      : (/* ir:node:fresh-6bc84ae424af1a10-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-6bc84ae424af1a10-get-user */ capabilities.users.getById(/* ir:node:fresh-6bc84ae424af1a10-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-6bc84ae424af1a10-missing */ { error: /* ir:node:fresh-6bc84ae424af1a10-missing-code */ "not_found_6bc84ae424af1a10" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-6bc84ae424af1a10-found */ { ok: /* ir:node:fresh-6bc84ae424af1a10-user-ref */ user };
        })());
  })();
}
