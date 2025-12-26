import { Settings2, ToggleLeft, ToggleRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { SystemCard } from "./system-card"
import type { Sistema } from "@/types/etl"

interface SystemsGridProps {
    sistemas: Record<string, Sistema>
    onToggle: (id: string, ativo: boolean) => void
    onOptionToggle: (id: string, opcao: string, valor: boolean) => void
    onActivateAll: () => void
    onDeactivateAll: () => void
}

export function SystemsGrid({
    sistemas,
    onToggle,
    onOptionToggle,
    onActivateAll,
    onDeactivateAll
}: SystemsGridProps) {
    // Sort systems by order
    const sortedSistemas = Object.entries(sistemas)
        .sort(([, a], [, b]) => (a.ordem || 99) - (b.ordem || 99));

    return (
        <Card>
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2 text-lg">
                        <Settings2 className="h-5 w-5 text-primary" />
                        Sistemas
                    </CardTitle>
                    <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={onActivateAll}>
                            <ToggleRight className="mr-1.5 h-4 w-4" />
                            Ativar Todos
                        </Button>
                        <Button variant="outline" size="sm" onClick={onDeactivateAll}>
                            <ToggleLeft className="mr-1.5 h-4 w-4" />
                            Desativar Todos
                        </Button>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                    {sortedSistemas.map(([id, sistema]) => (
                        <SystemCard
                            key={id}
                            sistema={{ ...sistema, id }}
                            onToggle={onToggle}
                            onOptionToggle={onOptionToggle}
                        />
                    ))}
                </div>
                {sortedSistemas.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                        Nenhum sistema configurado
                    </div>
                )}
            </CardContent>
        </Card>
    )
}
