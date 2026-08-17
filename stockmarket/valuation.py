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
    low_value: float | None
    high_value: float | None

    def to_dict(self):
        return {
            "estimates": [e.to_dict() for e in self.estimates],
            "fair_value": self.fair_value,
            "upside": self.upside,
            "low_value": self.low_value,
            "high_value": self.high_value,
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
    """
    Convert growth to a usable finite number.
    """

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
    fcf_per_share,
    growth,
    discount_rate=0.09,
    terminal_growth=0.025,
    years=5,
):

    fcf_per_share = _safe_positive(fcf_per_share)

    if fcf_per_share is None:
        return None

    growth = _safe_growth(growth, 0.0)

    # Limit near-term growth to a reasonable range.
    growth = _clamp(growth, -0.05, 0.10)

    # Keep discount rates conservative.
    discount_rate = _clamp(
        float(discount_rate),
        0.08,
        0.15,
    )

    terminal_growth = _clamp(
        float(terminal_growth),
        0.00,
        0.03,
    )

    # Gordon Growth requires r > g.
    if terminal_growth >= discount_rate:
        terminal_growth = discount_rate - 0.01

    value = 0.0

    for year in range(1, years + 1):

        projected_fcf_per_share = (
            fcf_per_share
            * ((1.0 + growth) ** year)
        )

        discounted_fcf = (
            projected_fcf_per_share
            / ((1.0 + discount_rate) ** year)
        )

        value += discounted_fcf

    terminal_fcf_per_share = (
        fcf_per_share
        * ((1.0 + growth) ** years)
    )

    terminal_value_per_share = (
        terminal_fcf_per_share
        * (1.0 + terminal_growth)
        / (discount_rate - terminal_growth)
    )

    discounted_terminal_value = (
        terminal_value_per_share
        / ((1.0 + discount_rate) ** years)
    )

    value += discounted_terminal_value

    return value


