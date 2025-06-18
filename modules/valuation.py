# modules/valuation.py
from modules.api_fallback import APIFallbackManager
import yfinance as yf
from typing import Optional, Dict, Any
from modules.fetcher import StockDataFetcher
import streamlit as st

# modules/valuation.py

class Valuation:
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.stock = yf.Ticker(self.ticker)
        self.api_fallback = APIFallbackManager()
        self.fetcher = StockDataFetcher(self.ticker)
        self.data = self._get_fundamental_data()
        self._validate_data()
        if not self.ticker or not isinstance(self.ticker, str):
            raise ValueError("Ticker inválido o vacío.")


    def _get_fundamental_data(self) -> Dict[str, Any]:
        """Fetch fundamental data with prioritized fallback logic"""
        data_sources = [
            self._try_yfinance_data,  # Most reliable free source
            self._try_alphavantage_data,
            self._try_polygon_data,
            self._try_finnhub_data,
            self._try_tiingo_data,
            self._try_finage_data,
            self._try_quandl_data
        ]

        collected_data = {}
        required_fields = ["trailingEps", "currentPrice"]
        
        for source in data_sources:
            try:
                data = source()
                if data:
                    collected_data.update(data)
                    
                    # Check if we have minimum required data
                    if all(field in collected_data and collected_data[field] is not None 
                        for field in required_fields):
                        return collected_data
                        
            except Exception as e:
                print(f"⚠️ Error in {source.__name__}: {str(e)[:100]}")

        # Return whatever partial data we have
        return collected_data if collected_data else {
            "trailingEps": None,
            "freeCashflow": None,
            "dividendRate": None,
            "currentPrice": None,
            "sharesOutstanding": None,
            "marketCap": None
        }

    def _validate_data(self) -> None:
        """Validate that required data is available."""
        if not self.data:
            raise ValueError(f"No fundamental data available for {self.ticker}")
        
        if "fundamentals" in self.data:
            self.fundamentals_df = self.data["fundamentals"]
        else:
            self.fundamentals_df = None

    def _try_yfinance_data(self) -> Dict[str, Any]:
        """Try to get data from Yahoo Finance with better error handling."""
        try:
            data = self.fetcher._get_fundamental_data_yfinance()
            if not data:
                return {}
                
            # Validate we have minimum required data
            required_fields = ['trailingEps', 'currentPrice']
            if not all(field in data and data[field] is not None for field in required_fields):
                return {}
                
            return data
        except Exception as e:
            print(f"Error fetching YFinance data: {str(e)}")
            return {}

    def _try_alphavantage_data(self) -> Dict[str, Any]:
        """Try to get data from Alpha Vantage."""
        data = self.fetcher._get_fundamental_data_alphavantage()  # Changed
        if data and data.get("trailingEps") is not None:
            print(f"✅ Data obtained from Alpha Vantage for {self.ticker}")
            return data
        return {}


    def _try_finnhub_data(self) -> Dict[str, Any]:
        """Try to get data from Finnhub."""
        data = self.fetcher.get_data_finnhub()
        if data and data.get("trailingEps") is not None:
            print(f"✅ Data obtained from Finnhub for {self.ticker}")
            return data
        return {}

    def _try_tiingo_data(self) -> Dict[str, Any]:
        """Try to get data from Tiingo."""
        data = self.fetcher.get_data_tiingo()
        if data and data.get("trailingEps") is not None:
            print(f"✅ Data obtained from Tiingo for {self.ticker}")
            return data
        return {}

    def _try_polygon_data(self) -> Dict[str, Any]:
        """Try to get data from Polygon."""
        data = self.fetcher._get_fundamental_data_polygon()  # Changed from get_data_polygon()
        if data and data.get("trailingEps") is not None:
            print(f"✅ Data obtained from Polygon for {self.ticker}")
            return data
        return {}

    # Similarly update all other _try_* methods to use _get_fundamental_data_* instead of get_data_*

    def _try_finage_data(self) -> Dict[str, Any]:
        """Try to get data from Finage."""
        data = self.fetcher.get_data_finage()
        if data and data.get("trailingEps") is not None:
            print(f"✅ Data obtained from Finage for {self.ticker}")
            return data
        return {}

    def _try_quandl_data(self) -> Dict[str, Any]:
        """Try to get data from Quandl."""
        data = self.fetcher.get_data_quandl()
        if data and data.get("trailingEps") is not None:
            print(f"✅ Data obtained from Quandl for {self.ticker}")
            return data
        return {}

    def intrinsic_value_per(self, expected_per: float = 15) -> Optional[float]:
        """Calculate intrinsic value using P/E ratio method."""
        eps = self.data.get("trailingEps")
        return eps * expected_per if eps is not None else None
    # In intrinsic_value_dcf method:
    def intrinsic_value_dcf(self, years: int = 5, growth_rate: Optional[float] = None,
                      terminal_growth: Optional[float] = None, 
                      discount_rate: Optional[float] = None) -> Optional[float]:
        """
        Calculate intrinsic value using Discounted Cash Flow method with robust error handling.
        """
        try:
            # 1. Get Free Cash Flow with comprehensive fallbacks
            fcf = self._get_valid_fcf()
            if fcf is None:
                # st.warning("Could not determine valid Free Cash Flow")
                return None

            # 2. Get Shares Outstanding with comprehensive fallbacks
            shares_outstanding = self._get_valid_shares_outstanding()
            if shares_outstanding is None:
                # st.warning("Could not determine valid shares outstanding")
                return None

            # 3. Validate and set default rates if needed
            growth_rate = growth_rate if growth_rate is not None else self._estimate_safe_growth_rate()
            terminal_growth = terminal_growth if terminal_growth is not None else 0.03  # Conservative long-term GDP growth
            discount_rate = discount_rate if discount_rate is not None else self._calculate_safe_wacc()

            # 4. Validate rate relationships
            if discount_rate <= terminal_growth:
                # st.warning("Discount rate must be greater than terminal growth rate")
                return None

            # 5. Calculate DCF components
            discounted_fcf = sum(
                fcf * ((1 + growth_rate) ** t) / ((1 + discount_rate) ** t)
                for t in range(1, years + 1)
            )

            terminal_value = (fcf * (1 + growth_rate) * (1 + terminal_growth)) / (discount_rate - terminal_growth)
            terminal_value_discounted = terminal_value / ((1 + discount_rate) ** years)

            # 6. Calculate and return intrinsic value
            intrinsic_value = (discounted_fcf + terminal_value_discounted) / shares_outstanding
            return round(intrinsic_value, 2)

        except Exception as e:
            # st.error(f"DCF calculation failed: {str(e)}")
            return None

    def _get_valid_fcf(self) -> Optional[float]:
        """Safely retrieve Free Cash Flow with multiple fallback methods."""
        try:
            # Try direct FCF fields first
            for field in ['freeCashflow', 'freeCashFlow', 'fcf']:
                if field in self.data and self.data[field] is not None:
                    return float(self.data[field])
            
            # Try calculating from components if available
            if all(k in self.data for k in ['operatingCashflow', 'capitalExpenditures']):
                return float(self.data['operatingCashflow']) - float(self.data['capitalExpenditures'])
            
            # Try fundamentals DataFrame if it exists and has data
            if hasattr(self, 'fundamentals_df') and self.fundamentals_df is not None:
                for col in ['FreeCashFlow', 'Free Cash Flow', 'FCF']:
                    if col in self.fundamentals_df.columns:
                        return float(self.fundamentals_df[col].iloc[0])
            
            return None
        except Exception as e:
            st.error(f"FCF retrieval failed: {str(e)}")
            return None

    def _get_valid_shares_outstanding(self) -> Optional[float]:
        """Safely retrieve Shares Outstanding with multiple fallback methods."""
        try:
            # Try direct fields first
            for field in ['sharesOutstanding', 'shares']:
                if field in self.data and self.data[field] is not None:
                    return float(self.data[field])
            
            # Calculate from market cap if available
            if all(k in self.data for k in ['marketCap', 'currentPrice']):
                return float(self.data['marketCap']) / float(self.data['currentPrice'])
            
            # Try fundamentals DataFrame if it exists and has data
            if hasattr(self, 'fundamentals_df') and self.fundamentals_df is not None:
                for col in ['SharesOutstanding', 'Shares Outstanding']:
                    if col in self.fundamentals_df.columns:
                        return float(self.fundamentals_df[col].iloc[0])
            
            return None
        except Exception as e:
            st.error(f"Shares outstanding retrieval failed: {str(e)}")
            return None

    def _estimate_safe_growth_rate(self) -> float:
        """Estimate a safe growth rate with fallback."""
        try:
            rate = self.estimate_growth_rate()
            return max(min(rate, 0.15), 0.01)  # Cap at 15%, minimum 1%
        except:
            return 0.05  # Default 5% growth

    def _calculate_safe_wacc(self) -> float:
        """Return a conservative default WACC if calculation fails."""
        try:
            wacc = self.calculate_wacc()
            return max(min(wacc, 0.15), 0.06)  # Cap at 15%, minimum 6%
        except:
            return 0.08  # Default 8% WACC

    def _get_fcf_with_fallbacks(self) -> Optional[float]:
        """Try multiple ways to get Free Cash Flow."""
        # Try direct FCF fields first
        for field in ['freeCashflow', 'freeCashFlow', 'fcf', 'FreeCashFlow']:
            if field in self.data and self.data[field] is not None:
                try:
                    return float(self.data[field])
                except (TypeError, ValueError):
                    continue
        
        # Try calculating from components
        if all(field in self.data for field in ['operatingCashflow', 'capitalExpenditures']):
            try:
                return float(self.data['operatingCashflow']) - float(self.data['capitalExpenditures'])
            except (TypeError, ValueError):
                pass
        
        # Try getting from fundamentals if available
        if hasattr(self, 'fundamentals_df'):
            for col in ['FreeCashFlow', 'Free Cash Flow', 'FCF']:
                if col in self.fundamentals_df.columns:
                    try:
                        return float(self.fundamentals_df[col].iloc[0])
                    except (TypeError, ValueError, IndexError):
                        continue
        return None

    def _get_shares_outstanding_with_fallbacks(self) -> Optional[float]:
        """Try multiple ways to get shares outstanding."""
        # Try direct fields first
        for field in ['sharesOutstanding', 'shares', 'SharesOutstanding']:
            if field in self.data and self.data[field] is not None:
                try:
                    return float(self.data[field])
                except (TypeError, ValueError):
                    continue
        
        # Try calculating from market cap and price
        if all(field in self.data for field in ['marketCap', 'currentPrice']):
            try:
                return float(self.data['marketCap']) / float(self.data['currentPrice'])
            except (TypeError, ValueError, ZeroDivisionError):
                pass
        
        # Try getting from fundamentals if available
        if hasattr(self, 'fundamentals_df'):
            for col in ['SharesOutstanding', 'Shares Outstanding']:
                if col in self.fundamentals_df.columns:
                    try:
                        return float(self.fundamentals_df[col].iloc[0])
                    except (TypeError, ValueError, IndexError):
                        continue
        return None

    # Helper methods would be added to the class:
    def _get_fcf_from_cashflow_statement(self) -> Optional[float]:
        """Try to get FCF from cashflow statement if available."""
        if hasattr(self, 'fundamentals_df'):
            for col in ['FreeCashFlow', 'Free Cash Flow', 'FCF']:
                if col in self.fundamentals_df:
                    return self.fundamentals_df[col]
        return None

    def _estimate_fcf_from_components(self) -> Optional[float]:
        """Estimate FCF from operating cash flow and capital expenditures."""
        if 'operatingCashflow' in self.data and 'capitalExpenditures' in self.data:
            try:
                return float(self.data['operatingCashflow']) - float(self.data['capitalExpenditures'])
            except (TypeError, ValueError):
                pass
        return None

    def _calculate_shares_from_market_cap(self) -> Optional[float]:
        """Calculate shares outstanding from market cap and current price."""
        if 'marketCap' in self.data and 'currentPrice' in self.data:
            try:
                return float(self.data['marketCap']) / float(self.data['currentPrice'])
            except (TypeError, ValueError, ZeroDivisionError):
                pass
        return None

    def _get_shares_from_fundamentals(self) -> Optional[float]:
        """Try to get shares from fundamentals if available."""
        if hasattr(self, 'fundamentals_df'):
            for col in ['SharesOutstanding', 'Shares Outstanding']:
                if col in self.fundamentals_df:
                    return self.fundamentals_df[col]
        return None


    def estimate_growth_rate(self, years: int = 5) -> float:
        """Estimate growth rate based on historical free cash flow."""
        try:
            ticker_obj = yf.Ticker(self.ticker)
            cashflow = ticker_obj.cashflow

            # Possible labels for free cash flow
            possible_keys = [
                'Free Cash Flow',
                'FreeCashFlow',
                'Total Cash From Operating Activities',
                'Operating Cash Flow'
            ]

            fcf = None
            for key in possible_keys:
                if key in cashflow.index:
                    fcf = cashflow.loc[key].dropna().astype(float)
                    break
            
            if fcf is not None and len(fcf) >= years:
                start = fcf.iloc[-1]
                end = fcf.iloc[0]
                cagr = (end / start) ** (1 / years) - 1
                return round(cagr, 4)
        except Exception as e:
            print(f"Error estimating growth rate: {e}")

        return 0.08  # Conservative fallback

    def estimate_terminal_growth(self) -> float:
        """Estimate terminal growth rate (long-term GDP + inflation)."""
        return 0.03

    def calculate_wacc(self) -> float:
        """Calculate Weighted Average Cost of Capital."""
        try:
            beta = float(self.data.get("beta", 1.2))
            ke = beta * 0.05 + 0.02  # CAPM: rf + beta * (rm - rf)
            kd = float(self.data.get("yield", 0.03))
            tax_rate = float(self.data.get("effectiveTaxRate", 0.21))
            equity = float(self.data.get("marketCap", 1))
            debt = float(self.data.get("totalDebt", 1))
            total = equity + debt
            
            wacc = (equity / total) * ke + (debt / total) * kd * (1 - tax_rate)
            return round(wacc, 4)
        except Exception:
            return 0.09  # Fallback value

    def current_price(self):
        try:
            data = self.stock.history(period="1d")
            if data.empty:
                return None
            return data["Close"].iloc[-1]
        except Exception as e:
            print(f"Error al obtener el precio actual: {e}")
            return None


    def intrinsic_value_gordon(
        self,
        dividend: Optional[float] = None,
        growth: float = 0.04,
        discount: float = 0.09
    ) -> Optional[float]:
        """Calculate intrinsic value using Gordon Growth Model."""
        dividend = dividend or self.data.get("dividendRate")
        if dividend is None:
            return None
            
        if discount <= growth:
            raise ValueError("Discount rate must be greater than growth rate")
            
        return dividend * (1 + growth) / (discount - growth)

    def multiples_analysis(self) -> Dict[str, Optional[float]]:
        """Analyze valuation multiples."""
        metrics = {
            "P/E": self.data.get("trailingPE"),
            "P/B": self.data.get("priceToBook"),
            "P/S": self.data.get("priceToSalesTrailing12Months"),
            "EV/EBITDA": self.data.get("enterpriseToEbitda"),
        }
        return {k: round(v, 2) if v is not None else None for k, v in metrics.items()}