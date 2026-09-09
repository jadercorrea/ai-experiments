// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA90870ccea4789699(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-90870ccea4789699-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-90870ccea4789699-normalizer */ (/* ir:node:fresh-90870ccea4789699-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-90870ccea4789699-validation */ (/* ir:node:fresh-90870ccea4789699-is-empty */ (/* ir:node:fresh-90870ccea4789699-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-90870ccea4789699-invalid */ { error: /* ir:node:fresh-90870ccea4789699-invalid-code */ "empty_identifier_90870ccea4789699" })
      : (/* ir:node:fresh-90870ccea4789699-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-90870ccea4789699-get-user */ capabilities.users.getById(/* ir:node:fresh-90870ccea4789699-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-90870ccea4789699-missing */ { error: /* ir:node:fresh-90870ccea4789699-missing-code */ "unknown_user_90870ccea4789699" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-90870ccea4789699-found */ { ok: /* ir:node:fresh-90870ccea4789699-user-ref */ user };
        })());
  })();
}
