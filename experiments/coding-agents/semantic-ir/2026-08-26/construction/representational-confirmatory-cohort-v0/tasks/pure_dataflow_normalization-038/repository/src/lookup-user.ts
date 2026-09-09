// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAc1674660bdd3a942(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-c1674660bdd3a942-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-c1674660bdd3a942-normalizer */ rawId;
    return /* ir:node:fresh-c1674660bdd3a942-validation */ (/* ir:node:fresh-c1674660bdd3a942-is-empty */ (/* ir:node:fresh-c1674660bdd3a942-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-c1674660bdd3a942-invalid */ { error: /* ir:node:fresh-c1674660bdd3a942-invalid-code */ "invalid_input_c1674660bdd3a942" })
      : (/* ir:node:fresh-c1674660bdd3a942-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-c1674660bdd3a942-get-user */ capabilities.users.getById(/* ir:node:fresh-c1674660bdd3a942-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-c1674660bdd3a942-missing */ { error: /* ir:node:fresh-c1674660bdd3a942-missing-code */ "not_found_c1674660bdd3a942" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-c1674660bdd3a942-found */ { ok: /* ir:node:fresh-c1674660bdd3a942-user-ref */ user };
        })());
  })();
}
