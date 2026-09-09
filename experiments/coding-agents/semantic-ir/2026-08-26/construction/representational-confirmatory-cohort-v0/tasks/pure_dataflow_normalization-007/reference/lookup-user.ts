// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA64a464fa221e93cb(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-64a464fa221e93cb-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-64a464fa221e93cb-normalizer */ (/* ir:node:fresh-64a464fa221e93cb-raw-after-normalization-patch */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-64a464fa221e93cb-validation */ (/* ir:node:fresh-64a464fa221e93cb-is-empty */ (/* ir:node:fresh-64a464fa221e93cb-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-64a464fa221e93cb-invalid */ { error: /* ir:node:fresh-64a464fa221e93cb-invalid-code */ "invalid_input_64a464fa221e93cb" })
      : (/* ir:node:fresh-64a464fa221e93cb-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-64a464fa221e93cb-get-user */ capabilities.users.getById(/* ir:node:fresh-64a464fa221e93cb-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-64a464fa221e93cb-missing */ { error: /* ir:node:fresh-64a464fa221e93cb-missing-code */ "not_found_64a464fa221e93cb" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-64a464fa221e93cb-found */ { ok: /* ir:node:fresh-64a464fa221e93cb-user-ref */ user };
        })());
  })();
}
