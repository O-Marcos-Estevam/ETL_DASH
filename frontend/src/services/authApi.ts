/**
 * Authentication API Service
 */
import type { LoginRequest, LoginResponse, RefreshResponse, User } from '@/types/auth';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:4001/api';

// Token storage keys
const ACCESS_TOKEN_KEY = 'etl_access_token';
const REFRESH_TOKEN_KEY = 'etl_refresh_token';
const USER_KEY = 'etl_user';

// Token management
export function getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function getStoredUser(): User | null {
    const userJson = localStorage.getItem(USER_KEY);
    if (userJson) {
        try {
            return JSON.parse(userJson);
        } catch {
            return null;
        }
    }
    return null;
}

export function storeTokens(accessToken: string, refreshToken: string, user: User): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearTokens(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}

// API calls
export async function login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Erro de login' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    const data: LoginResponse = await response.json();
    storeTokens(data.access_token, data.refresh_token, data.user);
    return data;
}

export async function refreshTokens(): Promise<RefreshResponse | null> {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
        return null;
    }

    try {
        const response = await fetch(`${API_BASE}/auth/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (!response.ok) {
            clearTokens();
            return null;
        }

        const data: RefreshResponse = await response.json();

        // Update stored tokens
        const user = getStoredUser();
        if (user) {
            storeTokens(data.access_token, data.refresh_token, user);
        }

        return data;
    } catch {
        clearTokens();
        return null;
    }
}

export async function logout(): Promise<void> {
    const accessToken = getAccessToken();
    const refreshToken = getRefreshToken();

    // Best effort - logout on server
    if (accessToken && refreshToken) {
        try {
            await fetch(`${API_BASE}/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh_token: refreshToken }),
            });
        } catch {
            // Ignore errors - clear local tokens anyway
        }
    }

    clearTokens();
}

export async function getCurrentUser(): Promise<User | null> {
    const accessToken = getAccessToken();
    if (!accessToken) {
        return null;
    }

    try {
        const response = await fetch(`${API_BASE}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`,
            },
        });

        if (!response.ok) {
            if (response.status === 401) {
                // Token expired, try refresh
                const refreshed = await refreshTokens();
                if (refreshed) {
                    return getCurrentUser();
                }
            }
            clearTokens();
            return null;
        }

        return response.json();
    } catch {
        return null;
    }
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
    const accessToken = getAccessToken();
    if (!accessToken) {
        throw new Error('Não autenticado');
    }

    const response = await fetch(`${API_BASE}/auth/change-password`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword,
        }),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Erro ao alterar senha' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }
}

export const authApi = {
    login,
    logout,
    refreshTokens,
    getCurrentUser,
    changePassword,
    getAccessToken,
    getRefreshToken,
    getStoredUser,
    storeTokens,
    clearTokens,
};

export default authApi;
