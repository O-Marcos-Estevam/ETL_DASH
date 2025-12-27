import {
    BarChart3,
    Map,
    FileSpreadsheet,
    Database,
    Server,
    FileCode,
    Box,
    Activity
} from "lucide-react"

export const SystemIcon = ({ name, className }: { name: string; className?: string }) => {
    const icons: Record<string, any> = {
        "BarChart3": BarChart3,
        "Map": Map,
        "FileSpreadsheet": FileSpreadsheet,
        "Database": Database,
        "Server": Server,
        "FileCode": FileCode,
        "Activity": Activity
    }

    const IconComponent = icons[name] || Box

    return <IconComponent className={className} />
}
