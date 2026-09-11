// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAfe6ee001d9326d8b(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-fe6ee001d9326d8b-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-fe6ee001d9326d8b-normalizer */ (/* ir:node:fresh-fe6ee001d9326d8b-raw-after-normalization-patch */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-fe6ee001d9326d8b-validation */ (/* ir:node:fresh-fe6ee001d9326d8b-is-empty */ (/* ir:node:fresh-fe6ee001d9326d8b-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-fe6ee001d9326d8b-invalid */ { error: /* ir:node:fresh-fe6ee001d9326d8b-invalid-code */ "invalid_input_fe6ee001d9326d8b" })
      : (/* ir:node:fresh-fe6ee001d9326d8b-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-fe6ee001d9326d8b-get-user */ capabilities.users.getById(/* ir:node:fresh-fe6ee001d9326d8b-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-fe6ee001d9326d8b-missing */ { error: /* ir:node:fresh-fe6ee001d9326d8b-missing-code */ "not_found_fe6ee001d9326d8b" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-fe6ee001d9326d8b-found */ { ok: /* ir:node:fresh-fe6ee001d9326d8b-user-ref */ user };
        })());
  })();
}
