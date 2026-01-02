import { ModeToggle } from "@/components/mode-toggle"
import { useAuth } from "@/auth"
import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Badge } from "@/components/ui/badge"

export function Header() {
    const { user, logout, isAdmin } = useAuth()

    const handleLogout = async () => {
        try {
            await logout()
        } catch (error) {
            console.error('Erro ao fazer logout:', error)
        }
    }

    return (
        <header className="flex h-[52px] items-center gap-4 border-b bg-background px-6">
            <h1 className="text-lg font-semibold">Dashboard</h1>
            <div className="ml-auto flex items-center gap-3">
                <ModeToggle />

                {user && (
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="flex items-center gap-2 px-2">
                                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                                    <span className="text-sm font-medium text-primary">
                                        {user.username.charAt(0).toUpperCase()}
                                    </span>
                                </div>
                                <span className="hidden sm:inline-block text-sm">
                                    {user.username}
                                </span>
                                {isAdmin && (
                                    <Badge variant="secondary" className="hidden sm:inline-flex text-xs">
                                        Admin
                                    </Badge>
                                )}
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-48">
                            <DropdownMenuLabel>
                                <div className="flex flex-col">
                                    <span>{user.username}</span>
                                    <span className="text-xs font-normal text-muted-foreground">
                                        {user.role === 'admin' ? 'Administrador' : 'Visualizador'}
                                    </span>
                                </div>
                            </DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                                onClick={handleLogout}
                                className="text-destructive focus:text-destructive cursor-pointer"
                            >
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="2"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    className="mr-2 h-4 w-4"
                                >
                                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                                    <polyline points="16 17 21 12 16 7" />
                                    <line x1="21" y1="12" x2="9" y2="12" />
                                </svg>
                                Sair
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                )}
            </div>
        </header>
    )
}
