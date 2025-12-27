import { AlertCircle, CheckCircle2, Clock } from "lucide-react"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export function RecentActivity() {
    const activities = [
        {
            id: 1,
            job: "Import Funds (AMPLIS)",
            status: "success",
            time: "2 mins ago",
        },
        {
            id: 2,
            job: "Process XML (QORE)",
            status: "warning",
            time: "15 mins ago",
        },
        {
            id: 3,
            job: "Upload FIDC (MAPS)",
            status: "error",
            time: "1 hour ago",
        },
        {
            id: 4,
            job: "Sync Database",
            status: "success",
            time: "2 hours ago",
        },
        {
            id: 5,
            job: "Generate Reports",
            status: "success",
            time: "3 hours ago",
        },
    ]

    return (
        <Card className="col-span-4 lg:col-span-1">
            <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Latest system events.</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="space-y-8">
                    {activities.map((activity) => (
                        <div key={activity.id} className="flex items-center">
                            <div className="mr-4 mt-0.5">
                                {activity.status === "success" && (
                                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                                )}
                                {activity.status === "warning" && (
                                    <Clock className="h-4 w-4 text-yellow-500" />
                                )}
                                {activity.status === "error" && (
                                    <AlertCircle className="h-4 w-4 text-red-500" />
                                )}
                            </div>
                            <div className="w-full space-y-1">
                                <p className="text-sm font-medium leading-none">
                                    {activity.job}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                    {activity.time}
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    )
}
