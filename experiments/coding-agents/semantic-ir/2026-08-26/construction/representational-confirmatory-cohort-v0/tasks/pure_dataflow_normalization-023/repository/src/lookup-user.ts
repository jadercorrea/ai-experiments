// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA347e39ac56822aae(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-347e39ac56822aae-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-347e39ac56822aae-normalizer */ rawId;
    return /* ir:node:fresh-347e39ac56822aae-validation */ (/* ir:node:fresh-347e39ac56822aae-is-empty */ (/* ir:node:fresh-347e39ac56822aae-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-347e39ac56822aae-invalid */ { error: /* ir:node:fresh-347e39ac56822aae-invalid-code */ "invalid_input_347e39ac56822aae" })
      : (/* ir:node:fresh-347e39ac56822aae-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-347e39ac56822aae-get-user */ capabilities.users.getById(/* ir:node:fresh-347e39ac56822aae-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-347e39ac56822aae-missing */ { error: /* ir:node:fresh-347e39ac56822aae-missing-code */ "not_found_347e39ac56822aae" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-347e39ac56822aae-found */ { ok: /* ir:node:fresh-347e39ac56822aae-user-ref */ user };
        })());
  })();
}
