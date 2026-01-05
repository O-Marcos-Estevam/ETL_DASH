/**
 * Authentication API Service
 *
 * Features:
 * - JWT token management with expiration handling
 * - Auto-refresh before token expires
 * - Validation on load
 */
import type { LoginRequest, LoginResponse, RefreshResponse, User } from '@/types/auth';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:4001/api';

// Token storage keys
const ACCESS_TOKEN_KEY = 'etl_access_token';
const REFRESH_TOKEN_KEY = 'etl_refresh_token';
const USER_KEY = 'etl_user';
const TOKEN_EXPIRY_KEY = 'etl_token_expiry';

// Refresh token 5 minutes before expiry
const REFRESH_THRESHOLD_MS = 5 * 60 * 1000;

// Auto-refresh timer
let refreshTimer: ReturnType<typeof setTimeout> | null = null;

// Callback for auth state changes (set by AuthContext)
let onAuthExpired: (() => void) | null = null;

/**
 * Set callback for when authentication expires
 */
export function setAuthExpiredCallback(callback: (() => void) | null): void {
    onAuthExpired = callback;
}

/**
 * Parse JWT token to extract payload (without verification)
 */
function parseJwt(token: string): { exp?: number; [key: string]: unknown } | null {
    try {
        const base64Url = token.split('.')[1];
        if (!base64Url) return null;

        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
            atob(base64)
                .split('')
                .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                .join('')
        );
        return JSON.parse(jsonPayload);
    } catch {
        return null;
    }
}

/**
 * Get token expiry time in milliseconds
 */
function getTokenExpiry(token: string): number | null {
    const payload = parseJwt(token);
    if (payload?.exp) {
        return payload.exp * 1000; // Convert to milliseconds
    }
    return null;
}

/**
 * Check if token is expired
 */
export function isTokenExpired(token: string | null): boolean {
    if (!token) return true;

    const expiry = getTokenExpiry(token);
    if (!expiry) return true;

    return Date.now() >= expiry;
}

/**
 * Check if token will expire within threshold
 */
export function isTokenExpiringSoon(token: string | null): boolean {
    if (!token) return true;

    const expiry = getTokenExpiry(token);
    if (!expiry) return true;

    return Date.now() >= (expiry - REFRESH_THRESHOLD_MS);
}

/**
 * Get time until token expires (in ms)
 */
export function getTimeUntilExpiry(token: string | null): number {
    if (!token) return 0;

    const expiry = getTokenExpiry(token);
    if (!expiry) return 0;

    return Math.max(0, expiry - Date.now());
}

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

    // Store expiry time for quick checks
    const expiry = getTokenExpiry(accessToken);
    if (expiry) {
        localStorage.setItem(TOKEN_EXPIRY_KEY, expiry.toString());
    }

    // Schedule auto-refresh
    scheduleTokenRefresh(accessToken);
}

export function clearTokens(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);

    // Clear refresh timer
    if (refreshTimer) {
        clearTimeout(refreshTimer);
        refreshTimer = null;
    }
}

/**
 * Schedule automatic token refresh before expiry
 */
function scheduleTokenRefresh(token: string): void {
    // Clear existing timer
    if (refreshTimer) {
        clearTimeout(refreshTimer);
        refreshTimer = null;
    }

    const timeUntilExpiry = getTimeUntilExpiry(token);
    if (timeUntilExpiry <= 0) return;

    // Schedule refresh before expiry (with threshold)
    const refreshIn = Math.max(0, timeUntilExpiry - REFRESH_THRESHOLD_MS);

    console.log(`[Auth] Token refresh scheduled in ${Math.round(refreshIn / 1000 / 60)} minutes`);

    refreshTimer = setTimeout(async () => {
        console.log('[Auth] Auto-refreshing token...');
        const result = await refreshTokens();
        if (!result) {
            console.log('[Auth] Auto-refresh failed, session expired');
            onAuthExpired?.();
        }
    }, refreshIn);
}

/**
 * Validate stored tokens on app load
 * Returns true if tokens are valid (or successfully refreshed)
 */
export async function validateStoredTokens(): Promise<boolean> {
    const accessToken = getAccessToken();
    const refreshToken = getRefreshToken();

    // No tokens stored
    if (!accessToken || !refreshToken) {
        return false;
    }

    // Access token still valid
    if (!isTokenExpired(accessToken)) {
        // Schedule refresh if not already scheduled
        scheduleTokenRefresh(accessToken);

        // If expiring soon, refresh proactively
        if (isTokenExpiringSoon(accessToken)) {
            console.log('[Auth] Token expiring soon, refreshing...');
            const result = await refreshTokens();
            return result !== null;
        }

        return true;
    }

    // Access token expired, try refresh
    console.log('[Auth] Access token expired, attempting refresh...');
    const result = await refreshTokens();
    return result !== null;
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
    // Token expiration utilities
    isTokenExpired,
    isTokenExpiringSoon,
    getTimeUntilExpiry,
    validateStoredTokens,
    setAuthExpiredCallback,
};

export default authApi;
