"use client"

import { useState, useEffect } from "react"
import { Check, Search, Save, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/components/ui/use-toast"
import { api } from "@/services/api"

// Sistemas que suportam seleção de fundos
const sistemasComFundos = ["maps", "fidc", "qore"] as const
type SistemaComFundos = typeof sistemasComFundos[number]

const sistemasLabels: Record<SistemaComFundos, string> = {
    maps: "MAPS",
    fidc: "FIDC",
    qore: "QORE"
}

export function FundsForm() {
    const [credentials, setCredentials] = useState<any>({})
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [search, setSearch] = useState("")
    const [activeTab, setActiveTab] = useState<SistemaComFundos>("maps")
    const { toast } = useToast()

    useEffect(() => {
        loadCredentials()
    }, [])

    const loadCredentials = async () => {
        setLoading(true)
        try {
            const data = await api.getCredentials()
            setCredentials(data)
        } catch (error) {
            toast({
                title: "Erro",
                description: "Não foi possível carregar as configurações",
                variant: "destructive"
            })
        } finally {
            setLoading(false)
        }
    }

    const handleSave = async () => {
        setSaving(true)
        try {
            await api.saveCredentials(credentials)
            toast({
                title: "Sucesso",
                description: "Configurações de fundos salvas com sucesso"
            })
        } catch (error) {
            toast({
                title: "Erro",
                description: "Não foi possível salvar as configurações",
                variant: "destructive"
            })
        } finally {
            setSaving(false)
        }
    }

    // Obtém fundos disponíveis de um sistema
    const getFundosDisponiveis = (sistema: SistemaComFundos): string[] => {
        return credentials[sistema]?.fundos || []
    }

    // Obtém fundos selecionados de um sistema
    const getFundosSelecionados = (sistema: SistemaComFundos): string[] => {
        return credentials[sistema]?.fundos_selecionados || []
    }

    // Verifica se "usar todos" está ativo
    const getUsarTodos = (sistema: SistemaComFundos): boolean => {
        return credentials[sistema]?.usar_todos !== false
    }

    // Atualiza "usar_todos"
    const setUsarTodos = (sistema: SistemaComFundos, value: boolean) => {
        setCredentials((prev: any) => ({
            ...prev,
            [sistema]: {
                ...prev[sistema],
                usar_todos: value
            }
        }))
    }

    // Toggle fundo selecionado
    const toggleFundo = (sistema: SistemaComFundos, fundo: string) => {
        const current = getFundosSelecionados(sistema)
        const updated = current.includes(fundo)
            ? current.filter(f => f !== fundo)
            : [...current, fundo]

        setCredentials((prev: any) => ({
            ...prev,
            [sistema]: {
                ...prev[sistema],
                fundos_selecionados: updated
            }
        }))
    }

    // Selecionar todos
    const selectAll = (sistema: SistemaComFundos) => {
        setCredentials((prev: any) => ({
            ...prev,
            [sistema]: {
                ...prev[sistema],
                fundos_selecionados: [...getFundosDisponiveis(sistema)]
            }
        }))
    }

    // Limpar seleção
    const clearSelection = (sistema: SistemaComFundos) => {
        setCredentials((prev: any) => ({
            ...prev,
            [sistema]: {
                ...prev[sistema],
                fundos_selecionados: []
            }
        }))
    }

    if (loading) {
        return (
            <div className="flex justify-center p-8">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        )
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>Seleção de Fundos por Sistema</CardTitle>
                <CardDescription>
                    Configure quais fundos serão processados em cada sistema.
                    Se "Usar Todos" estiver ativo, todos os fundos disponíveis serão processados.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as SistemaComFundos)}>
                    <TabsList className="grid w-full grid-cols-3">
                        {sistemasComFundos.map(sistema => (
                            <TabsTrigger key={sistema} value={sistema}>
                                {sistemasLabels[sistema]}
                                <Badge variant="outline" className="ml-2 text-xs">
                                    {getFundosDisponiveis(sistema).length}
                                </Badge>
                            </TabsTrigger>
                        ))}
                    </TabsList>

                    {sistemasComFundos.map(sistema => {
                        const fundosDisponiveis = getFundosDisponiveis(sistema)
                        const fundosSelecionados = getFundosSelecionados(sistema)
                        const usarTodos = getUsarTodos(sistema)

                        const filtered = fundosDisponiveis.filter(f =>
                            f.toLowerCase().includes(search.toLowerCase())
                        )

                        return (
                            <TabsContent key={sistema} value={sistema} className="space-y-4 mt-4">
                                {/* Toggle Usar Todos */}
                                <div className="flex items-center justify-between p-4 border rounded-lg bg-muted/50">
                                    <Label htmlFor={`${sistema}-usar-todos`} className="flex flex-col space-y-1">
                                        <span className="font-medium">Usar Todos os Fundos</span>
                                        <span className="font-normal text-sm text-muted-foreground">
                                            Quando ativo, processa todos os {fundosDisponiveis.length} fundos disponíveis
                                        </span>
                                    </Label>
                                    <Switch
                                        id={`${sistema}-usar-todos`}
                                        checked={usarTodos}
                                        onCheckedChange={(checked) => setUsarTodos(sistema, checked)}
                                    />
                                </div>

                                {/* Seleção Manual (só aparece se usar_todos = false) */}
                                {!usarTodos && (
                                    <>
                                        <div className="flex items-center gap-2">
                                            <div className="relative flex-1">
                                                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                                                <Input
                                                    placeholder="Buscar fundo..."
                                                    className="pl-8"
                                                    value={search}
                                                    onChange={(e) => setSearch(e.target.value)}
                                                />
                                            </div>
                                            <Badge variant="secondary">
                                                {fundosSelecionados.length} de {fundosDisponiveis.length}
                                            </Badge>
                                        </div>

                                        {fundosDisponiveis.length === 0 ? (
                                            <div className="text-center py-8 text-muted-foreground border rounded-md">
                                                Nenhum fundo configurado para {sistemasLabels[sistema]}.
                                                <br />
                                                <span className="text-xs">
                                                    Configure no arquivo credentials.json
                                                </span>
                                            </div>
                                        ) : (
                                            <>
                                                <ScrollArea className="h-[250px] border rounded-md p-4">
                                                    <div className="space-y-2">
                                                        {filtered.map(fundo => {
                                                            const isSelected = fundosSelecionados.includes(fundo)
                                                            return (
                                                                <div
                                                                    key={fundo}
                                                                    className={`flex items-center space-x-3 p-2 rounded-lg border transition-colors cursor-pointer hover:bg-accent ${isSelected ? 'bg-accent/50 border-primary' : 'border-transparent'}`}
                                                                    onClick={() => toggleFundo(sistema, fundo)}
                                                                >
                                                                    <div className={`flex h-5 w-5 items-center justify-center rounded-sm border ${isSelected ? 'bg-primary border-primary text-primary-foreground' : 'border-primary'}`}>
                                                                        {isSelected && <Check className="h-3.5 w-3.5" />}
                                                                    </div>
                                                                    <span className="text-sm">{fundo}</span>
                                                                </div>
                                                            )
                                                        })}
                                                        {filtered.length === 0 && search && (
                                                            <div className="text-center py-4 text-muted-foreground">
                                                                Nenhum fundo encontrado para "{search}"
                                                            </div>
                                                        )}
                                                    </div>
                                                </ScrollArea>

                                                <div className="flex gap-2">
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => selectAll(sistema)}
                                                        disabled={fundosSelecionados.length === fundosDisponiveis.length}
                                                    >
                                                        Selecionar Todos
                                                    </Button>
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => clearSelection(sistema)}
                                                        disabled={fundosSelecionados.length === 0}
                                                    >
                                                        Limpar Seleção
                                                    </Button>
                                                </div>
                                            </>
                                        )}
                                    </>
                                )}
                            </TabsContent>
                        )
                    })}
                </Tabs>

                <div className="flex justify-end pt-4 border-t mt-4">
                    <Button onClick={handleSave} disabled={saving}>
                        {saving ? (
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                            <Save className="mr-2 h-4 w-4" />
                        )}
                        Salvar Configurações de Fundos
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}
