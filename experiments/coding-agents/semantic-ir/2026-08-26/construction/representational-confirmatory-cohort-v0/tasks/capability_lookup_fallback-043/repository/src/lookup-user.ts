// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA52b14377545ed412(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-52b14377545ed412-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-52b14377545ed412-normalizer */ (/* ir:node:fresh-52b14377545ed412-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-52b14377545ed412-validation */ (/* ir:node:fresh-52b14377545ed412-is-empty */ (/* ir:node:fresh-52b14377545ed412-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-52b14377545ed412-invalid */ { error: /* ir:node:fresh-52b14377545ed412-invalid-code */ "invalid_input_52b14377545ed412" })
      : (/* ir:node:fresh-52b14377545ed412-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-52b14377545ed412-get-user */ capabilities.users.getById(/* ir:node:fresh-52b14377545ed412-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-52b14377545ed412-missing */ { error: /* ir:node:fresh-52b14377545ed412-missing-code */ "not_found_52b14377545ed412" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-52b14377545ed412-found */ { ok: /* ir:node:fresh-52b14377545ed412-user-ref */ user };
        })());
  })();
}
