export const EXECUTE_CONTRACT = "executeUser" as const;
export type ExecuteUser = (id: string) => { id: string };
