# modules/valuation.py
class Valuation:
    def __init__(self, ticker):
        self.ticker = ticker
        self.data = self._get_data()

    def _get_data(self):
        import yfinance as yf
        info = yf.Ticker(self.ticker).info
        return info

    def intrinsic_value_per(self, expected_per=15):
        eps = self.data.get("trailingEps")
        if not eps:
            return None
        return eps * expected_per

    def intrinsic_value_dcf(self, growth_rate=0.08, discount_rate=0.10, years=5):
        fcf = self.data.get("freeCashflow")
        if not fcf:
            return None

        fcf = float(fcf)
        total_value = 0
        for year in range(1, years + 1):
            projected_fcf = fcf * ((1 + growth_rate) ** year)
            discounted_fcf = projected_fcf / ((1 + discount_rate) ** year)
            total_value += discounted_fcf

        return total_value

    def intrinsic_value_gordon(self, dividend=None, growth=0.04, discount=0.09):
        if dividend is None:
            dividend = self.data.get("dividendRate")
        if not dividend:
            return None
        return dividend * (1 + growth) / (discount - growth)

    def multiples_analysis(self):
        metrics = {
            "P/E": self.data.get("trailingPE"),
            "P/B": self.data.get("priceToBook"),
            "P/S": self.data.get("priceToSalesTrailing12Months"),
            "EV/EBITDA": self.data.get("enterpriseToEbitda"),
        }
        return {k: round(v, 2) for k, v in metrics.items() if v is not None}



def calcular_dcf(fcf, wacc, crecimiento, años=5):
    valor_presente = sum([fcf / ((1 + wacc) ** t) for t in range(1, años + 1)])
    valor_terminal = (fcf * (1 + crecimiento)) / (wacc - crecimiento)
    valor_terminal_presente = valor_terminal / ((1 + wacc) ** años)
    return round(valor_presente + valor_terminal_presente, 2)

def calcular_valor_por_multiplo(earnings, pe_ratio):
    return round(earnings * pe_ratio, 2)
