// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAaf2ae0a860a33b5c(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-af2ae0a860a33b5c-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-af2ae0a860a33b5c-normalizer */ (/* ir:node:fresh-af2ae0a860a33b5c-raw-after-normalization-patch */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-af2ae0a860a33b5c-validation */ (/* ir:node:fresh-af2ae0a860a33b5c-is-empty */ (/* ir:node:fresh-af2ae0a860a33b5c-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-af2ae0a860a33b5c-invalid */ { error: /* ir:node:fresh-af2ae0a860a33b5c-invalid-code */ "invalid_input_af2ae0a860a33b5c" })
      : (/* ir:node:fresh-af2ae0a860a33b5c-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-af2ae0a860a33b5c-get-user */ capabilities.users.getById(/* ir:node:fresh-af2ae0a860a33b5c-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-af2ae0a860a33b5c-missing */ { error: /* ir:node:fresh-af2ae0a860a33b5c-missing-code */ "not_found_af2ae0a860a33b5c" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-af2ae0a860a33b5c-found */ { ok: /* ir:node:fresh-af2ae0a860a33b5c-user-ref */ user };
        })());
  })();
}
