// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA49880e11ac8e3d7d(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-49880e11ac8e3d7d-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-49880e11ac8e3d7d-normalizer */ (/* ir:node:fresh-49880e11ac8e3d7d-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-49880e11ac8e3d7d-validation */ (/* ir:node:fresh-49880e11ac8e3d7d-is-empty */ (/* ir:node:fresh-49880e11ac8e3d7d-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-49880e11ac8e3d7d-invalid */ { error: /* ir:node:fresh-49880e11ac8e3d7d-invalid-code */ "invalid_input_49880e11ac8e3d7d" })
      : (/* ir:node:fresh-49880e11ac8e3d7d-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-49880e11ac8e3d7d-get-user */ capabilities.users.getById(/* ir:node:fresh-49880e11ac8e3d7d-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-49880e11ac8e3d7d-missing */ { error: /* ir:node:fresh-49880e11ac8e3d7d-missing-code */ "not_found_49880e11ac8e3d7d" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-49880e11ac8e3d7d-found */ { ok: /* ir:node:fresh-49880e11ac8e3d7d-user-ref */ user };
        })());
  })();
}
