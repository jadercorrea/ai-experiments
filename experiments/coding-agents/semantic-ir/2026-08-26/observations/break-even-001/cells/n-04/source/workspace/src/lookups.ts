export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function lookupUser01(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const trimmed = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
  if (trimmed.length === 0) return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(trimmed);
  if (user === undefined) return { error: 'not_found' };
  return { ok: user };
}

export function lookupUser02(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const trimmed = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
  if (trimmed.length === 0) return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(trimmed);
  if (user === undefined) return { error: 'not_found' };
  return { ok: user };
}

export function lookupUser03(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const trimmed = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
  if (trimmed.length === 0) return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(trimmed);
  if (user === undefined) return { error: 'not_found' };
  return { ok: user };
}

export function lookupUser04(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const trimmed = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
  if (trimmed.length === 0) return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(trimmed);
  if (user === undefined) return { error: 'not_found' };
  return { ok: user };
}
