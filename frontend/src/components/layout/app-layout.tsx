import { useState, useEffect } from "react"
import { Sidebar } from "./sidebar"
import { Header } from "./header"

interface AppLayoutProps {
    children: React.ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
    /* Get collapsed state from local storage or default to false */
    const [isCollapsed, setIsCollapsed] = useState(() => {
        const saved = localStorage.getItem("sidebar-collapsed")
        return saved ? JSON.parse(saved) : false
    })

    /* Persist collapsed state */
    useEffect(() => {
        localStorage.setItem("sidebar-collapsed", JSON.stringify(isCollapsed))
    }, [isCollapsed])

    return (
        <div className="flex h-screen overflow-hidden bg-background">
            <Sidebar isCollapsed={isCollapsed} setIsCollapsed={setIsCollapsed} />
            <div className="flex flex-col flex-1 overflow-hidden">
                <Header />
                <main className="flex-1 overflow-y-auto p-6">
                    {children}
                </main>
            </div>
        </div>
    )
}
