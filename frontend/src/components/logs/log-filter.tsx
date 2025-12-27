import { Search, Filter, Ban, Download } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuCheckboxItem,
    DropdownMenuContent,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

interface LogFilterProps {
    filterText: string
    onFilterTextChange: (text: string) => void
    onClear: () => void
    onDownload: () => void
    levels: Record<string, boolean>
    onToggleLevel: (level: string) => void
}

export function LogFilter({
    filterText,
    onFilterTextChange,
    onClear,
    onDownload,
    levels,
    onToggleLevel
}: LogFilterProps) {
    return (
        <div className="flex flex-col sm:flex-row gap-3 items-center justify-between p-2 bg-background border rounded-lg">
            <div className="flex items-center gap-2 w-full sm:w-auto flex-1">
                <div className="relative w-full max-w-sm">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search logs..."
                        value={filterText}
                        onChange={(e) => onFilterTextChange(e.target.value)}
                        className="pl-8 h-9"
                    />
                </div>

                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="outline" size="sm" className="h-9">
                            <Filter className="mr-2 h-4 w-4" />
                            Levels
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-56">
                        <DropdownMenuLabel>Filter by Level</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        {Object.keys(levels).map(level => (
                            <DropdownMenuCheckboxItem
                                key={level}
                                checked={levels[level]}
                                onCheckedChange={() => onToggleLevel(level)}
                            >
                                {level}
                            </DropdownMenuCheckboxItem>
                        ))}
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                <Button variant="outline" size="sm" onClick={onDownload} className="h-9">
                    <Download className="mr-2 h-4 w-4" />
                    Export
                </Button>
                <Button variant="destructive" size="sm" onClick={onClear} className="h-9">
                    <Ban className="mr-2 h-4 w-4" />
                    Clear
                </Button>
            </div>
        </div>
    )
}
