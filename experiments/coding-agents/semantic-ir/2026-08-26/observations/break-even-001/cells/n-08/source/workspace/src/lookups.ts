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
  if (id.length === 0) return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}

export function lookupUser03(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const id = rawId.replace(/^[\x20\x09\x0A\x0B\x0C\x0D]+|[\x20\x09\x0A\x0B\x0C\x0D]+$/g, '');
  if (!id) return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  if (user === undefined) return { error: 'not_found' };
  return { ok: user };
}

export function lookupUser04(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  let start = 0;
  let end = rawId.length;
  const ws = new Set([' ', '\t', '\n', '\v', '\f', '\r']);
  while (start < end && ws.has(rawId[start])) start++;
  while (end > start && ws.has(rawId[end - 1])) end--;
  const id = rawId.slice(start, end);
  if (id === '') return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}

export function lookupUser05(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const ASCII_WS = /^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g;
  const id = rawId.replace(ASCII_WS, '');
  if (id === '') return { error: 'invalid_user_id' };
  const result = capabilities.users.getById(id);
  return result !== undefined ? { ok: result } : { error: 'not_found' };
}

export function lookupUser06(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  function trimAsciiWs(s: string): string {
    let i = 0, j = s.length;
    while (i < j && ' \t\n\v\f\r'.includes(s[i])) i++;
    while (j > i && ' \t\n\v\f\r'.includes(s[j - 1])) j--;
    return s.slice(i, j);
  }
  const id = trimAsciiWs(rawId);
  if (id === '') return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}

export function lookupUser07(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const id = rawId.replace(/^[ \t\n\v\f\r]*(.*?)[ \t\n\v\f\r]*$/, '$1');
  if (id === '') return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(id);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}

export function lookupUser08(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  const chars = Array.from(' \t\n\v\f\r');
  let s = rawId;
  while (s.length > 0 && chars.includes(s[0])) s = s.slice(1);
  while (s.length > 0 && chars.includes(s[s.length - 1])) s = s.slice(0, -1);
  if (s === '') return { error: 'invalid_user_id' };
  const user = capabilities.users.getById(s);
  return user !== undefined ? { ok: user } : { error: 'not_found' };
}
