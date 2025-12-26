import { useState, useEffect } from "react"
import { FolderOpen, Save, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ConfigService } from "@/services/config"

const pathFields = [
    { id: "csv", label: "Arquivos CSV", placeholder: "C:\\Dados\\CSV" },
    { id: "pdf", label: "Arquivos PDF", placeholder: "C:\\Dados\\PDF" },
    { id: "maps", label: "Arquivos MAPS", placeholder: "C:\\Dados\\MAPS" },
    { id: "fidc", label: "Arquivos FIDC", placeholder: "C:\\Dados\\FIDC" },
    { id: "jcot", label: "Arquivos JCOT", placeholder: "C:\\Dados\\JCOT" },
    { id: "qore_excel", label: "Excel QORE", placeholder: "C:\\Qore\\Excel" },
    { id: "britech", label: "BRITECH", placeholder: "C:\\Dados\\BRITECH" },
    { id: "output", label: "Saída (Output)", placeholder: "C:\\Output" },
]

export function PathsForm() {
    const [config, setConfig] = useState<any>({})
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)

    useEffect(() => {
        loadConfig()
    }, [])

    const loadConfig = async () => {
        setLoading(true)
        const data = await ConfigService.getConfig()
        setConfig(data)
        setLoading(false)
    }

    const handleSave = async () => {
        setSaving(true)
        const res = await ConfigService.saveConfig(config)
        setSaving(false)
        if (res.message) alert(res.message)
    }

    const handleChange = (key: string, value: string) => {
        setConfig((prev: any) => ({
            ...prev,
            paths: {
                ...prev.paths,
                [key]: value
            }
        }))
    }

    if (loading) return <div className="p-8 text-center"><Loader2 className="animate-spin inline-block" /></div>

    const paths = config.paths || {}

    return (
        <Card>
            <CardHeader>
                <CardTitle>Caminhos de Arquivos</CardTitle>
                <CardDescription>
                    Configuração dos diretórios de entrada e saída.
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
                                />
                                <Button variant="outline" size="icon" title="Selecionar Pasta">
                                    <FolderOpen className="h-4 w-4" />
                                </Button>
                            </div>
                        </div>
                    ))}
                </div>
                <div className="flex justify-end mt-4">
                    <Button onClick={handleSave} disabled={saving}>
                        {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                        Salvar Caminhos
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}
