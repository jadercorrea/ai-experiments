export interface User {
  readonly id: string;
  readonly name: string;
}

export type Result<T, E> = { ok: T } | { error: E };

export interface SemanticCapabilities {
  readonly users: {
    getById(id: string): User | undefined;
  };
}

export function lookupUser(
  rawId: string,
  capabilities: SemanticCapabilities,
): Result<User, string> {
  const normalized = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, "");
  if (normalized === "") {
    return { error: "invalid_user_id" };
  }
  const user = capabilities.users.getById(normalized);
  if (user === undefined) {
    return { error: "not_found" };
  }
  return { ok: user };
}
