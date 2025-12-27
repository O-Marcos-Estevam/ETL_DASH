import { ModeToggle } from "@/components/mode-toggle"

export function Header() {
    return (
        <header className="flex h-[52px] items-center gap-4 border-b bg-background px-6">
            <h1 className="text-lg font-semibold">Dashboard</h1>
            <div className="ml-auto flex items-center gap-2">
                <ModeToggle />
            </div>
        </header>
    )
}
