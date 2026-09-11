// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA671acb08d532a91d(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-671acb08d532a91d-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-671acb08d532a91d-normalizer */ (/* ir:node:fresh-671acb08d532a91d-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-671acb08d532a91d-validation */ (/* ir:node:fresh-671acb08d532a91d-is-empty */ (/* ir:node:fresh-671acb08d532a91d-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-671acb08d532a91d-invalid */ { error: /* ir:node:fresh-671acb08d532a91d-invalid-code */ "invalid_input_671acb08d532a91d" })
      : (/* ir:node:fresh-671acb08d532a91d-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-671acb08d532a91d-get-user */ capabilities.users.getById(/* ir:node:fresh-671acb08d532a91d-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-671acb08d532a91d-missing */ { error: /* ir:node:fresh-671acb08d532a91d-missing-code */ "not_found_671acb08d532a91d" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-671acb08d532a91d-found */ { ok: /* ir:node:fresh-671acb08d532a91d-user-ref */ user };
        })());
  })();
}
