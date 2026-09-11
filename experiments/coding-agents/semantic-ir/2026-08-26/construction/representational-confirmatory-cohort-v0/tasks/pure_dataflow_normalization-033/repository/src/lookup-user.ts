// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA1d1f5a2daeb25886(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-1d1f5a2daeb25886-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-1d1f5a2daeb25886-normalizer */ rawId;
    return /* ir:node:fresh-1d1f5a2daeb25886-validation */ (/* ir:node:fresh-1d1f5a2daeb25886-is-empty */ (/* ir:node:fresh-1d1f5a2daeb25886-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-1d1f5a2daeb25886-invalid */ { error: /* ir:node:fresh-1d1f5a2daeb25886-invalid-code */ "invalid_input_1d1f5a2daeb25886" })
      : (/* ir:node:fresh-1d1f5a2daeb25886-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-1d1f5a2daeb25886-get-user */ capabilities.users.getById(/* ir:node:fresh-1d1f5a2daeb25886-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-1d1f5a2daeb25886-missing */ { error: /* ir:node:fresh-1d1f5a2daeb25886-missing-code */ "not_found_1d1f5a2daeb25886" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-1d1f5a2daeb25886-found */ { ok: /* ir:node:fresh-1d1f5a2daeb25886-user-ref */ user };
        })());
  })();
}
