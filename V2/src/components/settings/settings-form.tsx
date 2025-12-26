import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export function SettingsForm() {
    return (
        <div className="grid gap-6">
            <Card>
                <CardHeader>
                    <CardTitle>General Settings</CardTitle>
                    <CardDescription>
                        Configure general application behavior.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center justify-between space-x-2">
                        <Label htmlFor="auto-refresh" className="flex flex-col space-y-1">
                            <span>Auto Refresh Dashboard</span>
                            <span className="font-normal text-muted-foreground">
                                Automatically refresh dashboard data every 30 seconds.
                            </span>
                        </Label>
                        <Switch id="auto-refresh" defaultChecked />
                    </div>
                    <div className="flex items-center justify-between space-x-2">
                        <Label htmlFor="notifications" className="flex flex-col space-y-1">
                            <span>Enable Notifications</span>
                            <span className="font-normal text-muted-foreground">
                                Show desktop notifications for failed jobs.
                            </span>
                        </Label>
                        <Switch id="notifications" />
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle>Advanced</CardTitle>
                    <CardDescription>
                        System parameters.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid w-full max-w-sm items-center gap-1.5">
                        <Label htmlFor="api-url">Backend API URL</Label>
                        <Input type="text" id="api-url" placeholder="http://localhost:4001" defaultValue="http://localhost:4001" disabled />
                        <p className="text-sm text-muted-foreground">Configured via environment variables.</p>
                    </div>
                </CardContent>
            </Card>
            <div className="flex justify-end">
                <Button>Save Changes</Button>
            </div>
        </div>
    )
}
