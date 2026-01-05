/**
 * Authentication Context Provider
 *
 * Features:
 * - JWT token expiration validation on load
 * - Automatic token refresh before expiry
 * - Silent expiration handling
 */
import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import type { User, AuthContextType } from '@/types/auth';
import {
    login as apiLogin,
    logout as apiLogout,
    refreshTokens,
    getCurrentUser,
    getAccessToken,
    clearTokens,
    validateStoredTokens,
    setAuthExpiredCallback,
} from '@/services/authApi';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
    children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
    const [user, setUser] = useState<User | null>(null);
    const [accessToken, setAccessToken] = useState<string | null>(null);
    const [refreshToken, setRefreshToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Handle silent token expiration
    const handleAuthExpired = useCallback(() => {
        console.log('[AuthContext] Session expired, logging out');
        setUser(null);
        setAccessToken(null);
        setRefreshToken(null);
        clearTokens();
    }, []);

    // Register auth expired callback
    useEffect(() => {
        setAuthExpiredCallback(handleAuthExpired);
        return () => setAuthExpiredCallback(null);
    }, [handleAuthExpired]);

    // Initialize auth state from storage with token validation
    useEffect(() => {
        const initAuth = async () => {
            try {
                // First, validate stored tokens (handles expiration + auto-refresh)
                const tokensValid = await validateStoredTokens();

                if (!tokensValid) {
                    console.log('[AuthContext] No valid tokens found');
                    setIsLoading(false);
                    return;
                }

                // Tokens are valid, get current user
                const storedToken = getAccessToken();
                const validUser = await getCurrentUser();

                if (validUser && storedToken) {
                    setUser(validUser);
                    setAccessToken(storedToken);
                    console.log('[AuthContext] Session restored for:', validUser.username);
                } else {
                    // Token validation passed but user fetch failed
                    clearTokens();
                }
            } catch (error) {
                console.error('[AuthContext] Init error:', error);
                clearTokens();
            } finally {
                setIsLoading(false);
            }
        };

        initAuth();
    }, []);

    const login = useCallback(async (username: string, password: string) => {
        setIsLoading(true);
        try {
            const response = await apiLogin({ username, password });
            setUser(response.user);
            setAccessToken(response.access_token);
            setRefreshToken(response.refresh_token);
        } finally {
            setIsLoading(false);
        }
    }, []);

    const logout = useCallback(async () => {
        setIsLoading(true);
        try {
            await apiLogout();
        } finally {
            setUser(null);
            setAccessToken(null);
            setRefreshToken(null);
            setIsLoading(false);
        }
    }, []);

    const refreshAuth = useCallback(async (): Promise<boolean> => {
        const result = await refreshTokens();
        if (result) {
            setAccessToken(result.access_token);
            setRefreshToken(result.refresh_token);
            return true;
        }
        return false;
    }, []);

    const value: AuthContextType = {
        user,
        accessToken,
        refreshToken,
        isAuthenticated: !!user && !!accessToken,
        isLoading,
        isAdmin: user?.role === 'admin',
        login,
        logout,
        refreshAuth,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth(): AuthContextType {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

export { AuthContext };
