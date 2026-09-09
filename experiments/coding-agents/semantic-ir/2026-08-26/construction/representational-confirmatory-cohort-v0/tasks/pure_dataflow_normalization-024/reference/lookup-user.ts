// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA9a6187e0fd3ac425(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-9a6187e0fd3ac425-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-9a6187e0fd3ac425-normalizer */ (/* ir:node:fresh-9a6187e0fd3ac425-raw-after-normalization-patch */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-9a6187e0fd3ac425-validation */ (/* ir:node:fresh-9a6187e0fd3ac425-is-empty */ (/* ir:node:fresh-9a6187e0fd3ac425-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-9a6187e0fd3ac425-invalid */ { error: /* ir:node:fresh-9a6187e0fd3ac425-invalid-code */ "invalid_input_9a6187e0fd3ac425" })
      : (/* ir:node:fresh-9a6187e0fd3ac425-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-9a6187e0fd3ac425-get-user */ capabilities.users.getById(/* ir:node:fresh-9a6187e0fd3ac425-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-9a6187e0fd3ac425-missing */ { error: /* ir:node:fresh-9a6187e0fd3ac425-missing-code */ "not_found_9a6187e0fd3ac425" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-9a6187e0fd3ac425-found */ { ok: /* ir:node:fresh-9a6187e0fd3ac425-user-ref */ user };
        })());
  })();
}
