export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function lookupUser01(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const id = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
  if (id === '') return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}

export function lookupUser02(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const id = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
  if (id === '') return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}

export function lookupUser03(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const id = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
  if (id === '') return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}

export function lookupUser04(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const id = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
  if (id === '') return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}

export function lookupUser05(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const id = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
  if (id === '') return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}

export function lookupUser06(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const id = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
  if (id === '') return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}

export function lookupUser07(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const id = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
  if (id === '') return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}

export function lookupUser08(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const id = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
  if (id === '') return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}

export function lookupUser09(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const id = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
  if (id === '') return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}

export function lookupUser10(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const id = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
  if (id === '') return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}

export function lookupUser11(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const id = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
  if (id === '') return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}

export function lookupUser12(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const id = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
  if (id === '') return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}

export function lookupUser13(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const id = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
  if (id === '') return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}

export function lookupUser14(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const id = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
  if (id === '') return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}

export function lookupUser15(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const id = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
  if (id === '') return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}

export function lookupUser16(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const id = rawId.replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
  if (id === '') return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}
