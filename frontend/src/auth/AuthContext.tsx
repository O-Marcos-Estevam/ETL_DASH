/**
 * Authentication Context Provider
 */
import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import type { User, AuthContextType } from '@/types/auth';
import {
    login as apiLogin,
    logout as apiLogout,
    refreshTokens,
    getCurrentUser,
    getAccessToken,
    getStoredUser,
    clearTokens,
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

    // Initialize auth state from storage
    useEffect(() => {
        const initAuth = async () => {
            const storedToken = getAccessToken();
            const storedUser = getStoredUser();

            if (storedToken && storedUser) {
                // Validate token by fetching current user
                const validUser = await getCurrentUser();
                if (validUser) {
                    setUser(validUser);
                    setAccessToken(storedToken);
                } else {
                    clearTokens();
                }
            }

            setIsLoading(false);
        };

        initAuth();
    }, []);

    // Auto-refresh token before expiry
    useEffect(() => {
        if (!accessToken) return;

        // Refresh 5 minutes before expiry (tokens expire in 30 min)
        const refreshInterval = setInterval(async () => {
            const result = await refreshTokens();
            if (result) {
                setAccessToken(result.access_token);
            } else {
                // Refresh failed, logout
                setUser(null);
                setAccessToken(null);
                setRefreshToken(null);
            }
        }, 25 * 60 * 1000); // 25 minutes

        return () => clearInterval(refreshInterval);
    }, [accessToken]);

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
