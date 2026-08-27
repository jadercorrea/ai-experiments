// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
  directory: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function processWithDirectory(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:capability-v2-directory-fallback-001-normalize-let */ (() => {
    const normalizedId: string = /* ir:node:capability-v2-directory-fallback-001-trim */ (/* ir:node:capability-v2-directory-fallback-001-raw-id-ref */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:capability-v2-directory-fallback-001-validity-if */ (/* ir:node:capability-v2-directory-fallback-001-is-empty */ (/* ir:node:capability-v2-directory-fallback-001-normalized-ref-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:capability-v2-directory-fallback-001-invalid-id */ { error: /* ir:node:capability-v2-directory-fallback-001-invalid-id-code */ "invalid_user_id" })
      : (/* ir:node:capability-v2-directory-fallback-001-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:capability-v2-directory-fallback-001-get-user */ capabilities.users.getById(/* ir:node:capability-v2-directory-fallback-001-normalized-ref-for-lookup */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:capability-v2-directory-fallback-001-not-found */ (() => {
              const __semantic_ir_option_2 = /* ir:node:capability-v2-directory-fallback-001-dir-get */ capabilities.directory.getById(/* ir:node:capability-v2-directory-fallback-001-normalized-ref-for-dir */ normalizedId);
              if (__semantic_ir_option_2 === undefined) {
                return /* ir:node:capability-v2-directory-fallback-001-dir-not-found */ { error: /* ir:node:capability-v2-directory-fallback-001-dir-not-found-code */ "not_found" };
              }
              const dirUser: User = __semantic_ir_option_2;
              return /* ir:node:capability-v2-directory-fallback-001-dir-found */ { ok: /* ir:node:capability-v2-directory-fallback-001-dir-user-ref */ dirUser };
            })();
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:capability-v2-directory-fallback-001-found */ { ok: /* ir:node:capability-v2-directory-fallback-001-user-ref */ user };
        })());
  })();
}
