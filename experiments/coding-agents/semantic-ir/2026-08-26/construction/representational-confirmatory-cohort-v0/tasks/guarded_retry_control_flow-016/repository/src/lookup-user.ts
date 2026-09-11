// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAfa1c00bfe14f0d27(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-fa1c00bfe14f0d27-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-fa1c00bfe14f0d27-normalizer */ (/* ir:node:fresh-fa1c00bfe14f0d27-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-fa1c00bfe14f0d27-validation */ (/* ir:node:fresh-fa1c00bfe14f0d27-is-empty */ (/* ir:node:fresh-fa1c00bfe14f0d27-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-fa1c00bfe14f0d27-invalid */ { error: /* ir:node:fresh-fa1c00bfe14f0d27-invalid-code */ "invalid_input_fa1c00bfe14f0d27" })
      : (/* ir:node:fresh-fa1c00bfe14f0d27-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-fa1c00bfe14f0d27-get-user */ capabilities.users.getById(/* ir:node:fresh-fa1c00bfe14f0d27-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-fa1c00bfe14f0d27-missing */ { error: /* ir:node:fresh-fa1c00bfe14f0d27-missing-code */ "not_found_fa1c00bfe14f0d27" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-fa1c00bfe14f0d27-found */ { ok: /* ir:node:fresh-fa1c00bfe14f0d27-user-ref */ user };
        })());
  })();
}
