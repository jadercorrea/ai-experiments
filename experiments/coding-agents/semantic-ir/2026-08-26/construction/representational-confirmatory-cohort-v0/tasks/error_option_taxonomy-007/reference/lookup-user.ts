// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA043728b6b2ba0839(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-043728b6b2ba0839-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-043728b6b2ba0839-normalizer */ (/* ir:node:fresh-043728b6b2ba0839-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-043728b6b2ba0839-validation */ (/* ir:node:fresh-043728b6b2ba0839-is-empty */ (/* ir:node:fresh-043728b6b2ba0839-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-043728b6b2ba0839-invalid */ { error: /* ir:node:fresh-043728b6b2ba0839-invalid-code */ "empty_identifier_043728b6b2ba0839" })
      : (/* ir:node:fresh-043728b6b2ba0839-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-043728b6b2ba0839-get-user */ capabilities.users.getById(/* ir:node:fresh-043728b6b2ba0839-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-043728b6b2ba0839-missing */ { error: /* ir:node:fresh-043728b6b2ba0839-missing-code */ "unknown_user_043728b6b2ba0839" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-043728b6b2ba0839-found */ { ok: /* ir:node:fresh-043728b6b2ba0839-user-ref */ user };
        })());
  })();
}
