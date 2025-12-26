import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { PORTFOLIO_COLORS } from "@/types/portfolio"

const mockData = [
    {
        month: "Jan",
        caixa: 15,
        rf: 45,
        rv: 20,
        credito: 10,
        cpr: 10
    },
    {
        month: "Fev",
        caixa: 12,
        rf: 48,
        rv: 22,
        credito: 8,
        cpr: 10
    },
    {
        month: "Mar",
        caixa: 18,
        rf: 42,
        rv: 25,
        credito: 5,
        cpr: 10
    },
    {
        month: "Abr",
        caixa: 20,
        rf: 40,
        rv: 25,
        credito: 5,
        cpr: 10
    },
]

export function PortfolioStackedChart() {
    return (
        <Card className="w-full">
            <CardHeader>
                <CardTitle>Evolução da Composição</CardTitle>
                <CardDescription>
                    Distribuição das classes de ativos nos últimos meses.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                    <BarChart
                        data={mockData}
                        margin={{
                            top: 20,
                            right: 30,
                            left: 20,
                            bottom: 5,
                        }}
                    >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                        <XAxis
                            dataKey="month"
                            stroke="hsl(var(--muted-foreground))"
                            fontSize={12}
                            tickLine={false}
                            axisLine={false}
                        />
                        <YAxis
                            stroke="hsl(var(--muted-foreground))"
                            fontSize={12}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(value) => `${value}%`}
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', color: 'hsl(var(--card-foreground))' }}
                            itemStyle={{ color: 'hsl(var(--card-foreground))' }}
                            cursor={{ fill: 'hsl(var(--muted)/0.2)' }}
                        />
                        <Legend wrapperStyle={{ paddingTop: "20px" }} />
                        <Bar dataKey="caixa" name="Caixa" stackId="a" fill={PORTFOLIO_COLORS.caixa} />
                        <Bar dataKey="rf" name="Renda Fixa" stackId="a" fill={PORTFOLIO_COLORS.rf} />
                        <Bar dataKey="rv" name="Renda Variável" stackId="a" fill={PORTFOLIO_COLORS.rv} />
                        <Bar dataKey="credito" name="Dir. Creditórios" stackId="a" fill={PORTFOLIO_COLORS.dir_cred} />
                        <Bar dataKey="cpr" name="CPR" stackId="a" fill={PORTFOLIO_COLORS.cpr} />
                    </BarChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    )
}
