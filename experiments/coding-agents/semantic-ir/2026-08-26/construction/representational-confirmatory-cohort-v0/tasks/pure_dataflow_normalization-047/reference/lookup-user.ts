// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA77e5fdd06d9f398a(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-77e5fdd06d9f398a-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-77e5fdd06d9f398a-normalizer */ rawId;
    return /* ir:node:fresh-77e5fdd06d9f398a-validation */ (/* ir:node:fresh-77e5fdd06d9f398a-is-empty */ (/* ir:node:fresh-77e5fdd06d9f398a-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-77e5fdd06d9f398a-invalid */ { error: /* ir:node:fresh-77e5fdd06d9f398a-invalid-code */ "invalid_input_77e5fdd06d9f398a" })
      : (/* ir:node:fresh-77e5fdd06d9f398a-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-77e5fdd06d9f398a-get-user */ capabilities.users.getById(/* ir:node:fresh-77e5fdd06d9f398a-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-77e5fdd06d9f398a-missing */ { error: /* ir:node:fresh-77e5fdd06d9f398a-missing-code */ "not_found_77e5fdd06d9f398a" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-77e5fdd06d9f398a-found */ { ok: /* ir:node:fresh-77e5fdd06d9f398a-user-ref */ user };
        })());
  })();
}
