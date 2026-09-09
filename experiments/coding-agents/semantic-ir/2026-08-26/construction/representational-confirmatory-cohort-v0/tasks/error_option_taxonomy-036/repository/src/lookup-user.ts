// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA95df8687b777f0df(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-95df8687b777f0df-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-95df8687b777f0df-normalizer */ (/* ir:node:fresh-95df8687b777f0df-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-95df8687b777f0df-validation */ (/* ir:node:fresh-95df8687b777f0df-is-empty */ (/* ir:node:fresh-95df8687b777f0df-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-95df8687b777f0df-invalid */ { error: /* ir:node:fresh-95df8687b777f0df-invalid-code */ "invalid_input_95df8687b777f0df" })
      : (/* ir:node:fresh-95df8687b777f0df-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-95df8687b777f0df-get-user */ capabilities.users.getById(/* ir:node:fresh-95df8687b777f0df-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-95df8687b777f0df-missing */ { error: /* ir:node:fresh-95df8687b777f0df-missing-code */ "not_found_95df8687b777f0df" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-95df8687b777f0df-found */ { ok: /* ir:node:fresh-95df8687b777f0df-user-ref */ user };
        })());
  })();
}
