import type { ApiResponse } from "@/types/etl";

const API_BASE = "http://localhost:4001/api";

export interface ExecuteParams {
    sistemas: string[];
    dry_run?: boolean;
    limpar?: boolean;
    data_inicial?: string;
    data_final?: string;
}

export const ExecutionService = {
    async runJob(params: ExecuteParams): Promise<ApiResponse> {
        try {
            const res = await fetch(`${API_BASE}/execute`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(params)
            });

            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.detail || "Failed to trigger execution");
            }

            return await res.json();
        } catch (error) {
            console.error(error);
            return { success: false, message: String(error) };
        }
    }
}
