// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA38abedef9bc7a6ea(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-38abedef9bc7a6ea-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-38abedef9bc7a6ea-normalizer */ (/* ir:node:fresh-38abedef9bc7a6ea-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-38abedef9bc7a6ea-validation */ (/* ir:node:fresh-38abedef9bc7a6ea-is-empty */ (/* ir:node:fresh-38abedef9bc7a6ea-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-38abedef9bc7a6ea-invalid */ { error: /* ir:node:fresh-38abedef9bc7a6ea-invalid-code */ "invalid_input_38abedef9bc7a6ea" })
      : (/* ir:node:fresh-38abedef9bc7a6ea-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-38abedef9bc7a6ea-get-user */ capabilities.users.getById(/* ir:node:fresh-38abedef9bc7a6ea-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-38abedef9bc7a6ea-missing */ { error: /* ir:node:fresh-38abedef9bc7a6ea-missing-code */ "not_found_38abedef9bc7a6ea" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-38abedef9bc7a6ea-found */ { ok: /* ir:node:fresh-38abedef9bc7a6ea-user-ref */ user };
        })());
  })();
}
