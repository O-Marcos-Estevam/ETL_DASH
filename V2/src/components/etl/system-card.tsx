import { Switch } from "@/components/ui/switch"
import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { Sistema } from "@/types/etl"
import { OPTION_ICONS, OPTION_LABELS } from "@/types/etl"
import { SystemIcon } from "./system-icon"

interface SystemCardProps {
    sistema: Sistema
    onToggle: (id: string, ativo: boolean) => void
    onOptionToggle: (id: string, opcao: string, valor: boolean) => void
}

export function SystemCard({ sistema, onToggle, onOptionToggle }: SystemCardProps) {
    const statusClass = sistema.status === 'RUNNING'
        ? 'border-blue-500/50 bg-blue-500/5'
        : sistema.ativo
            ? 'border-green-500/30 bg-green-500/5'
            : 'border-muted opacity-60';

    return (
        <Card className={cn("transition-all duration-300", statusClass)}>
            <CardContent className="p-4">
                {/* Header */}
                <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                        <div className="text-2xl">
                            <SystemIcon name={sistema.icone} className="h-8 w-8 text-primary/80" />
                        </div>
                        <div className="min-w-0">
                            <h3 className="font-semibold truncate">{sistema.nome}</h3>
                            <p className="text-xs text-muted-foreground truncate">
                                {sistema.descricao}
                            </p>
                        </div>
                    </div>
                    <Switch
                        checked={sistema.ativo}
                        onCheckedChange={(checked) => onToggle(sistema.id, checked)}
                    />
                </div>

                {/* Options */}
                {sistema.opcoes && Object.keys(sistema.opcoes).length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                        {Object.entries(sistema.opcoes).map(([key, value]) => (
                            <button
                                key={key}
                                onClick={() => onOptionToggle(sistema.id, key, !value)}
                                className={cn(
                                    "inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs transition-colors",
                                    value
                                        ? "bg-primary/20 text-primary border border-primary/30"
                                        : "bg-muted/50 text-muted-foreground border border-transparent hover:bg-muted"
                                )}
                            >
                                <span>{OPTION_ICONS[key] || '⚙️'}</span>
                                <span>{OPTION_LABELS[key] || key}</span>
                            </button>
                        ))}
                    </div>
                )}

                {/* Progress Bar */}
                <div className="mt-3 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                        className={cn(
                            "h-full transition-all duration-500 rounded-full",
                            sistema.status === 'RUNNING' ? "bg-blue-500 animate-pulse" :
                                sistema.status === 'SUCCESS' ? "bg-green-500" :
                                    sistema.status === 'ERROR' ? "bg-red-500" : "bg-primary/30"
                        )}
                        style={{ width: `${sistema.progresso || 0}%` }}
                    />
                </div>

                {/* Status Message */}
                <p className="mt-2 text-xs text-muted-foreground truncate">
                    {sistema.mensagem || (sistema.ativo ? 'Pronto para executar' : 'Desativado')}
                </p>
            </CardContent>
        </Card>
    )
}
