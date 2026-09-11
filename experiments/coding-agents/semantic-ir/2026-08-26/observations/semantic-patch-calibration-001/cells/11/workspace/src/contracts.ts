export const LOOKUP_CONTRACT = "lookupUser" as const;
export type LookupUser = (id: string) => { id: string };
