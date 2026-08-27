export const FETCH_CONTRACT = "fetchUser" as const;
export type FetchUser = (id: string) => { id: string };
