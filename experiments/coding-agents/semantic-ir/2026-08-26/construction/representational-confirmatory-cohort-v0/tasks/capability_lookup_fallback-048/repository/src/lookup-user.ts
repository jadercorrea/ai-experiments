// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA5452ccb1611f09df(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-5452ccb1611f09df-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-5452ccb1611f09df-normalizer */ (/* ir:node:fresh-5452ccb1611f09df-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-5452ccb1611f09df-validation */ (/* ir:node:fresh-5452ccb1611f09df-is-empty */ (/* ir:node:fresh-5452ccb1611f09df-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-5452ccb1611f09df-invalid */ { error: /* ir:node:fresh-5452ccb1611f09df-invalid-code */ "invalid_input_5452ccb1611f09df" })
      : (/* ir:node:fresh-5452ccb1611f09df-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-5452ccb1611f09df-get-user */ capabilities.users.getById(/* ir:node:fresh-5452ccb1611f09df-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-5452ccb1611f09df-missing */ { error: /* ir:node:fresh-5452ccb1611f09df-missing-code */ "not_found_5452ccb1611f09df" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-5452ccb1611f09df-found */ { ok: /* ir:node:fresh-5452ccb1611f09df-user-ref */ user };
        })());
  })();
}
