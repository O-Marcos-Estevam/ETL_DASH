import { useEffect, useState } from "react"
import { Activity, CheckCircle2, TrendingUp, XCircle, Play, MoreHorizontal } from "lucide-react"

import { ExecutionChart } from "@/components/dashboard/execution-chart"
import { KpiCard } from "@/components/dashboard/kpi-card"
import { RecentActivity } from "@/components/dashboard/recent-activity"
import { CardSkeleton } from "@/components/ui/loading-skeleton"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ExecutionService } from "@/services/execution"
import { useToast } from "@/components/ui/use-toast"
import { useNavigate } from "react-router-dom"

export function DashboardPage() {
    const [isLoading, setIsLoading] = useState(true)
    const { toast } = useToast()
    const navigate = useNavigate()

    // Simulate initial data loading
    useEffect(() => {
        const timer = setTimeout(() => setIsLoading(false), 1500)
        return () => clearTimeout(timer)
    }, [])

    const handleRun = async (sistema?: string) => {
        try {
            const sistemas = sistema ? [sistema] : ["amplis_reag", "maps", "fidc", "jcot", "britech", "qore"]

            toast({
                title: "Iniciando Execução",
                description: `Disparando ${sistema ? sistema.toUpperCase() : "TODOS"}...`,
            })

            const res = await ExecutionService.runJob({
                sistemas,
                dry_run: false
            })

            if (res.status === "started") {
                toast({
                    title: "Execução Iniciada",
                    description: "Monitorando logs em tempo real.",
                })
                // Redirect user to Logs page to watch progress
                navigate("/logs")
            } else {
                throw new Error(res.message || "Erro desconhecido")
            }

        } catch (error) {
            toast({
                variant: "destructive",
                title: "Erro ao Executar",
                description: String(error),
            })
        }
    }

    return (
        <div className="flex flex-col gap-6 animate-in fade-in duration-500">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
                    <p className="text-muted-foreground">
                        Overview of system performance and recent activities.
                    </p>
                </div>
                <div className="flex gap-2">
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="outline">
                                Executar Individual <MoreHorizontal className="ml-2 h-4 w-4" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleRun('maps')}>Rodar MAPS</DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleRun('fidc')}>Rodar FIDC</DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleRun('amplis_reag')}>Rodar AMPLIS</DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleRun('jcot')}>Rodar JCOT</DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleRun('britech')}>Rodar BRITECH</DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleRun('qore')}>Rodar QORE</DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                    <Button onClick={() => handleRun()}>
                        <Play className="mr-2 h-4 w-4" /> Iniciar Rotina Completa
                    </Button>
                </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {isLoading ? (
                    <>
                        <CardSkeleton />
                        <CardSkeleton />
                        <CardSkeleton />
                        <CardSkeleton />
                    </>
                ) : (
                    <>
                        <KpiCard
                            title="Total Jobs"
                            value="1,284"
                            icon={Activity}
                            description="Total executions (24h)"
                            trend="up"
                        />
                        <KpiCard
                            title="Success Rate"
                            value="98.5%"
                            icon={CheckCircle2}
                            description="Avg. success rate"
                            trend="neutral"
                        />
                        <KpiCard
                            title="Failed Jobs"
                            value="12"
                            icon={XCircle}
                            description="Required attention"
                            trend="down"
                        />
                        <KpiCard
                            title="Active Workers"
                            value="4"
                            icon={TrendingUp}
                            description="Currently processing"
                            trend="neutral"
                        />
                    </>
                )}
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {isLoading ? (
                    <>
                        <div className="col-span-1 lg:col-span-3 rounded-xl border bg-card text-card-foreground shadow">
                            <div className="p-6">
                                <Skeleton className="h-[300px] w-full" />
                            </div>
                        </div>
                        <div className="col-span-1 lg:col-span-1 rounded-xl border bg-card text-card-foreground shadow">
                            <div className="p-6">
                                <Skeleton className="h-[300px] w-full" />
                            </div>
                        </div>
                    </>
                ) : (
                    <>
                        <ExecutionChart />
                        <RecentActivity />
                    </>
                )}
            </div>
        </div>
    )
}
