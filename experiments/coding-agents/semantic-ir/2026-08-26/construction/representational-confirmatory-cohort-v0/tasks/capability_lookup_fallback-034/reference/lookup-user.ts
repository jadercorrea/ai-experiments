// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
  directory: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA24d65a1e90d3c06e(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-24d65a1e90d3c06e-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-24d65a1e90d3c06e-normalizer */ (/* ir:node:fresh-24d65a1e90d3c06e-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-24d65a1e90d3c06e-validation */ (/* ir:node:fresh-24d65a1e90d3c06e-is-empty */ (/* ir:node:fresh-24d65a1e90d3c06e-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-24d65a1e90d3c06e-invalid */ { error: /* ir:node:fresh-24d65a1e90d3c06e-invalid-code */ "invalid_input_24d65a1e90d3c06e" })
      : (/* ir:node:fresh-24d65a1e90d3c06e-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-24d65a1e90d3c06e-get-user */ capabilities.users.getById(/* ir:node:fresh-24d65a1e90d3c06e-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-24d65a1e90d3c06e-directory-match */ (() => {
              const __semantic_ir_option_2 = /* ir:node:fresh-24d65a1e90d3c06e-get-directory-user */ capabilities.directory.getById(/* ir:node:fresh-24d65a1e90d3c06e-identifier-for-directory */ normalizedId);
              if (__semantic_ir_option_2 === undefined) {
                return /* ir:node:fresh-24d65a1e90d3c06e-missing */ { error: /* ir:node:fresh-24d65a1e90d3c06e-missing-code */ "not_found_24d65a1e90d3c06e" };
              }
              const directoryUser: User = __semantic_ir_option_2;
              return /* ir:node:fresh-24d65a1e90d3c06e-directory-found */ { ok: /* ir:node:fresh-24d65a1e90d3c06e-directory-user-ref */ directoryUser };
            })();
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-24d65a1e90d3c06e-found */ { ok: /* ir:node:fresh-24d65a1e90d3c06e-user-ref */ user };
        })());
  })();
}
