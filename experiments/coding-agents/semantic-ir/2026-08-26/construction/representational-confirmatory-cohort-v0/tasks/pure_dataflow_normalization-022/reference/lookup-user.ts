// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAb630e8495cfc918f(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-b630e8495cfc918f-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-b630e8495cfc918f-normalizer */ (/* ir:node:fresh-b630e8495cfc918f-raw-after-normalization-patch */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-b630e8495cfc918f-validation */ (/* ir:node:fresh-b630e8495cfc918f-is-empty */ (/* ir:node:fresh-b630e8495cfc918f-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-b630e8495cfc918f-invalid */ { error: /* ir:node:fresh-b630e8495cfc918f-invalid-code */ "invalid_input_b630e8495cfc918f" })
      : (/* ir:node:fresh-b630e8495cfc918f-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-b630e8495cfc918f-get-user */ capabilities.users.getById(/* ir:node:fresh-b630e8495cfc918f-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-b630e8495cfc918f-missing */ { error: /* ir:node:fresh-b630e8495cfc918f-missing-code */ "not_found_b630e8495cfc918f" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-b630e8495cfc918f-found */ { ok: /* ir:node:fresh-b630e8495cfc918f-user-ref */ user };
        })());
  })();
}
