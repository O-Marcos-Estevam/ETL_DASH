import type { ApiResponse } from "@/types/etl";

const API_BASE = "http://localhost:4001/api";

export const ConfigService = {
    async getConfig(): Promise<any> {
        try {
            const res = await fetch(`${API_BASE}/config`);
            if (!res.ok) throw new Error("Failed to fetch config");
            return await res.json();
        } catch (error) {
            console.error(error);
            return {};
        }
    },

    async saveConfig(config: any): Promise<ApiResponse> {
        try {
            const res = await fetch(`${API_BASE}/config`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(config)
            });
            if (!res.ok) throw new Error("Failed to save config");
            return await res.json();
        } catch (error) {
            console.error(error);
            return { success: false, message: String(error) };
        }
    }
}
