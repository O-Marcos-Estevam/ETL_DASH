import { Rocket, Key, Trash2 } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"

interface ExecutionControlsProps {
    isExecuting: boolean
    hasActiveSystems: boolean
    onExecute: (limparPastas: boolean) => void
    onOpenCredentials: () => void
}

export function ExecutionControls({
    isExecuting,
    hasActiveSystems,
    onExecute,
    onOpenCredentials
}: ExecutionControlsProps) {
    const [limparPastas, setLimparPastas] = useState(false)

    return (
        <Card>
            <CardContent className="flex flex-wrap items-center justify-between gap-4 p-4">
                <div className="flex items-center gap-3">
                    <Switch
                        id="limpar-pastas"
                        checked={limparPastas}
                        onCheckedChange={setLimparPastas}
                    />
                    <Label
                        htmlFor="limpar-pastas"
                        className="flex items-center gap-2 cursor-pointer"
                    >
                        <Trash2 className="h-4 w-4" />
                        Limpar Pastas Antes
                    </Label>
                </div>

                <div className="flex gap-3">
                    <Button
                        variant="outline"
                        onClick={onOpenCredentials}
                    >
                        <Key className="mr-2 h-4 w-4" />
                        Credenciais
                    </Button>

                    <Button
                        size="lg"
                        disabled={isExecuting || !hasActiveSystems}
                        onClick={() => onExecute(limparPastas)}
                        className={cn(
                            "min-w-[200px] font-semibold transition-all",
                            isExecuting && "animate-pulse"
                        )}
                    >
                        <Rocket className="mr-2 h-5 w-5" />
                        {isExecuting ? 'Executando...' : 'EXECUTAR PIPELINE'}
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}
