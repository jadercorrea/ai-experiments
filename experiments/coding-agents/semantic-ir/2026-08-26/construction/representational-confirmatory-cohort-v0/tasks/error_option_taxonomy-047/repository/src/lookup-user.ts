// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA84a3b1423351986a(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-84a3b1423351986a-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-84a3b1423351986a-normalizer */ rawId;
    return /* ir:node:fresh-84a3b1423351986a-validation */ (/* ir:node:fresh-84a3b1423351986a-is-empty */ (/* ir:node:fresh-84a3b1423351986a-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-84a3b1423351986a-invalid */ { error: /* ir:node:fresh-84a3b1423351986a-invalid-code */ "invalid_input_84a3b1423351986a" })
      : (/* ir:node:fresh-84a3b1423351986a-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-84a3b1423351986a-get-user */ capabilities.users.getById(/* ir:node:fresh-84a3b1423351986a-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-84a3b1423351986a-missing */ { error: /* ir:node:fresh-84a3b1423351986a-missing-code */ "not_found_84a3b1423351986a" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-84a3b1423351986a-found */ { ok: /* ir:node:fresh-84a3b1423351986a-user-ref */ user };
        })());
  })();
}
