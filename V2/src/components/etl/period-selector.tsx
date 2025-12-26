import { Calendar } from "lucide-react"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { Periodo } from "@/types/etl"

interface PeriodSelectorProps {
    periodo: Periodo
    onChange: (periodo: Periodo) => void
}

export function PeriodSelector({ periodo, onChange }: PeriodSelectorProps) {
    return (
        <Card>
            <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-lg">
                    <Calendar className="h-5 w-5 text-primary" />
                    Período
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    <div className="space-y-2">
                        <Label htmlFor="data-inicial" className="text-muted-foreground">
                            Data Inicial
                        </Label>
                        <Input
                            id="data-inicial"
                            type="date"
                            value={periodo.dataInicial || ''}
                            onChange={(e) => onChange({ ...periodo, dataInicial: e.target.value || null })}
                            className="bg-muted/50"
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="data-final" className="text-muted-foreground">
                            Data Final
                        </Label>
                        <Input
                            id="data-final"
                            type="date"
                            value={periodo.dataFinal || ''}
                            onChange={(e) => onChange({ ...periodo, dataFinal: e.target.value || null })}
                            className="bg-muted/50"
                        />
                    </div>
                    <div className="flex items-center gap-3 pt-6">
                        <Switch
                            id="usar-d1"
                            checked={periodo.usarD1Anbima}
                            onCheckedChange={(checked) => onChange({ ...periodo, usarD1Anbima: checked })}
                        />
                        <Label htmlFor="usar-d1" className="cursor-pointer">
                            Usar D-1 ANBIMA
                        </Label>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
