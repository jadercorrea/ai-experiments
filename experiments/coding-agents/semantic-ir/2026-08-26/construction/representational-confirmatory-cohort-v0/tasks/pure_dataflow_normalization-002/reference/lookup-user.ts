// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAd9648cc525f1f150(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-d9648cc525f1f150-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-d9648cc525f1f150-normalizer */ (/* ir:node:fresh-d9648cc525f1f150-raw-after-normalization-patch */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-d9648cc525f1f150-validation */ (/* ir:node:fresh-d9648cc525f1f150-is-empty */ (/* ir:node:fresh-d9648cc525f1f150-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-d9648cc525f1f150-invalid */ { error: /* ir:node:fresh-d9648cc525f1f150-invalid-code */ "invalid_input_d9648cc525f1f150" })
      : (/* ir:node:fresh-d9648cc525f1f150-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-d9648cc525f1f150-get-user */ capabilities.users.getById(/* ir:node:fresh-d9648cc525f1f150-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-d9648cc525f1f150-missing */ { error: /* ir:node:fresh-d9648cc525f1f150-missing-code */ "not_found_d9648cc525f1f150" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-d9648cc525f1f150-found */ { ok: /* ir:node:fresh-d9648cc525f1f150-user-ref */ user };
        })());
  })();
}
