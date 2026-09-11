// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA1e5cb6857dd06745(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-1e5cb6857dd06745-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-1e5cb6857dd06745-normalizer */ (/* ir:node:fresh-1e5cb6857dd06745-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-1e5cb6857dd06745-validation */ (/* ir:node:fresh-1e5cb6857dd06745-is-empty */ (/* ir:node:fresh-1e5cb6857dd06745-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-1e5cb6857dd06745-invalid */ { error: /* ir:node:fresh-1e5cb6857dd06745-invalid-code */ "invalid_input_1e5cb6857dd06745" })
      : (/* ir:node:fresh-1e5cb6857dd06745-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-1e5cb6857dd06745-get-user */ capabilities.users.getById(/* ir:node:fresh-1e5cb6857dd06745-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-1e5cb6857dd06745-missing */ { error: /* ir:node:fresh-1e5cb6857dd06745-missing-code */ "not_found_1e5cb6857dd06745" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-1e5cb6857dd06745-found */ { ok: /* ir:node:fresh-1e5cb6857dd06745-user-ref */ user };
        })());
  })();
}
