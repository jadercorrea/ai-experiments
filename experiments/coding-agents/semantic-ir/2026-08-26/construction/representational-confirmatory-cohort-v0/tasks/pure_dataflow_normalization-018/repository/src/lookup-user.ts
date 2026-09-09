// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAd5bde1e5afb40267(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-d5bde1e5afb40267-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-d5bde1e5afb40267-normalizer */ rawId;
    return /* ir:node:fresh-d5bde1e5afb40267-validation */ (/* ir:node:fresh-d5bde1e5afb40267-is-empty */ (/* ir:node:fresh-d5bde1e5afb40267-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-d5bde1e5afb40267-invalid */ { error: /* ir:node:fresh-d5bde1e5afb40267-invalid-code */ "invalid_input_d5bde1e5afb40267" })
      : (/* ir:node:fresh-d5bde1e5afb40267-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-d5bde1e5afb40267-get-user */ capabilities.users.getById(/* ir:node:fresh-d5bde1e5afb40267-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-d5bde1e5afb40267-missing */ { error: /* ir:node:fresh-d5bde1e5afb40267-missing-code */ "not_found_d5bde1e5afb40267" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-d5bde1e5afb40267-found */ { ok: /* ir:node:fresh-d5bde1e5afb40267-user-ref */ user };
        })());
  })();
}
