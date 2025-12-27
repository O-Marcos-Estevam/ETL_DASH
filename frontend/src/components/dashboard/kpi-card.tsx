import { type LucideIcon } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface KpiCardProps {
    title: string
    value: string | number
    icon: LucideIcon
    description?: string
    trend?: "up" | "down" | "neutral"
    className?: string
}

export function KpiCard({
    title,
    value,
    icon: Icon,
    description,
    trend,
    className,
}: KpiCardProps) {
    return (
        <Card className={cn("overflow-hidden", className)}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                    {title}
                </CardTitle>
                <Icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold">{value}</div>
                {description && (
                    <p className="text-xs text-muted-foreground mt-1">
                        {description}
                        {trend === "up" && <span className="text-green-500 ml-1">↑</span>}
                        {trend === "down" && <span className="text-red-500 ml-1">↓</span>}
                    </p>
                )}
            </CardContent>
        </Card>
    )
}
