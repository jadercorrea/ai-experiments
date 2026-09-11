// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserA729634e6bd884740(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-729634e6bd884740-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-729634e6bd884740-normalizer */ (/* ir:node:fresh-729634e6bd884740-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-729634e6bd884740-validation */ (/* ir:node:fresh-729634e6bd884740-is-empty */ (/* ir:node:fresh-729634e6bd884740-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-729634e6bd884740-invalid */ { error: /* ir:node:fresh-729634e6bd884740-invalid-code */ "invalid_input_729634e6bd884740" })
      : (/* ir:node:fresh-729634e6bd884740-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-729634e6bd884740-get-user */ capabilities.users.getById(/* ir:node:fresh-729634e6bd884740-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-729634e6bd884740-missing */ { error: /* ir:node:fresh-729634e6bd884740-missing-code */ "not_found_729634e6bd884740" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-729634e6bd884740-found */ { ok: /* ir:node:fresh-729634e6bd884740-user-ref */ user };
        })());
  })();
}
