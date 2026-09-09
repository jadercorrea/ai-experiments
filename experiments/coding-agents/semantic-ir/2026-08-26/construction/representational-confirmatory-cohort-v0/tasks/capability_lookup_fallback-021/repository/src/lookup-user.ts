// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAe6f27d0c8d414b4b(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-e6f27d0c8d414b4b-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-e6f27d0c8d414b4b-normalizer */ (/* ir:node:fresh-e6f27d0c8d414b4b-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-e6f27d0c8d414b4b-validation */ (/* ir:node:fresh-e6f27d0c8d414b4b-is-empty */ (/* ir:node:fresh-e6f27d0c8d414b4b-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-e6f27d0c8d414b4b-invalid */ { error: /* ir:node:fresh-e6f27d0c8d414b4b-invalid-code */ "invalid_input_e6f27d0c8d414b4b" })
      : (/* ir:node:fresh-e6f27d0c8d414b4b-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-e6f27d0c8d414b4b-get-user */ capabilities.users.getById(/* ir:node:fresh-e6f27d0c8d414b4b-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-e6f27d0c8d414b4b-missing */ { error: /* ir:node:fresh-e6f27d0c8d414b4b-missing-code */ "not_found_e6f27d0c8d414b4b" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-e6f27d0c8d414b4b-found */ { ok: /* ir:node:fresh-e6f27d0c8d414b4b-user-ref */ user };
        })());
  })();
}
