// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAf4154303f5ea5963(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-f4154303f5ea5963-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-f4154303f5ea5963-normalizer */ (/* ir:node:fresh-f4154303f5ea5963-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-f4154303f5ea5963-validation */ (/* ir:node:fresh-f4154303f5ea5963-is-empty */ (/* ir:node:fresh-f4154303f5ea5963-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-f4154303f5ea5963-invalid */ { error: /* ir:node:fresh-f4154303f5ea5963-invalid-code */ "invalid_input_f4154303f5ea5963" })
      : (/* ir:node:fresh-f4154303f5ea5963-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-f4154303f5ea5963-get-user */ capabilities.users.getById(/* ir:node:fresh-f4154303f5ea5963-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-f4154303f5ea5963-missing */ { error: /* ir:node:fresh-f4154303f5ea5963-missing-code */ "not_found_f4154303f5ea5963" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-f4154303f5ea5963-found */ { ok: /* ir:node:fresh-f4154303f5ea5963-user-ref */ user };
        })());
  })();
}
