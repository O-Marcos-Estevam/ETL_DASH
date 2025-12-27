
import { useLocation, Link } from "react-router-dom"
import { cn } from "@/lib/utils"
/* import { Button } from "@/components/ui/button" */
import {
    Separator,
} from "@/components/ui/separator"
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"
import {
    LayoutDashboard,
    Terminal,
    Settings,
    Database,
    ChevronLeft,
    ChevronRight,
    PieChart
} from "lucide-react"
import { Button } from "../ui/button"

interface SidebarProps {
    isCollapsed: boolean
    setIsCollapsed: (collapsed: boolean) => void
}

export function Sidebar({ isCollapsed, setIsCollapsed }: SidebarProps) {
    const location = useLocation()

    const navItems = [
        {
            title: "Dashboard",
            href: "/",
            icon: LayoutDashboard,
            variant: "default"
        },
        {
            title: "ETL",
            href: "/etl",
            icon: Database,
            variant: "ghost"
        },
        {
            title: "Portfolio",
            href: "/portfolio",
            icon: PieChart,
            variant: "ghost"
        },
        {
            title: "Logs",
            href: "/logs",
            icon: Terminal,
            variant: "ghost"
        },
        {
            title: "Settings",
            href: "/settings",
            icon: Settings,
            variant: "ghost"
        }
    ]

    return (
        <div className={cn("relative flex flex-col border-r bg-background transition-all duration-300", isCollapsed ? "w-[50px]" : "w-[240px]")}>
            <div className="flex h-[52px] items-center justify-between px-2">
                {/* Logo Area */}
                {!isCollapsed && (
                    <div className="flex items-center gap-2 pl-2">
                        <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary text-primary-foreground font-bold text-xs">
                            ETL
                        </div>
                        <span className="text-sm font-semibold">Dashboard V2</span>
                    </div>
                )}
                <Button
                    variant="ghost"
                    size="icon"
                    className="ml-auto h-8 w-8"
                    onClick={() => setIsCollapsed(!isCollapsed)}
                >
                    {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
                </Button>
            </div>
            <Separator />
            <div className="flex-1 overflow-auto py-2">
                <nav className="grid gap-1 px-2 group-[[data-collapsed=true]]:justify-center group-[[data-collapsed=true]]:px-2">
                    <TooltipProvider delayDuration={0}>
                        {navItems.map((item, index) => {
                            const isActive = location.pathname === item.href
                            return (
                                isCollapsed ? (
                                    <Tooltip key={index} delayDuration={0}>
                                        <TooltipTrigger asChild>
                                            <Link
                                                to={item.href}
                                                className={cn(
                                                    "h-9 w-9 flex items-center justify-center rounded-md",
                                                    isActive
                                                        ? "bg-primary text-primary-foreground"
                                                        : "text-muted-foreground hover:bg-muted hover:text-primary"
                                                )}
                                            >
                                                <item.icon className="h-4 w-4" />
                                                <span className="sr-only">{item.title}</span>
                                            </Link>
                                        </TooltipTrigger>
                                        <TooltipContent side="right" className="flex items-center gap-4">
                                            {item.title}
                                        </TooltipContent>
                                    </Tooltip>
                                ) : (
                                    <Link
                                        key={index}
                                        to={item.href}
                                        className={cn(
                                            "justify-start text-sm font-medium h-9 px-2 py-2 flex items-center gap-2 rounded-md transition-colors",
                                            isActive
                                                ? "bg-primary text-primary-foreground"
                                                : "hover:bg-muted hover:text-primary text-muted-foreground"
                                        )}
                                    >
                                        <item.icon className="h-4 w-4" />
                                        {item.title}
                                    </Link>
                                )
                            )
                        })}
                    </TooltipProvider>
                </nav>
            </div>
        </div>
    )
}
