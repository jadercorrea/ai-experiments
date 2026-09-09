// Generated deterministically from semantic IR. Do not edit.
export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function resolveUserAa2c5f9684125f744(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:fresh-a2c5f9684125f744-body */ (() => {
    const normalizedId: string = /* ir:node:fresh-a2c5f9684125f744-normalizer */ (/* ir:node:fresh-a2c5f9684125f744-raw-for-normalizer */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:fresh-a2c5f9684125f744-validation */ (/* ir:node:fresh-a2c5f9684125f744-is-empty */ (/* ir:node:fresh-a2c5f9684125f744-normalized-for-empty */ normalizedId).length === 0)
      ? (/* ir:node:fresh-a2c5f9684125f744-invalid */ { error: /* ir:node:fresh-a2c5f9684125f744-invalid-code */ "invalid_input_a2c5f9684125f744" })
      : (/* ir:node:fresh-a2c5f9684125f744-user-match */ (() => {
          const __semantic_ir_option_1 = /* ir:node:fresh-a2c5f9684125f744-get-user */ capabilities.users.getById(/* ir:node:fresh-a2c5f9684125f744-normalized-for-user */ normalizedId);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:fresh-a2c5f9684125f744-retry-guard */ (/* ir:node:fresh-a2c5f9684125f744-raw-equals-normalized */ (/* ir:node:fresh-a2c5f9684125f744-raw-for-guard */ rawId) === (/* ir:node:fresh-a2c5f9684125f744-normalized-for-guard */ normalizedId))
              ? (/* ir:node:fresh-a2c5f9684125f744-missing */ { error: /* ir:node:fresh-a2c5f9684125f744-missing-code */ "not_found_a2c5f9684125f744" })
              : (/* ir:node:fresh-a2c5f9684125f744-retry-match */ (() => {
                  const __semantic_ir_option_2 = /* ir:node:fresh-a2c5f9684125f744-retry-user */ capabilities.users.getById(/* ir:node:fresh-a2c5f9684125f744-raw-for-retry */ rawId);
                  if (__semantic_ir_option_2 === undefined) {
                    return /* ir:node:fresh-a2c5f9684125f744-retry-missing */ { error: /* ir:node:fresh-a2c5f9684125f744-retry-missing-code */ "not_found_a2c5f9684125f744" };
                  }
                  const retryUser: User = __semantic_ir_option_2;
                  return /* ir:node:fresh-a2c5f9684125f744-retry-found */ { ok: /* ir:node:fresh-a2c5f9684125f744-retry-user-ref */ retryUser };
                })());
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:fresh-a2c5f9684125f744-found */ { ok: /* ir:node:fresh-a2c5f9684125f744-user-ref */ user };
        })());
  })();
}
