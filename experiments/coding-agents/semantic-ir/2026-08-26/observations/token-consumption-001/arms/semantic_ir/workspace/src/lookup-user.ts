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
  void rawId;
  void capabilities;
  return { error: "not_implemented" };
}
