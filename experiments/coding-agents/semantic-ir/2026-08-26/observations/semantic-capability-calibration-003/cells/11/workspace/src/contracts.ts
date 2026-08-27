export const PROCESS_CONTRACT = "processUser" as const;
export type ProcessUser = (id: string) => { id: string };
