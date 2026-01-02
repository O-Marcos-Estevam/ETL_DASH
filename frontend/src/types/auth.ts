/**
 * Authentication Types
 */

export type UserRole = 'admin' | 'viewer';

export interface User {
    id: number;
    username: string;
    email?: string;
    role: UserRole;
    is_active: boolean;
    created_at: string;
    last_login?: string;
}

export interface LoginRequest {
    username: string;
    password: string;
}

export interface LoginResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
    user: User;
}

export interface RefreshResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
}

export interface AuthState {
    user: User | null;
    accessToken: string | null;
    refreshToken: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
}

export interface AuthContextType extends AuthState {
    login: (username: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
    refreshAuth: () => Promise<boolean>;
    isAdmin: boolean;
}
