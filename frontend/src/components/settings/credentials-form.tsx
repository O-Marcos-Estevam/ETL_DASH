"use client"

import { useState, useEffect } from "react"
import { Eye, EyeOff, Save, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useToast } from "@/components/ui/use-toast"
import { api } from "@/services/api"

// Definição dos sistemas e seus campos específicos
const sistemasConfig = {
    maps: {
        name: "MAPS",
        fields: [
            { key: "url", label: "URL", type: "text", placeholder: "https://api.maps.com.br" },
            { key: "username", label: "Usuário", type: "text", placeholder: "username" },
            { key: "password", label: "Senha", type: "password", placeholder: "••••••••" }
        ]
    },
    fidc: {
        name: "FIDC",
        fields: [
            { key: "url", label: "URL", type: "text", placeholder: "https://api.fidc.com.br" },
            { key: "username", label: "Usuário", type: "text", placeholder: "username" },
            { key: "password", label: "Senha", type: "password", placeholder: "••••••••" }
        ]
    },
    jcot: {
        name: "JCOT",
        fields: [
            { key: "url", label: "URL", type: "text", placeholder: "https://api.jcot.com.br" },
            { key: "username", label: "Usuário", type: "text", placeholder: "username" },
            { key: "password", label: "Senha", type: "password", placeholder: "••••••••" }
        ]
    },
    britech: {
        name: "BRITECH",
        fields: [
            { key: "url", label: "URL", type: "text", placeholder: "https://domogestora.britech.com.br/" },
            { key: "username", label: "Usuário", type: "text", placeholder: "username" },
            { key: "password", label: "Senha", type: "password", placeholder: "••••••••" }
        ]
    },
    qore: {
        name: "QORE",
        fields: [
            { key: "url", label: "URL", type: "text", placeholder: "https://api.qore.com.br" },
            { key: "username", label: "Usuário", type: "text", placeholder: "username" },
            { key: "password", label: "Senha", type: "password", placeholder: "••••••••" }
        ]
    },
    amplis_reag: {
        name: "AMPLIS REAG",
        path: ["amplis", "reag"],
        fields: [
            { key: "url", label: "URL", type: "text", placeholder: "https://api.amplis.com.br/reag" },
            { key: "username", label: "Usuário", type: "text", placeholder: "username" },
            { key: "password", label: "Senha", type: "password", placeholder: "••••••••" }
        ]
    },
    amplis_master: {
        name: "AMPLIS MASTER",
        path: ["amplis", "master"],
        fields: [
            { key: "url", label: "URL", type: "text", placeholder: "https://api.amplis.com.br/master" },
            { key: "username", label: "Usuário", type: "text", placeholder: "username" },
            { key: "password", label: "Senha", type: "password", placeholder: "••••••••" }
        ]
    }
}

type SistemaId = keyof typeof sistemasConfig

export function CredentialsForm() {
    const [credentials, setCredentials] = useState<any>({})
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [showPassword, setShowPassword] = useState<Record<string, boolean>>({})
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
                description: "Não foi possível carregar as credenciais",
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
                description: "Credenciais salvas com sucesso"
            })
        } catch (error) {
            toast({
                title: "Erro",
                description: "Não foi possível salvar as credenciais",
                variant: "destructive"
            })
        } finally {
            setSaving(false)
        }
    }

    // Obtém valor do config considerando path aninhado (ex: amplis.reag)
    const getValue = (sistemaId: SistemaId, fieldKey: string): string => {
        const config = sistemasConfig[sistemaId]
        if ('path' in config && config.path) {
            const [parent, child] = config.path
            return credentials[parent]?.[child]?.[fieldKey] || ""
        }
        return credentials[sistemaId]?.[fieldKey] || ""
    }

    // Atualiza valor no config considerando path aninhado
    const handleChange = (sistemaId: SistemaId, fieldKey: string, value: string) => {
        const config = sistemasConfig[sistemaId]

        setCredentials((prev: any) => {
            if ('path' in config && config.path) {
                const [parent, child] = config.path
                return {
                    ...prev,
                    [parent]: {
                        ...prev[parent],
                        [child]: {
                            ...prev[parent]?.[child],
                            [fieldKey]: value
                        }
                    }
                }
            }
            return {
                ...prev,
                [sistemaId]: {
                    ...prev[sistemaId],
                    [fieldKey]: value
                }
            }
        })
    }

    const togglePassword = (id: string) => {
        setShowPassword(prev => ({ ...prev, [id]: !prev[id] }))
    }

    if (loading) {
        return (
            <div className="flex justify-center p-8">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        )
    }

    const sistemaIds = Object.keys(sistemasConfig) as SistemaId[]

    return (
        <div className="grid gap-6">
            <Card>
                <CardHeader>
                    <CardTitle>Credenciais dos Sistemas</CardTitle>
                    <CardDescription>
                        Gerencie o acesso aos sistemas externos. Senhas são mascaradas por segurança.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Tabs defaultValue="maps" className="w-full">
                        <TabsList className="grid w-full grid-cols-4 lg:grid-cols-7 h-auto gap-1">
                            {sistemaIds.map(id => (
                                <TabsTrigger
                                    key={id}
                                    value={id}
                                    className="text-xs sm:text-sm px-2"
                                >
                                    {sistemasConfig[id].name.split(" ")[0]}
                                </TabsTrigger>
                            ))}
                        </TabsList>

                        {sistemaIds.map(sistemaId => {
                            const config = sistemasConfig[sistemaId]

                            return (
                                <TabsContent
                                    key={sistemaId}
                                    value={sistemaId}
                                    className="space-y-4 mt-4 border p-4 rounded-md"
                                >
                                    <h3 className="font-medium text-lg">{config.name}</h3>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {config.fields.map(field => (
                                            <div key={field.key} className="grid gap-2">
                                                <Label htmlFor={`${sistemaId}-${field.key}`}>
                                                    {field.label}
                                                </Label>
                                                <div className="relative">
                                                    <Input
                                                        id={`${sistemaId}-${field.key}`}
                                                        type={
                                                            field.type === "password" && !showPassword[`${sistemaId}-${field.key}`]
                                                                ? "password"
                                                                : "text"
                                                        }
                                                        value={getValue(sistemaId, field.key)}
                                                        onChange={(e) => handleChange(sistemaId, field.key, e.target.value)}
                                                        placeholder={field.placeholder}
                                                    />
                                                    {field.type === "password" && (
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            type="button"
                                                            className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                                                            onClick={() => togglePassword(`${sistemaId}-${field.key}`)}
                                                        >
                                                            {showPassword[`${sistemaId}-${field.key}`] ? (
                                                                <EyeOff className="h-4 w-4 text-muted-foreground" />
                                                            ) : (
                                                                <Eye className="h-4 w-4 text-muted-foreground" />
                                                            )}
                                                        </Button>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
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
                            Salvar Todas as Credenciais
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
