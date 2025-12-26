import { format } from "date-fns"
import { AlertCircle, Info, AlertTriangle, CheckCircle2 } from "lucide-react"
import type { LogEntry } from "@/types/etl"

interface LogEntryRowProps {
    entry: LogEntry
    index: number
}

export function LogEntryRow({ entry, index }: LogEntryRowProps) {
    const getLevelColor = (level: string) => {
        switch (level.toUpperCase()) {
            case 'ERROR': return 'text-red-400'
            case 'WARN': return 'text-yellow-400'
            case 'SUCCESS': return 'text-green-400'
            default: return 'text-blue-400'
        }
    }

    const getIcon = (level: string) => {
        switch (level.toUpperCase()) {
            case 'ERROR': return <AlertCircle className="h-4 w-4 text-red-400" />
            case 'WARN': return <AlertTriangle className="h-4 w-4 text-yellow-400" />
            case 'SUCCESS': return <CheckCircle2 className="h-4 w-4 text-green-400" />
            default: return <Info className="h-4 w-4 text-blue-400" />
        }
    }

    return (
        <div className={`flex items-start gap-3 py-1 px-2 font-mono text-xs sm:text-sm hover:bg-white/5 ${index % 2 === 0 ? 'bg-black/20' : ''}`}>
            <span className="text-gray-500 whitespace-nowrap pt-0.5">
                {format(new Date(entry.timestamp), "HH:mm:ss.SSS")}
            </span>

            <span className={`flex items-center gap-1 font-bold ${getLevelColor(entry.level)} uppercase w-20 pt-0.5`}>
                {getIcon(entry.level)}
                {entry.level}
            </span>

            <span className="flex-1 break-all text-gray-300">
                <span className="font-semibold text-gray-500 mr-2">[{entry.sistema}]</span>
                {entry.mensagem}
            </span>
        </div>
    )
}
