import { SettingsForm } from "@/components/settings/settings-form"
import { CredentialsForm } from "@/components/settings/credentials-form"
import { PathsForm } from "@/components/settings/paths-form"
import { FundsForm } from "@/components/settings/funds-form"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export function SettingsPage() {
    return (
        <div className="flex flex-col gap-6">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
                <p className="text-muted-foreground">
                    Manage system configuration and preferences.
                </p>
            </div>

            <Tabs defaultValue="general" className="space-y-4">
                <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="general">Geral</TabsTrigger>
                    <TabsTrigger value="credentials">Credenciais</TabsTrigger>
                    <TabsTrigger value="paths">Caminhos</TabsTrigger>
                    <TabsTrigger value="funds">Fundos</TabsTrigger>
                </TabsList>
                <TabsContent value="general" className="space-y-4">
                    <SettingsForm />
                </TabsContent>
                <TabsContent value="credentials" className="space-y-4">
                    <CredentialsForm />
                </TabsContent>
                <TabsContent value="paths" className="space-y-4">
                    <PathsForm />
                </TabsContent>
                <TabsContent value="funds" className="space-y-4">
                    <FundsForm />
                </TabsContent>
            </Tabs>
        </div>
    )
}
