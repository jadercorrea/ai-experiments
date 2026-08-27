export const LOOKUP_CONTRACT = "readUser" as const;
export type ReadUser = (id: string) => { id: string };
