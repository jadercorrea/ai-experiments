// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA0101a8f9948f643e(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-0101a8f9948f643e-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-0101a8f9948f643e-normalizer */ rawId;
    return /* ir:node:fresh-0101a8f9948f643e-validation */ (/* ir:node:fresh-0101a8f9948f643e-is-empty */ (/* ir:node:fresh-0101a8f9948f643e-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-0101a8f9948f643e-invalid */ { error: /* ir:node:fresh-0101a8f9948f643e-invalid-code */ "invalid_input_0101a8f9948f643e" })
      : (/* ir:node:fresh-0101a8f9948f643e-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-0101a8f9948f643e-get-user */ capabilities.users.getById(/* ir:node:fresh-0101a8f9948f643e-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-0101a8f9948f643e-missing */ { error: /* ir:node:fresh-0101a8f9948f643e-missing-code */ "not_found_0101a8f9948f643e" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-0101a8f9948f643e-found */ { ok: /* ir:node:fresh-0101a8f9948f643e-user-ref */ user };
        })());
  })();
}
