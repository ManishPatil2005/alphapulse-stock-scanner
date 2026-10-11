"""
services/fno_engine.py
Institutional NSE Futures & Options (F&O) Engine.

Provides:
- Complete Index & Stock F&O contracts database (NIFTY, BANKNIFTY, FINNIFTY, RELIANCE, HDFCBANK, etc.)
- Expiry generation (Weekly and Monthly Thursdays)
- Complete Option Chain computation:
  * Strike prices across -15 to +15 intervals around Spot
  * CE (Calls) & PE (Puts) contracts
  * LTP, Net Change, Volume, Implied Volatility (IV)
  * Open Interest (OI) & OI Change
  * Greeks (Delta, Gamma, Theta, Vega) via Black-Scholes model
  * Put-Call Ratio (PCR = Total Put OI / Total Call OI)
  * Max Pain Strike calculation
- Futures contracts (Current Month, Next Month, Far Month) with Premium/Discount and Open Interest
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple


# Standard Normal CDF and PDF for Black-Scholes Greeks
def norm_cdf(x: float) -> float:
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0


def norm_pdf(x: float) -> float:
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)


class FnoEngine:
    """Comprehensive NSE Futures & Options analytics and contract generation."""

    # Instrument metadata configuration: Lot size, strike interval, base volatility
    FNO_CONFIG: Dict[str, Dict[str, Any]] = {
        # Indices
        "NIFTY": {"lot_size": 25, "strike_step": 50, "base_iv": 0.14, "name": "NIFTY 50 Index", "type": "INDEX"},
        "^NSEI": {"lot_size": 25, "strike_step": 50, "base_iv": 0.14, "name": "NIFTY 50 Index", "type": "INDEX"},
        "BANKNIFTY": {"lot_size": 15, "strike_step": 100, "base_iv": 0.16, "name": "NIFTY Bank Index", "type": "INDEX"},
        "^NSEBANK": {"lot_size": 15, "strike_step": 100, "base_iv": 0.16, "name": "NIFTY Bank Index", "type": "INDEX"},
        "FINNIFTY": {"lot_size": 25, "strike_step": 50, "base_iv": 0.15, "name": "NIFTY Financial Services", "type": "INDEX"},
        "MIDCPNIFTY": {"lot_size": 50, "strike_step": 25, "base_iv": 0.18, "name": "NIFTY Midcap Select", "type": "INDEX"},

        # Major Liquid Equities
        "RELIANCE": {"lot_size": 250, "strike_step": 20, "base_iv": 0.22, "name": "Reliance Industries Ltd", "type": "STOCK"},
        "HDFCBANK": {"lot_size": 550, "strike_step": 10, "base_iv": 0.19, "name": "HDFC Bank Ltd", "type": "STOCK"},
        "ICICIBANK": {"lot_size": 700, "strike_step": 10, "base_iv": 0.20, "name": "ICICI Bank Ltd", "type": "STOCK"},
        "INFY": {"lot_size": 400, "strike_step": 20, "base_iv": 0.23, "name": "Infosys Ltd", "type": "STOCK"},
        "TCS": {"lot_size": 175, "strike_step": 20, "base_iv": 0.18, "name": "Tata Consultancy Services Ltd", "type": "STOCK"},
        "SBIN": {"lot_size": 750, "strike_step": 10, "base_iv": 0.24, "name": "State Bank of India", "type": "STOCK"},
        "TATAMOTORS": {"lot_size": 700, "strike_step": 10, "base_iv": 0.28, "name": "Tata Motors Ltd", "type": "STOCK"},
        "BHARTIARTL": {"lot_size": 475, "strike_step": 10, "base_iv": 0.21, "name": "Bharti Airtel Ltd", "type": "STOCK"},
        "ITC": {"lot_size": 1600, "strike_step": 5, "base_iv": 0.17, "name": "ITC Ltd", "type": "STOCK"},
        "LT": {"lot_size": 150, "strike_step": 50, "base_iv": 0.22, "name": "Larsen & Toubro Ltd", "type": "STOCK"},
        "AXISBANK": {"lot_size": 625, "strike_step": 10, "base_iv": 0.22, "name": "Axis Bank Ltd", "type": "STOCK"},
        "KOTAKBANK": {"lot_size": 400, "strike_step": 20, "base_iv": 0.19, "name": "Kotak Mahindra Bank Ltd", "type": "STOCK"},
        "BAJFINANCE": {"lot_size": 125, "strike_step": 50, "base_iv": 0.26, "name": "Bajaj Finance Ltd", "type": "STOCK"},
        "MARUTI": {"lot_size": 50, "strike_step": 100, "base_iv": 0.21, "name": "Maruti Suzuki India Ltd", "type": "STOCK"},
        "SUNPHARMA": {"lot_size": 350, "strike_step": 20, "base_iv": 0.20, "name": "Sun Pharma Industries", "type": "STOCK"},
        "TITAN": {"lot_size": 175, "strike_step": 20, "base_iv": 0.22, "name": "Titan Company Ltd", "type": "STOCK"},
        "TRENT": {"lot_size": 100, "strike_step": 100, "base_iv": 0.32, "name": "Trent Ltd", "type": "STOCK"},
        "TATASTEEL": {"lot_size": 5500, "strike_step": 2, "base_iv": 0.29, "name": "Tata Steel Ltd", "type": "STOCK"},
    }

    @classmethod
    def clean_symbol(cls, symbol: str) -> str:
        s = symbol.upper().strip()
        if s.endswith(".NS") or s.endswith(".BO"):
            s = s[:-3]
        return s

    @classmethod
    def get_config(cls, symbol: str, current_price: float = 1000.0) -> Dict[str, Any]:
        clean = cls.clean_symbol(symbol)
        if clean in cls.FNO_CONFIG:
            return cls.FNO_CONFIG[clean]
        
        # Heuristic configuration for any stock not explicitly listed
        strike_step = 50.0
        if current_price < 100:
            strike_step = 1.0
        elif current_price < 250:
            strike_step = 2.5
        elif current_price < 500:
            strike_step = 5.0
        elif current_price < 1000:
            strike_step = 10.0
        elif current_price < 2500:
            strike_step = 20.0
        elif current_price < 5000:
            strike_step = 50.0
        else:
            strike_step = 100.0

        lot_size = max(25, int(round(500000.0 / max(1.0, current_price))))

        return {
            "lot_size": lot_size,
            "strike_step": strike_step,
            "base_iv": 0.22,
            "name": f"{clean} Equity Derivatives",
            "type": "STOCK"
        }

    @classmethod
    def get_expiry_dates(cls, base_date: Optional[datetime] = None) -> List[str]:
        """
        Calculates upcoming Thursday expiry dates for NSE.
        Returns 4 weekly expiries and next 2 monthly expiries.
        """
        now = base_date or datetime.now()
        expiries = []

        # Find upcoming Thursdays
        curr = now.date()
        days_ahead = (3 - curr.weekday() + 7) % 7
        if days_ahead == 0 and now.hour >= 16:
            # If today is Thursday after 4 PM, move to next week
            days_ahead = 7

        first_thursday = curr + timedelta(days=days_ahead)
        for i in range(5):
            thurs = first_thursday + timedelta(weeks=i)
            expiries.append(thurs.strftime("%d-%b-%Y").upper())

        # Add last Thursday of next month
        next_month = curr.replace(day=28) + timedelta(days=4)
        last_thurs_next = next_month.replace(day=1) - timedelta(days=1)
        while last_thurs_next.weekday() != 3:
            last_thurs_next -= timedelta(days=1)
        exp_next = last_thurs_next.strftime("%d-%b-%Y").upper()
        if exp_next not in expiries:
            expiries.append(exp_next)

        return expiries

    @classmethod
    def black_scholes_price(
        cls,
        spot: float,
        strike: float,
        time_to_expiry_years: float,
        volatility: float,
        rate: float = 0.07,
        is_call: bool = True
    ) -> Tuple[float, float, float, float, float]:
        """
        Computes Black-Scholes Option Price and Greeks: (Price, Delta, Gamma, Theta, Vega).
        """
        t = max(0.001, time_to_expiry_years)
        vol = max(0.05, volatility)
        s = max(0.01, spot)
        k = max(0.01, strike)

        d1 = (math.log(s / k) + (rate + 0.5 * vol * vol) * t) / (vol * math.sqrt(t))
        d2 = d1 - vol * math.sqrt(t)

        df = math.exp(-rate * t)

        if is_call:
            price = max(0.05, s * norm_cdf(d1) - k * df * norm_cdf(d2))
            delta = norm_cdf(d1)
        else:
            price = max(0.05, k * df * norm_cdf(-d2) - s * norm_cdf(-d1))
            delta = norm_cdf(d1) - 1.0

        gamma = norm_pdf(d1) / (s * vol * math.sqrt(t))
        vega = s * math.sqrt(t) * norm_pdf(d1) / 100.0  # per 1% IV change
        theta = (- (s * norm_pdf(d1) * vol) / (2.0 * math.sqrt(t))
                 - (rate * k * df * (norm_cdf(d2) if is_call else norm_cdf(-d2)))) / 365.0

        return round(price, 2), round(delta, 3), round(gamma, 5), round(theta, 2), round(vega, 2)

    @classmethod
    def generate_option_chain(
        cls,
        symbol: str,
        spot_price: float,
        expiry: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Constructs a complete institutional Option Chain table with strike ladder,
        open interest buildup, PCR, Max Pain, and Greeks.
        """
        clean = cls.clean_symbol(symbol)
        cfg = cls.get_config(clean, spot_price)
        expiries = cls.get_expiry_dates()
        selected_expiry = expiry if (expiry and expiry in expiries) else expiries[0]

        strike_step = cfg["strike_step"]
        lot_size = cfg["lot_size"]
        base_iv = cfg["base_iv"]

        # Time to expiry in years
        try:
            exp_date = datetime.strptime(selected_expiry, "%d-%b-%Y")
            days_to_exp = max(1, (exp_date.date() - datetime.now().date()).days)
        except Exception:
            days_to_exp = 7
        t_years = days_to_exp / 365.0

        # Calculate ATM strike
        atm_strike = round(spot_price / strike_step) * strike_step

        # Build 15 strikes below and 15 strikes above ATM (total 31 strikes)
        strikes = [
            round(atm_strike + i * strike_step, 2)
            for i in range(-15, 16)
            if (atm_strike + i * strike_step) > 0
        ]

        chain_rows = []
        total_call_oi = 0
        total_put_oi = 0
        total_call_vol = 0
        total_put_vol = 0

        # Loss map for Max Pain
        loss_by_strike: Dict[float, float] = {k: 0.0 for k in strikes}

        for k in strikes:
            moneyness = (spot_price - k) / spot_price
            # Volatility smile skew
            call_iv = base_iv * (1.0 - 0.2 * moneyness + 0.5 * moneyness * moneyness)
            put_iv = base_iv * (1.0 + 0.3 * moneyness + 0.6 * moneyness * moneyness)

            # Option pricing & Greeks
            c_price, c_delta, c_gamma, c_theta, c_vega = cls.black_scholes_price(
                spot_price, k, t_years, call_iv, is_call=True
            )
            p_price, p_delta, p_gamma, p_theta, p_vega = cls.black_scholes_price(
                spot_price, k, t_years, put_iv, is_call=False
            )

            # Realistic OI distribution centered around ATM with resistance/support walls
            dist_factor = math.exp(-0.5 * (moneyness / 0.08) ** 2)
            round_number_boost = 1.6 if (k % (strike_step * 2) == 0) else 1.0

            # Calls have more OI above spot (resistance), Puts below spot (support)
            c_oi = int(round(dist_factor * 8500 * (1.2 if k >= spot_price else 0.6) * round_number_boost * lot_size))
            p_oi = int(round(dist_factor * 8200 * (1.2 if k <= spot_price else 0.6) * round_number_boost * lot_size))

            c_oi_change = int(round(c_oi * (0.05 if k >= spot_price else -0.04)))
            p_oi_change = int(round(p_oi * (0.06 if k <= spot_price else -0.03)))

            c_vol = int(round(c_oi * 0.45))
            p_vol = int(round(p_oi * 0.40))

            total_call_oi += c_oi
            total_put_oi += p_oi
            total_call_vol += c_vol
            total_put_vol += p_vol

            # Accumulate payouts for Max Pain
            for exp_p in strikes:
                call_payout = max(0.0, exp_p - k) * c_oi
                put_payout = max(0.0, k - exp_p) * p_oi
                loss_by_strike[exp_p] += (call_payout + put_payout)

            is_atm = abs(k - atm_strike) < (strike_step / 2.0)

            chain_rows.append({
                "strike": k,
                "is_atm": is_atm,
                "call": {
                    "contract": f"{clean}{selected_expiry[:5]}{k}CE",
                    "ltp": c_price,
                    "change": round(c_price * 0.035, 2),
                    "change_pct": 3.5,
                    "volume": c_vol,
                    "oi": c_oi,
                    "oi_change": c_oi_change,
                    "iv": round(call_iv * 100, 1),
                    "delta": c_delta,
                    "theta": c_theta,
                    "gamma": c_gamma,
                    "vega": c_vega
                },
                "put": {
                    "contract": f"{clean}{selected_expiry[:5]}{k}PE",
                    "ltp": p_price,
                    "change": round(-p_price * 0.028, 2),
                    "change_pct": -2.8,
                    "volume": p_vol,
                    "oi": p_oi,
                    "oi_change": p_oi_change,
                    "iv": round(put_iv * 100, 1),
                    "delta": p_delta,
                    "theta": p_theta,
                    "gamma": p_gamma,
                    "vega": p_vega
                }
            })

        # Max Pain Calculation (Strike where buyers lose the most / sellers pay the least)
        max_pain_strike = min(loss_by_strike.keys(), key=lambda s: loss_by_strike[s]) if loss_by_strike else atm_strike

        # Put-Call Ratio
        pcr = round(total_put_oi / max(1, total_call_oi), 2)
        pcr_sentiment = "BULLISH" if pcr > 1.15 else ("BEARISH" if pcr < 0.85 else "NEUTRAL")

        # Futures Contracts (Current, Next, Far Month)
        futures = []
        for idx, exp_label in enumerate(expiries[:3]):
            exp_days = (datetime.strptime(exp_label, "%d-%b-%Y").date() - datetime.now().date()).days
            prem = round(spot_price * 0.07 * (exp_days / 365.0), 2)
            fut_price = round(spot_price + prem, 2)
            fut_oi = int(round(total_call_oi * (0.8 - idx * 0.25)))
            futures.append({
                "expiry": exp_label,
                "contract": f"{clean}-{exp_label[:5]}-FUT",
                "price": fut_price,
                "premium": prem,
                "oi": fut_oi,
                "lot_size": lot_size
            })

        return {
            "symbol": clean,
            "name": cfg["name"],
            "type": cfg["type"],
            "spot_price": round(spot_price, 2),
            "atm_strike": atm_strike,
            "selected_expiry": selected_expiry,
            "available_expiries": expiries,
            "lot_size": lot_size,
            "strike_step": strike_step,
            "total_call_oi": total_call_oi,
            "total_put_oi": total_put_oi,
            "pcr": pcr,
            "pcr_sentiment": pcr_sentiment,
            "max_pain": max_pain_strike,
            "futures": futures,
            "chain": chain_rows
        }
