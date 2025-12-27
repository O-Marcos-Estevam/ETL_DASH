import { useRef, useEffect, useState } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { PauseCircle, PlayCircle, ArrowDown } from "lucide-react"
import { LogEntryRow } from "./log-entry-row"
import type { LogEntry } from "@/types/etl"

interface LogViewerProps {
    logs: LogEntry[]
    isPaused: boolean
    onTogglePause: () => void
}

export function LogViewer({ logs, isPaused, onTogglePause }: LogViewerProps) {
    const scrollRef = useRef<HTMLDivElement>(null)
    const [autoScroll, setAutoScroll] = useState(true)

    // Auto-scroll logic
    useEffect(() => {
        if (autoScroll && !isPaused && scrollRef.current) {
            // Find the generic viewport div created by Radix ScrollArea
            const viewport = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]');
            if (viewport) {
                viewport.scrollTop = viewport.scrollHeight;
            }
        }
    }, [logs, autoScroll, isPaused])

    const handleScroll = (_event: any) => {
        // Simple detection: if user scrolls up, disable auto-scroll
        // const viewport = event.target;
        // Logic can be improved, for now manual toggle is safer
    }

    return (
        <div className="relative border rounded-lg overflow-hidden bg-[#0c0c0c] h-[600px] flex flex-col shadow-inner">
            {/* Terminal Header */}
            <div className="flex items-center justify-between px-4 py-2 bg-muted/10 border-b border-white/10 text-xs text-muted-foreground">
                <div className="flex gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500/50" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500/50" />
                    <div className="w-3 h-3 rounded-full bg-green-500/50" />
                    <span className="ml-2">Console Output</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="tabular-nums">{logs.length} lines</span>
                    <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 hover:bg-white/10"
                        onClick={onTogglePause}
                        title={isPaused ? "Resume" : "Pause"}
                    >
                        {isPaused ? <PlayCircle className="h-4 w-4 animate-pulse text-yellow-500" /> : <PauseCircle className="h-4 w-4" />}
                    </Button>
                </div>
            </div>

            {/* Logs Area */}
            <ScrollArea
                ref={scrollRef}
                className="flex-1 p-2 font-mono text-sm"
                onScrollCapture={handleScroll}
            >
                <div className="pb-4">
                    {logs.length === 0 ? (
                        <div className="text-center text-muted-foreground py-20 italic">
                            Waiting for logs...
                        </div>
                    ) : (
                        logs.map((log, i) => (
                            <LogEntryRow key={`${log.timestamp}-${i}`} entry={log} index={i} />
                        ))
                    )}

                    {/* Anchor for scrolling */}
                    <div id="log-end" />
                </div>
            </ScrollArea>

            {/* Auto-scroll indicator/toggle */}
            {!autoScroll && (
                <Button
                    size="sm"
                    variant="secondary"
                    className="absolute bottom-4 right-4 shadow-lg bg-primary text-primary-foreground hover:bg-primary/90 rounded-full h-8 px-3 text-xs"
                    onClick={() => setAutoScroll(true)}
                >
                    <ArrowDown className="mr-1 h-3 w-3" />
                    Resume Scroll
                </Button>
            )}
        </div>
    )
}
