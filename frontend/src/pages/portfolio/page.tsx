import { useState } from "react"
import { PieChart, BarChart3, Layers } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { PortfolioStackedChart } from "@/components/portfolio/portfolio-stacked-chart"
import { PortfolioTreemap } from "@/components/portfolio/portfolio-treemap"
import { PORTFOLIO_COLORS } from "@/types/portfolio"

export function PortfolioPage() {
    const [selectedFundo, setSelectedFundo] = useState("all")

    // Mock total stats similar to KPI cards
    const stats = [
        { label: "Patrimônio Total", value: "R$ 45.2M", color: "text-primary" },
        { label: "Caixa", value: "R$ 6.8M", color: `text-[${PORTFOLIO_COLORS.caixa}]` },
        { label: "Renda Fixa", value: "R$ 18.5M", color: `text-[${PORTFOLIO_COLORS.rf}]` },
        { label: "Renda Variável", value: "R$ 11.3M", color: `text-[${PORTFOLIO_COLORS.rv}]` },
        { label: "Crédito", value: "R$ 4.5M", color: `text-[${PORTFOLIO_COLORS.dir_cred}]` },
    ]

    return (
        <div className="flex flex-col gap-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Portfolio Analysis</h2>
                    <p className="text-muted-foreground">
                        Composição detalhada e evolução da carteira.
                    </p>
                </div>
                <div className="flex items-center gap-4">
                    <Select value={selectedFundo} onValueChange={setSelectedFundo}>
                        <SelectTrigger className="w-[200px]">
                            <SelectValue placeholder="Selecione um Fundo" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">Todos os Fundos</SelectItem>
                            <SelectItem value="fundo_a">Fundo Alpha Multimercado</SelectItem>
                            <SelectItem value="fundo_b">Fundo Beta Ações</SelectItem>
                            <SelectItem value="fundo_c">Fundo Gama Crédito</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid gap-4 md:grid-cols-5">
                {stats.map((stat, i) => (
                    <Card key={i}>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">
                                {stat.label}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Main Charts Area */}
            <Tabs defaultValue="composition" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="composition" className="flex items-center gap-2">
                        <PieChart className="h-4 w-4" />
                        Composição (Treemap)
                    </TabsTrigger>
                    <TabsTrigger value="evolution" className="flex items-center gap-2">
                        <BarChart3 className="h-4 w-4" />
                        Evolução (Barras)
                    </TabsTrigger>
                    <TabsTrigger value="holdings" className="flex items-center gap-2">
                        <Layers className="h-4 w-4" />
                        Holdings
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="composition" className="space-y-4">
                    <PortfolioTreemap />
                </TabsContent>

                <TabsContent value="evolution" className="space-y-4">
                    <PortfolioStackedChart />
                </TabsContent>

                <TabsContent value="holdings">
                    <Card>
                        <CardHeader>
                            <CardTitle>Detalhamento de Ativos</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="flex items-center justify-center h-64 text-muted-foreground">
                                Tabela de ativos será implementada na próxima fase.
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    )
}
