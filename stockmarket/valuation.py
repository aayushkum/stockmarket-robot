from dataclasses import dataclass, asdict
import math
from .data import Snapshot


@dataclass
class ValuationResult:
    model: str
    fair_value: float | None
    note: str

    def to_dict(self):
        return asdict(self)


@dataclass
class ValuationSummary:
    estimates: list[ValuationResult]
    fair_value: float | None
    upside: float | None

    def to_dict(self):
        return {
            "estimates": [e.to_dict() for e in self.estimates],
            "fair_value": self.fair_value,
            "upside": self.upside,
        }


def _safe_positive(value):
    if value is None:
        return None

    try:
        value = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(value) or value <= 0:
        return None

    return value


def _safe_growth(value, default=None):
    if value is None:
        return default

    try:
        value = float(value)
    except (TypeError, ValueError):
        return default

    if not math.isfinite(value):
        return default

    return value


def _clamp(value, low, high):
    return max(low, min(high, value))


def dcf_value(
    fcf,
    growth,
    discount_rate=0.09,
    terminal_growth=0.025,
    years=5,
):
    fcf = _safe_positive(fcf)

    if fcf is None:
        return None

    growth = _safe_growth(growth, 0.0)

    # Do not allow unrealistic perpetual/high-growth assumptions.
    growth = _clamp(growth, -0.05, 0.10)

    discount_rate = _clamp(float(discount_rate), 0.08, 0.15)
    terminal_growth = _clamp(float(terminal_growth), 0.00, 0.03)

    if terminal_growth >= discount_rate:
        terminal_growth = discount_rate - 0.01

    value = 0.0

    for year in range(1, years + 1):
        projected_fcf = fcf * ((1.0 + growth) ** year)
        value += projected_fcf / ((1.0 + discount_rate) ** year)

    terminal_fcf = fcf * ((1.0 + growth) ** years)
    terminal_value = (
        terminal_fcf * (1.0 + terminal_growth)
        / (discount_rate - terminal_growth)
    )

    value += terminal_value / ((1.0 + discount_rate) ** years)

    return value


def summarize(snapshot: Snapshot) -> ValuationSummary:
    """
    Produce a valuation summary.
    """

    estimates: list[ValuationResult] = []

    price = _safe_positive(snapshot.price)

    # ------------------------------------------------------------
    # 1. PRIMARY MODEL: DCF
    # ------------------------------------------------------------

    fcf = _safe_positive(snapshot.free_cash_flow)

    growth = _safe_growth(
        snapshot.earnings_growth,
        _safe_growth(snapshot.revenue_growth, 0.0),
    )

    dcf = None

    if fcf is not None:
        # Conservative discount-rate proxy.
        beta = _safe_growth(snapshot.beta, 1.0)

        if beta is None:
            beta = 1.0

        discount_rate = 0.09 + max(0.0, beta - 1.0) * 0.02
        discount_rate = _clamp(discount_rate, 0.08, 0.14)

        dcf = dcf_value(
            fcf=fcf,
            growth=growth,
            discount_rate=discount_rate,
            terminal_growth=0.025,
            years=5,
        )

        if dcf is not None:
            estimates.append(
                ValuationResult(
                    "DCF",
                    dcf,
                    (
                        f"Primary intrinsic-value estimate; "
                        f"growth={growth:.1%}, "
                        f"discount_rate={discount_rate:.1%}"
                    ),
                )
            )
    else:
        estimates.append(
            ValuationResult(
                "DCF",
                None,
                "Unavailable: no positive free cash flow.",
            )
        )

    # ------------------------------------------------------------
    # 2. SECONDARY MODEL: FORWARD EPS × REASONABLE P/E
    # ------------------------------------------------------------

    forward_eps = _safe_positive(snapshot.forward_eps)

    if forward_eps is not None:
        growth_for_multiple = _safe_growth(growth, 0.0)

        # Base multiple of 15, with moderate growth adjustment.
        pe = 15.0 + _clamp(growth_for_multiple, -0.10, 0.20) * 25.0
        pe = _clamp(pe, 10.0, 22.0)

        eps_value = forward_eps * pe

        estimates.append(
            ValuationResult(
                "Forward EPS × P/E",
                eps_value,
                f"Secondary relative-valuation check; P/E={pe:.1f}",
            )
        )
    else:
        estimates.append(
            ValuationResult(
                "Forward EPS × P/E",
                None,
                "Unavailable: no positive forward EPS.",
            )
        )

    # ------------------------------------------------------------
    # 3. SECONDARY MODEL: FCF × MULTIPLE
    # ------------------------------------------------------------

    if fcf is not None:
        fcf_growth = _safe_growth(growth, 0.0)

        fcf_multiple = 15.0 + _clamp(fcf_growth, -0.10, 0.20) * 20.0
        fcf_multiple = _clamp(fcf_multiple, 8.0, 20.0)

        fcf_value = fcf * fcf_multiple

        estimates.append(
            ValuationResult(
                "FCF × Multiple",
                fcf_value,
                (
                    "Secondary cash-flow multiple check; "
                    f"multiple={fcf_multiple:.1f}"
                ),
            )
        )
    else:
        estimates.append(
            ValuationResult(
                "FCF × Multiple",
                None,
                "Unavailable: no positive free cash flow.",
            )
        )

    # ------------------------------------------------------------
    # 4. HISTORICAL EPS CHECK
    # ------------------------------------------------------------

    eps = _safe_positive(snapshot.eps)

    if eps is not None:
        historical_value = eps * 18.0

        estimates.append(
            ValuationResult(
                "Historical EPS × 18",
                historical_value,
                "Secondary historical-multiple sanity check.",
            )
        )
    else:
        estimates.append(
            ValuationResult(
                "Historical EPS × 18",
                None,
                "Unavailable: no positive EPS.",
            )
        )

    # ------------------------------------------------------------
    # FINAL FAIR VALUE
    # ------------------------------------------------------------

    valid = [
        estimate.fair_value
        for estimate in estimates
        if estimate.fair_value is not None
        and math.isfinite(estimate.fair_value)
        and estimate.fair_value > 0
    ]

    if not valid:
        return ValuationSummary(
            estimates=estimates,
            fair_value=None,
            upside=None,
        )

    primary = dcf

    # If DCF exists, it gets 60% of the final estimate.
    # Relative methods collectively receive 40%.
    if primary is not None:
        secondary = [
            x
            for x in valid
            if not math.isclose(x, primary, rel_tol=1e-12, abs_tol=1e-12)
        ]

        if secondary:
            secondary_median = sorted(secondary)[len(secondary) // 2]
            fair_value = primary * 0.60 + secondary_median * 0.40
        else:
            fair_value = primary
    else:
        # If DCF isn't possible, fall back to the median of the
        # relative valuation methods rather than an arbitrary average.
        sorted_values = sorted(valid)
        fair_value = sorted_values[len(sorted_values) // 2]

    upside = None

    if price is not None and price > 0:
        upside = fair_value / price - 1.0

    return ValuationSummary(
        estimates=estimates,
        fair_value=fair_value,
        upside=upside,
    )
