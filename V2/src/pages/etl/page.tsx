import { useState, useEffect, useCallback, useRef } from "react"
import { Activity, CheckCircle2, XCircle, Wifi, WifiOff, Save } from "lucide-react"
import { Button } from "@/components/ui/button"
import { KpiCard } from "@/components/dashboard/kpi-card"
import {
    PeriodSelector,
    SystemsGrid,
    ExecutionControls,
    CredentialsModal
} from "@/components/etl"
import { api } from "@/services/api"
import { ws, type JobCompletePayload } from "@/services/websocket"
import type { ConfiguracaoETL, Periodo, StatusUpdate } from "@/types/etl"

export function EtlPage() {
    // State
    const [config, setConfig] = useState<ConfiguracaoETL | null>(null)
    const [loading, setLoading] = useState(true)
    const [isExecuting, setIsExecuting] = useState(false)
    const [isConnected, setIsConnected] = useState(false)
    const [credentialsOpen, setCredentialsOpen] = useState(false)
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)

    // Ref para evitar closures stale em callbacks
    const toastTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

    // showToast estável com useCallback
    const showToast = useCallback((message: string, type: 'success' | 'error') => {
        if (toastTimeoutRef.current) {
            clearTimeout(toastTimeoutRef.current)
        }
        setToast({ message, type })
        toastTimeoutRef.current = setTimeout(() => setToast(null), 5000)
    }, [])

    // Handler para status updates via WebSocket
    const handleStatusUpdate = useCallback((sistemaId: string, status: StatusUpdate) => {
        setConfig(prev => {
            if (!prev?.sistemas[sistemaId]) return prev
            return {
                ...prev,
                sistemas: {
                    ...prev.sistemas,
                    [sistemaId]: {
                        ...prev.sistemas[sistemaId],
                        status: status.status,
                        progresso: status.progresso,
                        mensagem: status.mensagem
                    }
                }
            }
        })
    }, [])

    // Handler para job complete via WebSocket
    const handleJobComplete = useCallback((payload: JobCompletePayload) => {
        const currentJobId = localStorage.getItem('current_etl_job_id')
        if (currentJobId && payload.job_id === Number(currentJobId)) {
            setIsExecuting(false)
            const isSuccess = payload.status === 'completed'
            showToast(
                isSuccess
                    ? `Pipeline concluído com sucesso! (${payload.duracao_segundos}s)`
                    : `Pipeline finalizado com erro (${payload.duracao_segundos}s)`,
                isSuccess ? 'success' : 'error'
            )
        }
    }, [showToast])

    // Load config on mount
    useEffect(() => {
        const loadConfig = async () => {
            try {
                setLoading(true)
                const data = await api.getConfig()
                setConfig(data)
            } catch (error) {
                console.error("Erro ao carregar configuração:", error)
                setConfig({
                    versao: '2.0',
                    ultimaModificacao: new Date().toISOString(),
                    periodo: { dataInicial: null, dataFinal: null, usarD1Anbima: true },
                    sistemas: {}
                })
                showToast("Erro ao conectar com o servidor", "error")
            } finally {
                setLoading(false)
            }
        }

        loadConfig()
    }, [showToast])

    // Setup WebSocket connection and subscriptions
    useEffect(() => {
        const connectWebSocket = async () => {
            try {
                ws.resetReconnect()
                await ws.connect()
            } catch (error) {
                console.warn("WebSocket não conectado:", error)
            }
        }

        connectWebSocket()

        // Subscribe to WebSocket events
        const unsubConnection = ws.onConnectionChange(setIsConnected)
        const unsubStatus = ws.onStatusUpdate(handleStatusUpdate)
        const unsubJobComplete = ws.onJobComplete(handleJobComplete)

        return () => {
            unsubConnection()
            unsubStatus()
            unsubJobComplete()
            ws.disconnect()
        }
    }, [handleStatusUpdate, handleJobComplete])

    // Cleanup toast timeout on unmount
    useEffect(() => {
        return () => {
            if (toastTimeoutRef.current) {
                clearTimeout(toastTimeoutRef.current)
            }
        }
    }, [])

    // Handlers
    const handlePeriodChange = (periodo: Periodo) => {
        setConfig(prev => prev ? { ...prev, periodo } : null)
    }

    const handleToggleSistema = async (id: string, ativo: boolean) => {
        if (!config) return

        setConfig(prev => prev ? {
            ...prev,
            sistemas: { ...prev.sistemas, [id]: { ...prev.sistemas[id], ativo } }
        } : null)

        try {
            await api.toggleSistema(id, ativo)
        } catch (error) {
            console.error("Erro ao atualizar sistema:", error)
        }
    }

    const handleOptionToggle = async (id: string, opcao: string, valor: boolean) => {
        if (!config?.sistemas[id]?.opcoes) return

        setConfig(prev => prev ? {
            ...prev,
            sistemas: {
                ...prev.sistemas,
                [id]: {
                    ...prev.sistemas[id],
                    opcoes: { ...prev.sistemas[id].opcoes, [opcao]: valor }
                }
            }
        } : null)

        try {
            await api.updateOpcao(id, opcao, valor)
        } catch (error) {
            console.error("Erro ao atualizar opção:", error)
        }
    }

    const handleActivateAll = async () => {
        if (!config) return
        Object.keys(config.sistemas).forEach(id => {
            handleToggleSistema(id, true)
        })
        showToast("Todos os sistemas ativados", "success")
    }

    const handleDeactivateAll = async () => {
        if (!config) return
        Object.keys(config.sistemas).forEach(id => {
            handleToggleSistema(id, false)
        })
        showToast("Todos os sistemas desativados", "success")
    }

    const handleSaveConfig = async () => {
        if (!config) return
        try {
            await api.saveConfig(config)
            showToast("Configuração salva!", "success")
        } catch (error) {
            showToast("Erro ao salvar", "error")
        }
    }

    const handleExecute = async (limparPastas: boolean) => {
        if (isExecuting) return

        const ativos = config?.sistemas
            ? Object.values(config.sistemas).filter(s => s.ativo)
            : []

        if (ativos.length === 0) {
            showToast("Nenhum sistema ativo", "error")
            return
        }

        setIsExecuting(true)
        try {
            // Collect active systems
            const sistemasAtivos = Object.entries(config?.sistemas || {})
                .filter(([, s]) => s.ativo)
                .map(([id]) => id)

            // Collect options
            const opcoes: Record<string, Record<string, boolean>> = {}
            Object.entries(config?.sistemas || {}).forEach(([id, s]) => {
                if (s.opcoes) {
                    opcoes[id] = s.opcoes
                }
            })

            const result = await api.executePipeline({
                sistemas: sistemasAtivos,
                limpar: limparPastas,
                opcoes,
                data_inicial: config?.periodo.dataInicial,
                data_final: config?.periodo.dataFinal
            })

            console.log("Execute result:", result)

            if (result.status === "started") {
                showToast(limparPastas ? "Pipeline iniciado (com limpeza)!" : "Pipeline iniciado!", "success")
                if (result.job_id) {
                    localStorage.setItem('current_etl_job_id', String(result.job_id))
                }
                // Manter isExecuting=true - será setado false pelo handleJobComplete via WebSocket
            } else {
                // API retornou erro - parar execução
                setIsExecuting(false)
                showToast("Erro: " + (result.message || result.error || "Falha desconhecida"), "error")
            }
        } catch (error) {
            // Exceção na chamada API - parar execução
            setIsExecuting(false)
            console.error("Execute error:", error)
            showToast("Erro ao executar: " + (error instanceof Error ? error.message : String(error)), "error")
        }
        // Não usar finally - isExecuting deve permanecer true enquanto job roda
    }

    // Computed values
    const sistemas = config?.sistemas || {}
    const total = Object.keys(sistemas).length
    const ativos = Object.values(sistemas).filter(s => s.ativo).length
    const hasActiveSystems = ativos > 0

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
        )
    }

    return (
        <div className="flex flex-col gap-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                        ETL Dashboard
                        <span className="text-sm font-normal px-2 py-0.5 rounded-full bg-primary/20 text-primary">
                            V2
                        </span>
                    </h2>
                    <p className="text-muted-foreground">
                        Gerenciamento e execução do pipeline ETL
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 text-sm">
                        {isConnected ? (
                            <><Wifi className="h-4 w-4 text-green-500" /> <span>Conectado</span></>
                        ) : (
                            <><WifiOff className="h-4 w-4 text-muted-foreground" /> <span>Desconectado</span></>
                        )}
                    </div>
                    <Button variant="outline" onClick={handleSaveConfig}>
                        <Save className="mr-2 h-4 w-4" />
                        Salvar
                    </Button>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid gap-4 md:grid-cols-3">
                <KpiCard
                    title="Total de Sistemas"
                    value={total.toString()}
                    icon={Activity}
                    description="Sistemas configurados"
                    trend="neutral"
                />
                <KpiCard
                    title="Ativos"
                    value={ativos.toString()}
                    icon={CheckCircle2}
                    description="Prontos para execução"
                    trend="up"
                />
                <KpiCard
                    title="Inativos"
                    value={(total - ativos).toString()}
                    icon={XCircle}
                    description="Desabilitados"
                    trend="neutral"
                />
            </div>

            {/* Period Selector */}
            <PeriodSelector
                periodo={config?.periodo || { dataInicial: null, dataFinal: null, usarD1Anbima: true }}
                onChange={handlePeriodChange}
            />

            {/* Systems Grid */}
            <SystemsGrid
                sistemas={sistemas}
                onToggle={handleToggleSistema}
                onOptionToggle={handleOptionToggle}
                onActivateAll={handleActivateAll}
                onDeactivateAll={handleDeactivateAll}
            />

            {/* Execution Controls */}
            <ExecutionControls
                isExecuting={isExecuting}
                hasActiveSystems={hasActiveSystems}
                onExecute={handleExecute}
                onOpenCredentials={() => setCredentialsOpen(true)}
            />

            {/* Credentials Modal */}
            <CredentialsModal
                open={credentialsOpen}
                onClose={() => setCredentialsOpen(false)}
                onSave={() => showToast("Credenciais salvas!", "success")}
            />

            {/* Toast */}
            {toast && (
                <div className={`fixed bottom-4 right-4 z-[9999] px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 animate-in slide-in-from-bottom-5 ${toast.type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
                    }`}>
                    {toast.type === 'success' ? '✅' : '❌'}
                    {toast.message}
                </div>
            )}
        </div>
    )
}
