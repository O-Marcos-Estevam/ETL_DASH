import { useEffect, useState, useMemo, useCallback, useRef } from "react"
import { LogViewer } from "@/components/logs/log-viewer"
import { LogFilter } from "@/components/logs/log-filter"
import { api } from "@/services/api"
import { ws, type WSLogEntry, type JobCompletePayload } from "@/services/websocket"
import type { LogEntry } from "@/types/etl"
import { Wifi, WifiOff, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"

const MAX_LOGS = 1000; // Limit logs to prevent memory issues

export function LogsPage() {
    const [logs, setLogs] = useState<LogEntry[]>([])
    const [isConnected, setIsConnected] = useState(false)
    const [isPaused, setIsPaused] = useState(false)
    const [filterText, setFilterText] = useState("")
    const [jobId, setJobId] = useState<number | null>(null)
    const [jobStatus, setJobStatus] = useState<string>("idle")

    // Ref para acessar isPaused atual sem causar re-subscribe
    const isPausedRef = useRef(isPaused)
    isPausedRef.current = isPaused

    // Handle incoming log - estável, usa ref para isPaused
    const handleLog = useCallback((log: WSLogEntry) => {
        if (isPausedRef.current) return;

        // Filter by job_id if we have one
        const currentJobId = Number(localStorage.getItem('current_etl_job_id'));
        if (currentJobId && log.job_id && log.job_id !== currentJobId) {
            return; // Ignore logs from other jobs
        }

        setLogs(prev => {
            const newLogs = [...prev, log];
            // Keep only last MAX_LOGS entries
            return newLogs.slice(-MAX_LOGS);
        });
    }, []); // Sem dependências - usa ref

    // Handle job complete
    const handleJobComplete = useCallback((payload: JobCompletePayload) => {
        const currentJobId = Number(localStorage.getItem('current_etl_job_id'));
        if (payload.job_id === currentJobId) {
            setJobStatus(payload.status);
            console.log(`[Logs] Job ${payload.job_id} completed: ${payload.status} (${payload.duracao_segundos}s)`);
        }
    }, []);

    // Load initial job status on mount
    useEffect(() => {
        const storedJobId = localStorage.getItem('current_etl_job_id');
        if (storedJobId) {
            setJobId(Number(storedJobId));
            // Fetch initial job status
            api.getJobStatus(Number(storedJobId))
                .then(job => {
                    setJobStatus(job.status);
                    // Load existing logs if any
                    if (job.logs) {
                        const lines = job.logs.split('\n').filter((l: string) => l.trim());
                        const parsedLogs: LogEntry[] = lines.map((line: string) => {
                            let level: LogEntry['level'] = 'INFO';
                            if (line.includes('[ERROR]')) level = 'ERROR';
                            else if (line.includes('[WARN]')) level = 'WARN';
                            else if (line.includes('[SUCCESS]')) level = 'SUCCESS';

                            return {
                                timestamp: new Date().toISOString(),
                                level,
                                sistema: 'HISTORY',
                                mensagem: line
                            };
                        });
                        setLogs(parsedLogs);
                    }
                })
                .catch(err => console.warn('Failed to fetch job status:', err));
        }
    }, []); // Apenas no mount

    // Connect to WebSocket and subscribe to events
    useEffect(() => {
        const connectWS = async () => {
            try {
                ws.resetReconnect();
                await ws.connect();
            } catch (error) {
                console.warn('WebSocket connection failed:', error);
            }
        };

        connectWS();

        // Subscribe to events
        const unsubLog = ws.onLog(handleLog);
        const unsubJobComplete = ws.onJobComplete(handleJobComplete);
        const unsubConnection = ws.onConnectionChange(setIsConnected);

        return () => {
            unsubLog();
            unsubJobComplete();
            unsubConnection();
            ws.disconnect();
        };
    }, [handleLog, handleJobComplete])

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

    const handleReconnect = async () => {
        try {
            ws.resetReconnect();
            await ws.connect();
        } catch (error) {
            console.warn('Reconnect failed:', error);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'running': return 'text-blue-500 bg-blue-500/10';
            case 'completed': return 'text-green-500 bg-green-500/10';
            case 'error': return 'text-red-500 bg-red-500/10';
            default: return 'text-muted-foreground bg-muted/10';
        }
    };

    return (
        <div className="flex flex-col gap-4 h-[calc(100vh-6rem)]">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">System Logs</h2>
                    <p className="text-muted-foreground">
                        Job ID: {jobId || 'None'} | Status:{' '}
                        <span className={`font-mono font-bold uppercase px-2 py-0.5 rounded ${getStatusColor(jobStatus)}`}>
                            {jobStatus}
                        </span>
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    {isConnected ? (
                        <div className="flex items-center text-green-500 bg-green-500/10 px-3 py-1 rounded-full text-xs font-medium">
                            <Wifi className="w-3 h-3 mr-2" />
                            Live (WebSocket)
                        </div>
                    ) : (
                        <div className="flex items-center gap-2">
                            <div className="flex items-center text-red-500 bg-red-500/10 px-3 py-1 rounded-full text-xs font-medium">
                                <WifiOff className="w-3 h-3 mr-2" />
                                Disconnected
                            </div>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleReconnect}
                                className="h-7"
                            >
                                <RefreshCw className="w-3 h-3 mr-1" />
                                Reconnect
                            </Button>
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
