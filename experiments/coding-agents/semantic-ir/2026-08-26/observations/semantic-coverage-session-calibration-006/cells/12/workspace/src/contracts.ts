export const LOAD_CONTRACT = "loadUser" as const;
export type LoadUser = (id: string) => { id: string };
