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
  const id = rawId.replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
  if (id.length === 0) {
    return { error: "invalid_user_id" };
  }

  const user = capabilities.users.getById(id);
  return user === undefined ? { error: "not_found" } : { ok: user };
}
