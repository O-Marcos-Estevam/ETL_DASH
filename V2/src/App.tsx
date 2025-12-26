import { BrowserRouter as Router, Routes, Route } from "react-router-dom"
import { AppLayout } from "@/components/layout/app-layout"
import { DashboardPage } from "@/pages/dashboard/page"
import { EtlPage } from "@/pages/etl/page"
import { PortfolioPage } from "@/pages/portfolio/page"
import { LogsPage } from "@/pages/logs/page"
import { SettingsPage } from "@/pages/settings/page"

import { Toaster } from "@/components/ui/toaster"

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/etl" element={<EtlPage />} />
          <Route path="/portfolio" element={<PortfolioPage />} />
          <Route path="/logs" element={<LogsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
        <Toaster />
      </AppLayout>
    </Router>
  )
}

export default App
