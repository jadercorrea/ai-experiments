// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveGuardedUser(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:context-v1-reserved-id-guard-001-normalize-let */ (() => {
    const normalizedId: string = /* ir:node:context-v1-reserved-id-guard-001-trim */ (/* ir:node:context-v1-reserved-id-guard-001-raw-id-ref */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:context-v1-reserved-id-guard-001-validity-if */ (/* ir:node:context-v1-reserved-id-guard-001-is-empty */ (/* ir:node:context-v1-reserved-id-guard-001-normalized-ref-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:context-v1-reserved-id-guard-001-invalid-id */ { error: /* ir:node:context-v1-reserved-id-guard-001-invalid-id-code */ "invalid_user_id" })
      : (normalizedId === "root")
      ? ({ error: "reserved_user_id" })
      : (/* ir:node:context-v1-reserved-id-guard-001-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:context-v1-reserved-id-guard-001-get-user */ capabilities.users.getById(/* ir:node:context-v1-reserved-id-guard-001-normalized-ref-for-lookup */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:context-v1-reserved-id-guard-001-not-found */ { error: /* ir:node:context-v1-reserved-id-guard-001-not-found-code */ "not_found" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:context-v1-reserved-id-guard-001-found */ { ok: /* ir:node:context-v1-reserved-id-guard-001-user-ref */ user };
        })());
  })();
}