def summarize(snapshot: Snapshot) -> ValuationSummary:
    """
    Calculate several per-share valuation estimates.

    Model hierarchy:

        DCF
         ↓
        Primary intrinsic-value estimate

        EPS × P/E
        FCF/share × multiple
        Historical EPS × multiple
         ↓
        Secondary sanity checks
    """

    estimates = []

    price = _safe_positive(snapshot.price)

    # ============================================================
    # 1. DCF — PRIMARY MODEL
    # ============================================================

    fcf_per_share = _safe_positive(
        snapshot.free_cash_flow_per_share
    )

    growth = _safe_growth(
        snapshot.earnings_growth,
        _safe_growth(
            snapshot.revenue_growth,
            0.0,
        ),
    )

    dcf = None

    if fcf_per_share is not None:

        beta = _safe_positive(snapshot.beta)

        if beta is None:
            beta = 1.0
        discount_rate = (
            0.09
            + max(0.0, beta - 1.0) * 0.02
        )

        discount_rate = _clamp(
            discount_rate,
            0.08,
            0.14,
        )

        dcf = dcf_value(
            fcf_per_share=fcf_per_share,
            growth=growth,
            discount_rate=discount_rate,
            terminal_growth=0.025,
            years=5,
        )

        if dcf is not None:

            estimates.append(
                ValuationResult(
                    model="DCF",
                    fair_value=dcf,
                    note=(
                        "Primary intrinsic-value estimate; "
                        f"FCF/share=${fcf_per_share:.2f}, "
                        f"growth={growth:.1%}, "
                        f"discount_rate={discount_rate:.1%}"
                    ),
                )
            )

    else:

        estimates.append(
            ValuationResult(
                model="DCF",
                fair_value=None,
                note=(
                    "Unavailable: positive "
                    "FCF/share could not be calculated."
                ),
            )
        )

    # ============================================================
    # 2. FORWARD EPS × P/E
    # ============================================================

    forward_eps = _safe_positive(
        snapshot.forward_eps
    )

    eps_value = None

    if forward_eps is not None:

        growth_for_multiple = _safe_growth(
            growth,
            0.0,
        )
        pe = (
            15.0
            + _clamp(
                growth_for_multiple,
                -0.10,
                0.20,
            ) * 25.0
        )

        pe = _clamp(
            pe,
            10.0,
            22.0,
        )

        eps_value = forward_eps * pe

        estimates.append(
            ValuationResult(
                model="Forward EPS × P/E",
                fair_value=eps_value,
                note=(
                    "Secondary relative-valuation check; "
                    f"forward EPS=${forward_eps:.2f}, "
                    f"P/E={pe:.1f}"
                ),
            )
        )

    else:

        estimates.append(
            ValuationResult(
                model="Forward EPS × P/E",
                fair_value=None,
                note=(
                    "Unavailable: no positive "
                    "forward EPS."
                ),
            )
        )

    # ============================================================
    # 3. FCF/SHARE × MULTIPLE
    # ============================================================

    fcf_multiple_value = None

    if fcf_per_share is not None:

        fcf_growth = _safe_growth(
            growth,
            0.0,
        )

        fcf_multiple = (
            15.0
            + _clamp(
                fcf_growth,
                -0.10,
                0.20,
            ) * 20.0
        )

        fcf_multiple = _clamp(
            fcf_multiple,
            8.0,
            20.0,
        )

        fcf_multiple_value = (
            fcf_per_share
            * fcf_multiple
        )

        estimates.append(
            ValuationResult(
                model="FCF/share × Multiple",
                fair_value=fcf_multiple_value,
                note=(
                    "Secondary cash-flow multiple check; "
                    f"FCF/share=${fcf_per_share:.2f}, "
                    f"multiple={fcf_multiple:.1f}"
                ),
            )
        )

    else:

        estimates.append(
            ValuationResult(
                model="FCF/share × Multiple",
                fair_value=None,
                note=(
                    "Unavailable: no positive "
                    "FCF/share."
                ),
            )
        )

    # ============================================================
    # 4. HISTORICAL EPS × 18
    # ============================================================

    eps = _safe_positive(
        snapshot.eps
    )

    historical_value = None

    if eps is not None:

        historical_value = eps * 18.0

        estimates.append(
            ValuationResult(
                model="Historical EPS × 18",
                fair_value=historical_value,
                note=(
                    "Secondary historical-multiple "
                    f"check; EPS=${eps:.2f}, P/E=18"
                ),
            )
        )

    else:

        estimates.append(
            ValuationResult(
                model="Historical EPS × 18",
                fair_value=None,
                note=(
                    "Unavailable: no positive EPS."
                ),
            )
        )

    # ============================================================
    # FINAL VALUE
    # ============================================================

    valid_estimates = [
        estimate
        for estimate in estimates
        if estimate.fair_value is not None
        and math.isfinite(estimate.fair_value)
        and estimate.fair_value > 0
    ]

    valid_values = [
        estimate.fair_value
        for estimate in valid_estimates
    ]

    if not valid_values:

        return ValuationSummary(
            estimates=estimates,
            fair_value=None,
            upside=None,
            low_value=None,
            high_value=None,
        )

    # ------------------------------------------------------------
    # VALUATION RANGE
    # ------------------------------------------------------------

    low_value = min(valid_values)
    high_value = max(valid_values)

    # ------------------------------------------------------------
    # FINAL FAIR VALUE
    # ------------------------------------------------------------

    if dcf is not None:

        secondary_values = [
            estimate.fair_value
            for estimate in valid_estimates
            if estimate.model != "DCF"
        ]

        if secondary_values:

            sorted_secondary = sorted(
                secondary_values
            )

            middle = len(sorted_secondary) // 2

            if len(sorted_secondary) % 2 == 0:
                secondary_median = (
                    sorted_secondary[middle - 1]
                    + sorted_secondary[middle]
                ) / 2.0
            else:
                secondary_median = (
                    sorted_secondary[middle]
                )
            fair_value = (
                dcf * 0.60
                + secondary_median * 0.40
            )

        else:

            fair_value = dcf

    else:
        sorted_values = sorted(valid_values)

        middle = len(sorted_values) // 2

        if len(sorted_values) % 2 == 0:

            fair_value = (
                sorted_values[middle - 1]
                + sorted_values[middle]
            ) / 2.0

        else:

            fair_value = sorted_values[middle]

    # ------------------------------------------------------------
    # UPSIDE
    # ------------------------------------------------------------

    upside = None

    if price is not None and price > 0:

        upside = (
            fair_value / price
            - 1.0
        )

    return ValuationSummary(
        estimates=estimates,
        fair_value=fair_value,
        upside=upside,
        low_value=low_value,
        high_value=high_value,
    )
