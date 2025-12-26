"use client"

import { useState, useEffect } from "react"
import { Save, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useToast } from "@/components/ui/use-toast"

// Chave para localStorage
const SETTINGS_KEY = "etl_dashboard_settings"

// Configurações padrão
const defaultSettings = {
    autoRefresh: true,
    autoRefreshInterval: 30,
    notifications: false,
    darkMode: false,
    logRetentionDays: 7
}

export type Settings = typeof defaultSettings

export function SettingsForm() {
    const [settings, setSettings] = useState<Settings>(defaultSettings)
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const { toast } = useToast()

    useEffect(() => {
        loadSettings()
    }, [])

    const loadSettings = () => {
        setLoading(true)
        try {
            const stored = localStorage.getItem(SETTINGS_KEY)
            if (stored) {
                const parsed = JSON.parse(stored)
                setSettings({ ...defaultSettings, ...parsed })
            }
        } catch (error) {
            console.error("Erro ao carregar configurações:", error)
        } finally {
            setLoading(false)
        }
    }

    const handleSave = () => {
        setSaving(true)
        try {
            localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
            toast({
                title: "Sucesso",
                description: "Configurações salvas com sucesso"
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

    const handleChange = <K extends keyof Settings>(key: K, value: Settings[K]) => {
        setSettings(prev => ({ ...prev, [key]: value }))
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
                    <CardTitle>Configurações Gerais</CardTitle>
                    <CardDescription>
                        Configure o comportamento geral da aplicação.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="flex items-center justify-between space-x-2">
                        <Label htmlFor="auto-refresh" className="flex flex-col space-y-1">
                            <span>Auto Refresh Dashboard</span>
                            <span className="font-normal text-sm text-muted-foreground">
                                Atualiza automaticamente os dados do dashboard.
                            </span>
                        </Label>
                        <Switch
                            id="auto-refresh"
                            checked={settings.autoRefresh}
                            onCheckedChange={(checked) => handleChange("autoRefresh", checked)}
                        />
                    </div>

                    {settings.autoRefresh && (
                        <div className="grid w-full max-w-xs items-center gap-1.5 pl-4 border-l-2 border-muted">
                            <Label htmlFor="refresh-interval">Intervalo (segundos)</Label>
                            <Input
                                id="refresh-interval"
                                type="number"
                                min={10}
                                max={300}
                                value={settings.autoRefreshInterval}
                                onChange={(e) => handleChange("autoRefreshInterval", parseInt(e.target.value) || 30)}
                                className="w-24"
                            />
                        </div>
                    )}

                    <div className="flex items-center justify-between space-x-2">
                        <Label htmlFor="notifications" className="flex flex-col space-y-1">
                            <span>Notificações Desktop</span>
                            <span className="font-normal text-sm text-muted-foreground">
                                Exibe notificações do sistema para jobs finalizados.
                            </span>
                        </Label>
                        <Switch
                            id="notifications"
                            checked={settings.notifications}
                            onCheckedChange={(checked) => handleChange("notifications", checked)}
                        />
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle>Avançado</CardTitle>
                    <CardDescription>
                        Parâmetros do sistema.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid w-full max-w-sm items-center gap-1.5">
                        <Label htmlFor="api-url">Backend API URL</Label>
                        <Input
                            type="text"
                            id="api-url"
                            placeholder="http://localhost:4001"
                            defaultValue="http://localhost:4001"
                            disabled
                        />
                        <p className="text-sm text-muted-foreground">
                            Configurado via variáveis de ambiente.
                        </p>
                    </div>

                    <div className="grid w-full max-w-xs items-center gap-1.5">
                        <Label htmlFor="log-retention">Retenção de Logs (dias)</Label>
                        <Input
                            id="log-retention"
                            type="number"
                            min={1}
                            max={90}
                            value={settings.logRetentionDays}
                            onChange={(e) => handleChange("logRetentionDays", parseInt(e.target.value) || 7)}
                            className="w-24"
                        />
                        <p className="text-sm text-muted-foreground">
                            Logs mais antigos serão removidos automaticamente.
                        </p>
                    </div>
                </CardContent>
            </Card>

            <div className="flex justify-end">
                <Button onClick={handleSave} disabled={saving}>
                    {saving ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                        <Save className="mr-2 h-4 w-4" />
                    )}
                    Salvar Configurações
                </Button>
            </div>
        </div>
    )
}
