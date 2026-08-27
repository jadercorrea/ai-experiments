export const RESOLVE_CONTRACT = "resolveUser" as const;
export type ResolveUser = (id: string) => { id: string };
