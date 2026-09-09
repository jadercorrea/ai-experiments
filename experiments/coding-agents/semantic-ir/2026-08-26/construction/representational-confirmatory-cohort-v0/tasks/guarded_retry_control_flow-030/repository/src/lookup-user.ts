// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA508ebb87fc47a278(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-508ebb87fc47a278-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-508ebb87fc47a278-normalizer */ (/* ir:node:fresh-508ebb87fc47a278-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-508ebb87fc47a278-validation */ (/* ir:node:fresh-508ebb87fc47a278-is-empty */ (/* ir:node:fresh-508ebb87fc47a278-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-508ebb87fc47a278-invalid */ { error: /* ir:node:fresh-508ebb87fc47a278-invalid-code */ "invalid_input_508ebb87fc47a278" })
      : (/* ir:node:fresh-508ebb87fc47a278-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-508ebb87fc47a278-get-user */ capabilities.users.getById(/* ir:node:fresh-508ebb87fc47a278-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-508ebb87fc47a278-missing */ { error: /* ir:node:fresh-508ebb87fc47a278-missing-code */ "not_found_508ebb87fc47a278" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-508ebb87fc47a278-found */ { ok: /* ir:node:fresh-508ebb87fc47a278-user-ref */ user };
        })());
  })();
}
