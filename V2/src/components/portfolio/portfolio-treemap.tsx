import { ResponsiveContainer, Treemap, Tooltip } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { PORTFOLIO_COLORS } from "@/types/portfolio"

const data = [
    {
        name: "Renda Fixa",
        children: [
            { name: "Tesouro Selic", size: 250000 },
            { name: "Debêntures AAA", size: 100000 },
            { name: "CDBs Bancários", size: 50000 },
        ],
        itemColor: PORTFOLIO_COLORS.rf
    },
    {
        name: "Renda Variável",
        children: [
            { name: "Ações Blue Chips", size: 120000 },
            { name: "Small Caps", size: 50000 },
            { name: "ETFs Globais", size: 30000 },
        ],
        itemColor: PORTFOLIO_COLORS.rv
    },
    {
        name: "Direitos Creditórios",
        children: [
            { name: "FIDC Multispy", size: 80000 },
            { name: "FIDC Tech", size: 20000 },
        ],
        itemColor: PORTFOLIO_COLORS.dir_cred
    },
    {
        name: "Caixa",
        children: [
            { name: "Disponível", size: 150000 },
        ],
        itemColor: PORTFOLIO_COLORS.caixa
    },
    {
        name: "CPR",
        children: [
            { name: "CPR Financeira", size: 100000 },
        ],
        itemColor: PORTFOLIO_COLORS.cpr
    },
]

// Custom content for Treemap tiles
const CustomizedContent = (props: any) => {
    const { depth, x, y, width, height, name, payload } = props;

    return (
        <g>
            <rect
                x={x}
                y={y}
                width={width}
                height={height}
                style={{
                    fill: depth < 2 ? payload.itemColor || "#8884d8" : "none",
                    stroke: "#fff",
                    strokeWidth: 2 / (depth + 1e-10),
                    strokeOpacity: 1 / (depth + 1e-10),
                }}
            />
            {depth === 1 ? (
                <text
                    x={x + width / 2}
                    y={y + height / 2 + 7}
                    textAnchor="middle"
                    fill="#fff"
                    fontSize={14}
                    fontWeight="bold"
                >
                    {name}
                </text>
            ) : null}
        </g>
    );
};

export function PortfolioTreemap() {
    return (
        <Card className="w-full">
            <CardHeader>
                <CardTitle>Distribuição de Ativos (Detalhada)</CardTitle>
                <CardDescription>
                    Visão hierárquica por classe e ativo.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                    <Treemap
                        data={data}
                        dataKey="size"
                        stroke="#fff"
                        fill="#8884d8"
                        content={<CustomizedContent />}
                    >
                        <Tooltip
                            contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', color: 'hsl(var(--card-foreground))' }}
                            itemStyle={{ color: 'hsl(var(--card-foreground))' }}
                            formatter={(value: any) => `R$ ${value.toLocaleString('pt-BR')}`}
                        />
                    </Treemap>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    )
}
