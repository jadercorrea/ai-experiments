// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
  directory: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function executeWithDirectory(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:session-v3-directory-fallback-001-normalize-let */ (() => {
    const normalizedId: string = /* ir:node:session-v3-directory-fallback-001-trim */ (/* ir:node:session-v3-directory-fallback-001-raw-id-ref */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:session-v3-directory-fallback-001-validity-if */ (/* ir:node:session-v3-directory-fallback-001-is-empty */ (/* ir:node:session-v3-directory-fallback-001-normalized-ref-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:session-v3-directory-fallback-001-invalid-id */ { error: /* ir:node:session-v3-directory-fallback-001-invalid-id-code */ "invalid_user_id" })
      : (/* ir:node:session-v3-directory-fallback-001-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:session-v3-directory-fallback-001-get-user */ capabilities.users.getById(/* ir:node:session-v3-directory-fallback-001-normalized-ref-for-lookup */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:session-v3-directory-fallback-001-not-found */ (() => {
              const __semantic_ir_option_2 = /* ir:node:motion-9d811bcecb21-r1 */ capabilities.directory.getById(/* ir:node:motion-9d811bcecb21-r4 */ rawId);
              if (__semantic_ir_option_2 === undefined) {
                return /* ir:node:motion-9d811bcecb21-r2 */ { error: /* ir:node:motion-9d811bcecb21-r5 */ "not_found" };
              }
              const dirUser: User = __semantic_ir_option_2;
              return /* ir:node:motion-9d811bcecb21-r3 */ { ok: /* ir:node:motion-9d811bcecb21-r6 */ dirUser };
            })();
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:session-v3-directory-fallback-001-found */ { ok: /* ir:node:session-v3-directory-fallback-001-user-ref */ user };
        })());
  })();
}
