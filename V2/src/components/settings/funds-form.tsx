"use client"

import { useState } from "react"
import { Check, Search } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"

const mockFundos = [
    { id: "1", name: "FUNDO ALPHA FI MULTIMERCADO", cnpj: "12.345.678/0001-90" },
    { id: "2", name: "FUNDO BETA AÇÕES", cnpj: "98.765.432/0001-10" },
    { id: "3", name: "FUNDO GAMA CRÉDITO PRIVADO", cnpj: "11.222.333/0001-44" },
    { id: "4", name: "FUNDO DELTA PREVIDÊNCIA", cnpj: "55.666.777/0001-88" },
    { id: "5", name: "FUNDO EPSILON CAMBIAL", cnpj: "99.888.777/0001-22" },
]

export function FundsForm() {
    const [selected, setSelected] = useState<string[]>(["1", "2"])
    const [search, setSearch] = useState("")

    const toggleFundo = (id: string) => {
        setSelected(prev =>
            prev.includes(id)
                ? prev.filter(item => item !== id)
                : [...prev, id]
        )
    }

    const filtered = mockFundos.filter(f =>
        f.name.toLowerCase().includes(search.toLowerCase()) ||
        f.cnpj.includes(search)
    )

    return (
        <Card>
            <CardHeader>
                <CardTitle>Seleção de Fundos</CardTitle>
                <CardDescription>
                    Selecione os fundos que serão processados pelo ETL.
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="flex items-center gap-2">
                    <div className="relative flex-1">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Buscar por nome ou CNPJ..."
                            className="pl-8"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                    <Badge variant="secondary">
                        {selected.length} selecionados
                    </Badge>
                </div>

                <ScrollArea className="h-[300px] border rounded-md p-4">
                    <div className="space-y-2">
                        {filtered.map(fundo => (
                            <div
                                key={fundo.id}
                                className={`flex items-start space-x-3 p-2 rounded-lg border transition-colors cursor-pointer hover:bg-accent ${selected.includes(fundo.id) ? 'bg-accent/50 border-primary' : 'border-transparent'}`}
                                onClick={() => toggleFundo(fundo.id)}
                            >
                                <div className={`flex h-5 w-5 items-center justify-center rounded-sm border ${selected.includes(fundo.id) ? 'bg-primary border-primary text-primary-foreground' : 'border-primary'}`}>
                                    {selected.includes(fundo.id) && <Check className="h-3.5 w-3.5" />}
                                </div>
                                <div className="space-y-1">
                                    <p className="text-sm font-medium leading-none">{fundo.name}</p>
                                    <p className="text-xs text-muted-foreground">CNPJ: {fundo.cnpj}</p>
                                </div>
                            </div>
                        ))}
                        {filtered.length === 0 && (
                            <div className="text-center py-8 text-muted-foreground">
                                Nenhum fundo encontrado.
                            </div>
                        )}
                    </div>
                </ScrollArea>

                <div className="flex justify-end gap-2 pt-2">
                    <Button variant="outline" onClick={() => setSelected([])} disabled={selected.length === 0}>
                        Limpar Seleção
                    </Button>
                    <Button>
                        Salvar Seleção
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}
