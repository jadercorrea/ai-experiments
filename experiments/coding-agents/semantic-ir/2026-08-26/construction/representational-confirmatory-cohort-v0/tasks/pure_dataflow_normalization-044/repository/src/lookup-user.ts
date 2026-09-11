// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAeeb81f32a8a7b14e(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-eeb81f32a8a7b14e-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-eeb81f32a8a7b14e-normalizer */ (/* ir:node:fresh-eeb81f32a8a7b14e-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-eeb81f32a8a7b14e-validation */ (/* ir:node:fresh-eeb81f32a8a7b14e-is-empty */ (/* ir:node:fresh-eeb81f32a8a7b14e-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-eeb81f32a8a7b14e-invalid */ { error: /* ir:node:fresh-eeb81f32a8a7b14e-invalid-code */ "invalid_input_eeb81f32a8a7b14e" })
      : (/* ir:node:fresh-eeb81f32a8a7b14e-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-eeb81f32a8a7b14e-get-user */ capabilities.users.getById(/* ir:node:fresh-eeb81f32a8a7b14e-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-eeb81f32a8a7b14e-missing */ { error: /* ir:node:fresh-eeb81f32a8a7b14e-missing-code */ "not_found_eeb81f32a8a7b14e" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-eeb81f32a8a7b14e-found */ { ok: /* ir:node:fresh-eeb81f32a8a7b14e-user-ref */ user };
        })());
  })();
}
