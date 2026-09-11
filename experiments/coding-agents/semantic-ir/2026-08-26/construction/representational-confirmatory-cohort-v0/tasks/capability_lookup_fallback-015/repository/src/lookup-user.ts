// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA2781b23f0645d130(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-2781b23f0645d130-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-2781b23f0645d130-normalizer */ (/* ir:node:fresh-2781b23f0645d130-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-2781b23f0645d130-validation */ (/* ir:node:fresh-2781b23f0645d130-is-empty */ (/* ir:node:fresh-2781b23f0645d130-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-2781b23f0645d130-invalid */ { error: /* ir:node:fresh-2781b23f0645d130-invalid-code */ "invalid_input_2781b23f0645d130" })
      : (/* ir:node:fresh-2781b23f0645d130-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-2781b23f0645d130-get-user */ capabilities.users.getById(/* ir:node:fresh-2781b23f0645d130-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-2781b23f0645d130-missing */ { error: /* ir:node:fresh-2781b23f0645d130-missing-code */ "not_found_2781b23f0645d130" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-2781b23f0645d130-found */ { ok: /* ir:node:fresh-2781b23f0645d130-user-ref */ user };
        })());
  })();
}
