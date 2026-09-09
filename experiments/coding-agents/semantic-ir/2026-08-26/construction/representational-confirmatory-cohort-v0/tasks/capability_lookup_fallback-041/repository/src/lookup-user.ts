// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA5a50299e3ece1b60(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-5a50299e3ece1b60-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-5a50299e3ece1b60-normalizer */ (/* ir:node:fresh-5a50299e3ece1b60-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-5a50299e3ece1b60-validation */ (/* ir:node:fresh-5a50299e3ece1b60-is-empty */ (/* ir:node:fresh-5a50299e3ece1b60-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-5a50299e3ece1b60-invalid */ { error: /* ir:node:fresh-5a50299e3ece1b60-invalid-code */ "invalid_input_5a50299e3ece1b60" })
      : (/* ir:node:fresh-5a50299e3ece1b60-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-5a50299e3ece1b60-get-user */ capabilities.users.getById(/* ir:node:fresh-5a50299e3ece1b60-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-5a50299e3ece1b60-missing */ { error: /* ir:node:fresh-5a50299e3ece1b60-missing-code */ "not_found_5a50299e3ece1b60" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-5a50299e3ece1b60-found */ { ok: /* ir:node:fresh-5a50299e3ece1b60-user-ref */ user };
        })());
  })();
}
