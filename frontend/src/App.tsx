import { BrowserRouter as Router, Routes, Route } from "react-router-dom"
import { AppLayout } from "@/components/layout/app-layout"
import { DashboardPage } from "@/pages/dashboard/page"
import { EtlPage } from "@/pages/etl/page"
import { PortfolioPage } from "@/pages/portfolio/page"
import { LogsPage } from "@/pages/logs/page"
import { SettingsPage } from "@/pages/settings/page"
import { LoginPage } from "@/pages/auth/LoginPage"

import { Toaster } from "@/components/ui/toaster"
import { AuthProvider, ProtectedRoute } from "@/auth"

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public route */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected routes */}
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <Routes>
                    <Route path="/" element={<DashboardPage />} />
                    <Route path="/etl" element={<EtlPage />} />
                    <Route path="/portfolio" element={<PortfolioPage />} />
                    <Route path="/logs" element={<LogsPage />} />
                    <Route path="/settings" element={
                      <ProtectedRoute requiredRole="admin">
                        <SettingsPage />
                      </ProtectedRoute>
                    } />
                  </Routes>
                  <Toaster />
                </AppLayout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  )
}

export default App
