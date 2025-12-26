import { useState, useEffect } from "react"
import { X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { api } from "@/services/api"

interface CredentialsModalProps {
    open: boolean
    onClose: () => void
    onSave: () => void
}

export function CredentialsModal({ open, onClose, onSave }: CredentialsModalProps) {
    const [credentials, setCredentials] = useState<any>(null)
    const [jsonText, setJsonText] = useState("")
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (open) {
            loadCredentials()
        }
    }, [open])

    const loadCredentials = async () => {
        try {
            setLoading(true)
            setError(null)
            const data = await api.getCredentials()
            setCredentials(data)
            setJsonText(JSON.stringify(data, null, 2))
        } catch (err) {
            setError("Erro ao carregar credenciais")
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const handleSave = async () => {
        try {
            const dataToSave = JSON.parse(jsonText)
            await api.saveCredentials(dataToSave)
            onSave()
            onClose()
        } catch (err) {
            setError("Erro ao salvar credenciais")
        }
    }

    if (!open) return null

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="relative z-10 w-full max-w-3xl max-h-[85vh] overflow-hidden rounded-xl bg-background border shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b">
                    <h2 className="text-lg font-semibold">🔑 Credenciais dos Sistemas</h2>
                    <Button variant="ghost" size="icon" onClick={onClose}>
                        <X className="h-5 w-5" />
                    </Button>
                </div>

                {/* Body */}
                <div className="overflow-y-auto max-h-[calc(85vh-130px)]">
                    {loading ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
                        </div>
                    ) : error ? (
                        <div className="text-center py-12 text-destructive">{error}</div>
                    ) : (
                        <Tabs defaultValue="sistemas" className="w-full">
                            <TabsList className="w-full justify-start rounded-none border-b bg-transparent px-6">
                                <TabsTrigger value="sistemas">📊 Sistemas</TabsTrigger>
                                <TabsTrigger value="paths">📁 Pastas</TabsTrigger>
                                <TabsTrigger value="json">📝 JSON</TabsTrigger>
                            </TabsList>

                            <TabsContent value="sistemas" className="p-6">
                                <div className="grid gap-6 sm:grid-cols-2">
                                    {['maps', 'fidc', 'jcot', 'britech', 'qore'].map((sistema) => (
                                        <div key={sistema} className="p-4 rounded-lg bg-muted/50">
                                            <h3 className="font-semibold text-primary mb-3 uppercase">
                                                {sistema}
                                            </h3>
                                            <div className="space-y-3">
                                                <div>
                                                    <Label className="text-xs text-muted-foreground">URL</Label>
                                                    <Input
                                                        value={credentials?.[sistema]?.url || ''}
                                                        className="mt-1 bg-background"
                                                        readOnly
                                                    />
                                                </div>
                                                <div>
                                                    <Label className="text-xs text-muted-foreground">Usuário</Label>
                                                    <Input
                                                        value={credentials?.[sistema]?.username || ''}
                                                        className="mt-1 bg-background"
                                                        readOnly
                                                    />
                                                </div>
                                                <div>
                                                    <Label className="text-xs text-muted-foreground">Senha</Label>
                                                    <Input
                                                        type="password"
                                                        value={credentials?.[sistema]?.password || ''}
                                                        className="mt-1 bg-background"
                                                        readOnly
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </TabsContent>

                            <TabsContent value="paths" className="p-6">
                                <div className="p-4 rounded-lg bg-muted/50">
                                    <h3 className="font-semibold text-primary mb-4">📁 Caminhos de Download</h3>
                                    <div className="grid gap-3 sm:grid-cols-2">
                                        {['csv', 'pdf', 'jcot', 'britech', 'maps', 'fidc', 'qore_pdf', 'qore_excel'].map((path) => (
                                            <div key={path}>
                                                <Label className="text-xs text-muted-foreground uppercase">{path}</Label>
                                                <Input
                                                    value={credentials?.paths?.[path] || ''}
                                                    className="mt-1 bg-background text-xs"
                                                    readOnly
                                                />
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </TabsContent>

                            <TabsContent value="json" className="p-6">
                                <Textarea
                                    value={jsonText}
                                    onChange={(e) => setJsonText(e.target.value)}
                                    className="font-mono text-xs h-[400px] bg-muted/50"
                                    placeholder="JSON das credenciais..."
                                />
                            </TabsContent>
                        </Tabs>
                    )}
                </div>

                {/* Footer */}
                <div className="flex justify-end gap-3 px-6 py-4 border-t">
                    <Button variant="outline" onClick={onClose}>
                        Cancelar
                    </Button>
                    <Button onClick={handleSave} disabled={loading}>
                        💾 Salvar
                    </Button>
                </div>
            </div>
        </div>
    )
}
