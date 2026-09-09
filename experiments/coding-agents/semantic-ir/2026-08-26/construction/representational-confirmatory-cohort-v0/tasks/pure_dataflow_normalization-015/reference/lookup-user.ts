// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAf51cd5984bc5468f(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-f51cd5984bc5468f-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-f51cd5984bc5468f-normalizer */ rawId;
    return /* ir:node:fresh-f51cd5984bc5468f-validation */ (/* ir:node:fresh-f51cd5984bc5468f-is-empty */ (/* ir:node:fresh-f51cd5984bc5468f-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-f51cd5984bc5468f-invalid */ { error: /* ir:node:fresh-f51cd5984bc5468f-invalid-code */ "invalid_input_f51cd5984bc5468f" })
      : (/* ir:node:fresh-f51cd5984bc5468f-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-f51cd5984bc5468f-get-user */ capabilities.users.getById(/* ir:node:fresh-f51cd5984bc5468f-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-f51cd5984bc5468f-missing */ { error: /* ir:node:fresh-f51cd5984bc5468f-missing-code */ "not_found_f51cd5984bc5468f" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-f51cd5984bc5468f-found */ { ok: /* ir:node:fresh-f51cd5984bc5468f-user-ref */ user };
        })());
  })();
}
