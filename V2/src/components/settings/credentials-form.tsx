"use client"

import { useState, useEffect } from "react"
import { Eye, EyeOff, Save, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ConfigService } from "@/services/config"

const sistemas = [
    { id: "maps", name: "MAPS" },
    { id: "fidc", name: "FIDC (Direitos Creditórios)" },
    { id: "jcot", name: "JCOT" },
    { id: "britech", name: "BRITECH" },
    { id: "amplis", name: "AMPLIS" },
    { id: "qore", name: "QORE" },
]

export function CredentialsForm() {
    const [config, setConfig] = useState<any>({})
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [showPassword, setShowPassword] = useState<Record<string, boolean>>({})

    // We can't import useToast if it doesn't exist yet, checking file structure...
    // Assuming simple alert for now if toast not present

    useEffect(() => {
        loadConfig()
    }, [])

    const loadConfig = async () => {
        setLoading(true)
        const data = await ConfigService.getConfig()
        setConfig(data)
        setLoading(false)
    }

    const handleSave = async (_sistema: string) => {
        setSaving(true)
        // We save the WHOLE config object
        const res = await ConfigService.saveConfig(config)
        setSaving(false)
        if (res.message) {
            alert(res.message) // Replace with Toast later
        }
    }

    const handleChange = (sistema: string, field: string, value: string) => {
        setConfig((prev: any) => ({
            ...prev,
            [sistema]: {
                ...prev[sistema],
                [field]: value
            }
        }))
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

    return (
        <div className="grid gap-6">
            <Card>
                <CardHeader>
                    <CardTitle>Credenciais dos Sistemas</CardTitle>
                    <CardDescription>
                        Gerencie o acesso aos sistemas externos.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Tabs defaultValue="maps" className="w-full">
                        <TabsList className="grid w-full grid-cols-3 lg:grid-cols-6 h-auto">
                            {sistemas.map(sys => (
                                <TabsTrigger key={sys.id} value={sys.id} className="text-xs sm:text-sm">
                                    {sys.name.split(" ")[0]}
                                </TabsTrigger>
                            ))}
                        </TabsList>
                        {sistemas.map(sys => {
                            // Safe access to config object
                            const sysConfig = config[sys.id] || {}

                            return (
                                <TabsContent key={sys.id} value={sys.id} className="space-y-4 mt-4 border p-4 rounded-md">
                                    <div className="grid gap-2">
                                        <Label htmlFor={`${sys.id}-url`}>URL de Acesso</Label>
                                        <Input
                                            id={`${sys.id}-url`}
                                            value={sysConfig.url || ""}
                                            onChange={(e) => handleChange(sys.id, "url", e.target.value)}
                                            placeholder={`https://api.${sys.id}.com.br`}
                                        />
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="grid gap-2">
                                            <Label htmlFor={`${sys.id}-user`}>Usuário</Label>
                                            <Input
                                                id={`${sys.id}-user`}
                                                value={sysConfig.username || ""}
                                                onChange={(e) => handleChange(sys.id, "username", e.target.value)}
                                                placeholder="username"
                                            />
                                        </div>
                                        <div className="grid gap-2">
                                            <Label htmlFor={`${sys.id}-pass`}>Senha</Label>
                                            <div className="relative">
                                                <Input
                                                    id={`${sys.id}-pass`}
                                                    type={showPassword[sys.id] ? "text" : "password"}
                                                    value={sysConfig.password || ""}
                                                    onChange={(e) => handleChange(sys.id, "password", e.target.value)}
                                                    placeholder="••••••••"
                                                />
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                                                    onClick={() => togglePassword(sys.id)}
                                                >
                                                    {showPassword[sys.id] ? (
                                                        <EyeOff className="h-4 w-4 text-muted-foreground" />
                                                    ) : (
                                                        <Eye className="h-4 w-4 text-muted-foreground" />
                                                    )}
                                                </Button>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex justify-end pt-2">
                                        <Button size="sm" onClick={() => handleSave(sys.id)} disabled={saving}>
                                            {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                                            Salvar {sys.name}
                                        </Button>
                                    </div>
                                </TabsContent>
                            )
                        })}
                    </Tabs>
                </CardContent>
            </Card>
        </div>
    )
}
