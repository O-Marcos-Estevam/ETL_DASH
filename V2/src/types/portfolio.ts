/**
 * Portfolio and Composition Types
 */

export interface CarteiraPosicao {
    fundo: string
    data: string
    pos_caixa: number      // Caixa
    pos_rf: number         // Renda Fixa
    pos_rv: number         // Renda Variável
    pos_dir_cred: number   // Direitos Creditórios
    pos_cpr: number        // CPR e Duplicatas
}

export interface CarteiraTotal {
    fundo: string
    patrimonio: number
    composicao: {
        caixa: number
        rf: number
        rv: number
        credito: number
        cpr: number
    }
}

// Fixed colors for consistency
export const PORTFOLIO_COLORS = {
    caixa: "hsl(142, 76%, 36%)",      // Green
    rf: "hsl(217, 91%, 60%)",         // Blue
    rv: "hsl(262, 83%, 58%)",         // Purple
    dir_cred: "hsl(25, 95%, 53%)",    // Orange
    cpr: "hsl(48, 96%, 53%)"          // Yellow
}
