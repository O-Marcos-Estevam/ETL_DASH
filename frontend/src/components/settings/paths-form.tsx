"use client"

import { useState, useEffect } from "react"
import { FolderOpen, Save, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useToast } from "@/components/ui/use-toast"
import { api } from "@/services/api"

const pathFields = [
    { id: "csv", label: "CSV AMPLIS", placeholder: "C:\\Dados\\CSV_AMPLIS" },
    { id: "pdf", label: "Arquivos PDF", placeholder: "C:\\Dados\\PDF" },
    { id: "maps", label: "Excel MAPS", placeholder: "C:\\Dados\\EXCEL_MAPS" },
    { id: "fidc", label: "FIDC Estoque", placeholder: "C:\\Dados\\FIDC_ESTOQUE" },
    { id: "jcot", label: "Excel JCOT", placeholder: "C:\\Dados\\EXCEL_JCOT" },
    { id: "britech", label: "Excel BRITECH", placeholder: "C:\\Dados\\EXCEL_BRITECH" },
    { id: "qore_excel", label: "Excel QORE", placeholder: "C:\\Dados\\QORE_EXCEL" },
    { id: "qore_pdf", label: "PDF QORE", placeholder: "C:\\Dados\\QORE_PDF" },
    { id: "bd_xlsx", label: "BD.xlsx (DEPARA)", placeholder: "C:\\Dados\\DEPARA\\BD.xlsx" },
    { id: "trustee", label: "Auxiliar Trustee", placeholder: "C:\\Dados\\AUXLIAR_TRUSTEE" },
    { id: "selenium_temp", label: "Selenium Downloads", placeholder: "C:\\Temp\\SELENIUM_DOWNLOADS" },
]

export function PathsForm() {
    const [credentials, setCredentials] = useState<any>({})
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
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
                description: "Não foi possível carregar as configurações de caminhos",
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
                description: "Caminhos salvos com sucesso"
            })
        } catch (error) {
            toast({
                title: "Erro",
                description: "Não foi possível salvar os caminhos",
                variant: "destructive"
            })
        } finally {
            setSaving(false)
        }
    }

    const handleChange = (key: string, value: string) => {
        setCredentials((prev: any) => ({
            ...prev,
            paths: {
                ...prev.paths,
                [key]: value
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

    const paths = credentials.paths || {}

    return (
        <Card>
            <CardHeader>
                <CardTitle>Caminhos de Arquivos</CardTitle>
                <CardDescription>
                    Configuração dos diretórios de entrada e saída para processamento de arquivos.
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {pathFields.map(field => (
                        <div key={field.id} className="grid w-full items-center gap-1.5">
                            <Label htmlFor={field.id}>{field.label}</Label>
                            <div className="flex gap-2">
                                <Input
                                    id={field.id}
                                    value={paths[field.id] || ""}
                                    onChange={(e) => handleChange(field.id, e.target.value)}
                                    placeholder={field.placeholder}
                                    className="text-xs"
                                />
                                <Button
                                    variant="outline"
                                    size="icon"
                                    title="Selecionar Pasta"
                                    type="button"
                                >
                                    <FolderOpen className="h-4 w-4" />
                                </Button>
                            </div>
                        </div>
                    ))}
                </div>
                <div className="flex justify-end mt-4">
                    <Button onClick={handleSave} disabled={saving}>
                        {saving ? (
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                            <Save className="mr-2 h-4 w-4" />
                        )}
                        Salvar Caminhos
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}
