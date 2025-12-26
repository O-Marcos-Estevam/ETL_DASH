import { useEffect, useState, useMemo, useRef } from "react"
import { LogViewer } from "@/components/logs/log-viewer"
import { LogFilter } from "@/components/logs/log-filter"
import { api } from "@/services/api"
import type { LogEntry } from "@/types/etl"
import { Wifi, WifiOff, Loader2 } from "lucide-react"

export function LogsPage() {
    const [logs, setLogs] = useState<LogEntry[]>([])
    const [isConnected, setIsConnected] = useState(false)
    const [isPaused, setIsPaused] = useState(false)
    const [filterText, setFilterText] = useState("")
    const [jobId, setJobId] = useState<string | null>(null)
    const [jobStatus, setJobStatus] = useState<string>("unknown")

    // Configura polling
    useEffect(() => {
        // Recuperar ID do job
        const storedJobId = localStorage.getItem('current_etl_job_id')
        if (storedJobId) {
            setJobId(storedJobId)
            setIsConnected(true)
        }

        if (!storedJobId) return

        const pollLogs = async () => {
            if (isPaused) return

            try {
                const job = await api.getJobStatus(Number(storedJobId))
                setJobStatus(job.status)

                if (job.logs) {
                    // Parse logs from text blob
                    const lines = job.logs.split('\n')
                    const parsedLogs: LogEntry[] = lines.map((line: string, index: number) => {
                        if (!line.trim()) return null

                        // Tentar extrair level e timestamp se possível, ou usar defaults
                        let level = 'INFO'
                        if (line.includes('ERROR') || line.includes('Erro')) level = 'ERROR'
                        if (line.includes('WARN')) level = 'WARN'
                        if (line.includes('SUCCESS')) level = 'SUCCESS'

                        return {
                            id: `${job.id}-${index}`,
                            timestamp: new Date().toLocaleTimeString(), // Fallback
                            level: level as any,
                            sistema: 'ETL',
                            mensagem: line
                        }
                    }).filter(Boolean) as LogEntry[]

                    setLogs(parsedLogs)
                }

                if (job.status === 'completed' || job.status === 'error') {
                    // Stop polling eventually? No, user might want to see final state.
                    // Maybe reduce frequency.
                }

                setIsConnected(true)
            } catch (error) {
                console.error("Polling error:", error)
                setIsConnected(false)
            }
        }

        // Poll every 2 seconds
        const intervalId = setInterval(pollLogs, 2000)
        pollLogs() // Initial call

        return () => clearInterval(intervalId)
    }, [isPaused, jobId])

    const [levels, setLevels] = useState<Record<string, boolean>>({
        INFO: true,
        WARN: true,
        ERROR: true,
        SUCCESS: true
    })

    // Filter logs
    const filteredLogs = useMemo(() => {
        return logs.filter(log => {
            const matchesText =
                log.mensagem.toLowerCase().includes(filterText.toLowerCase()) ||
                log.sistema.toLowerCase().includes(filterText.toLowerCase())

            const matchesLevel = levels[log.level] ?? true

            return matchesText && matchesLevel
        })
    }, [logs, filterText, levels])

    const handleClear = () => setLogs([])

    const handleDownload = () => {
        const content = logs.map(l => `[${l.timestamp}] [${l.level}] [${l.sistema}] ${l.mensagem}`).join('\n')
        const blob = new Blob([content], { type: 'text/plain' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `etl-logs-${new Date().toISOString()}.txt`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
    }

    const toggleLevel = (level: string) => {
        setLevels(prev => ({ ...prev, [level]: !prev[level] }))
    }

    return (
        <div className="flex flex-col gap-4 h-[calc(100vh-6rem)]">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">System Logs</h2>
                    <p className="text-muted-foreground">
                        Job ID: {jobId || 'None'} | Status: <span className="font-mono font-bold uppercase">{jobStatus}</span>
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    {isConnected ? (
                        <div className="flex items-center text-green-500 bg-green-500/10 px-3 py-1 rounded-full text-xs font-medium">
                            <Wifi className="w-3 h-3 mr-2" />
                            Live (Polling)
                        </div>
                    ) : (
                        <div className="flex items-center text-red-500 bg-red-500/10 px-3 py-1 rounded-full text-xs font-medium">
                            <WifiOff className="w-3 h-3 mr-2" />
                            Disconnected
                        </div>
                    )}
                </div>
            </div>

            <LogFilter
                filterText={filterText}
                onFilterTextChange={setFilterText}
                onClear={handleClear}
                onDownload={handleDownload}
                levels={levels}
                onToggleLevel={toggleLevel}
            />

            <LogViewer
                logs={filteredLogs}
                isPaused={isPaused}
                onTogglePause={() => setIsPaused(!isPaused)}
            />
        </div>
    )
}
