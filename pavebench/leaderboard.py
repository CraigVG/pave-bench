from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# INSTANT badge gates. A system earns the badge only when it is fully automated,
# lands in the INSTANT latency class, and clears the accuracy floor across enough
# reviewed-gold cases spanning multiple GSD tiers. See docs/proving-instant-takeoff.md.
INSTANT_MIN_CASES = 20
INSTANT_MIN_GSD_TIERS = 2
INSTANT_MIN_PASS_RATE = 0.90


def load_runs(path: str | Path) -> list[dict[str, Any]]:
    manifest_path = Path(path)
    base_dir = manifest_path.parent
    runs: list[dict[str, Any]] = []
    for line_number, line in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        score_value = row.get("scorePath")
        if not score_value:
            raise ValueError(f"Run row {line_number} is missing scorePath")
        score_path = Path(score_value)
        if not score_path.is_absolute():
            score_path = base_dir / score_path
        row["_report"] = json.loads(score_path.read_text(encoding="utf-8"))
        runs.append(row)
    return runs


def _gsd_tier_span(summary: dict[str, Any]) -> int:
    tiers = summary.get("byGsdTier", {})
    return sum(1 for tier in tiers if tier != "unknown")


def instant_badge(summary: dict[str, Any], automation: str) -> tuple[bool, list[str]]:
    """Return (earned, unmet_reasons) for the INSTANT badge."""

    reasons: list[str] = []
    if automation != "full_auto":
        reasons.append(f"automation={automation} (needs full_auto)")
    if summary.get("latencyClass") != "INSTANT":
        reasons.append(f"latencyClass={summary.get('latencyClass')} (needs INSTANT)")
    cases = int(summary.get("cases", 0))
    if cases < INSTANT_MIN_CASES:
        reasons.append(f"{cases} cases (needs >= {INSTANT_MIN_CASES})")
    passes = int(summary.get("passes", 0))
    pass_rate = passes / cases if cases else 0.0
    if pass_rate < INSTANT_MIN_PASS_RATE:
        reasons.append(f"pass rate {pass_rate:.0%} (needs >= {INSTANT_MIN_PASS_RATE:.0%})")
    tiers = _gsd_tier_span(summary)
    if tiers < INSTANT_MIN_GSD_TIERS:
        reasons.append(f"{tiers} GSD tiers (needs >= {INSTANT_MIN_GSD_TIERS})")
    return (not reasons, reasons)


def _pct(value: float | None) -> str:
    return "-" if value is None else f"{value:.1%}"


def _num(value: float | None, suffix: str = "") -> str:
    return "-" if value is None else f"{value:g}{suffix}"


def _ms(value: float | None) -> str:
    return "-" if value is None else f"{value / 1000:g}s"


def _usd(value: float | None) -> str:
    return "-" if value is None else f"${value:.3f}"


def render_leaderboard(runs: list[dict[str, Any]]) -> str:
    lines: list[str] = ["# PaveBench Leaderboard", ""]
    lines.append(
        "Latency class: **INSTANT** = p95 wall-clock <= 10 s, **FAST** <= 60 s, "
        "**BATCH** > 60 s. The INSTANT badge additionally requires full automation "
        f"(no human in the loop), pass rate >= {INSTANT_MIN_PASS_RATE:.0%} over "
        f">= {INSTANT_MIN_CASES} reviewed-gold cases spanning >= {INSTANT_MIN_GSD_TIERS} "
        "GSD tiers. See docs/proving-instant-takeoff.md."
    )
    lines.append("")

    area_runs = [run for run in runs if run["_report"].get("summary", {}).get("cases")]
    if not area_runs:
        lines.append("_No area-task submissions yet._")
    else:
        lines.append("## Paved-area takeoff")
        lines.append("")
        header = (
            "| System | Track | Automation | Cases | Pass | mean IoU | median areaΔ | "
            "p90 areaΔ | cutout recov. | p95 latency | Latency class | mean cost | INSTANT |"
        )
        lines.append(header)
        lines.append("|" + "---|" * 13)
        for run in area_runs:
            summary = run["_report"]["summary"]
            earned, _ = instant_badge(summary, run.get("automation", "unknown"))
            cases = int(summary.get("cases", 0))
            passes = int(summary.get("passes", 0))
            lines.append(
                "| {system} | {track} | {automation} | {cases} | {passrate} | {iou:.3f} | "
                "{med} | {p90} | {recov} | {lat} | {lclass} | {cost} | {badge} |".format(
                    system=run.get("system", "?"),
                    track=run.get("track", "-"),
                    automation=run.get("automation", "-"),
                    cases=cases,
                    passrate=f"{passes}/{cases}",
                    iou=float(summary.get("meanIou", 0.0)),
                    med=_pct(summary.get("medianAreaDeltaPct")),
                    p90=_pct(summary.get("p90AreaDeltaPct")),
                    recov=_pct(summary.get("meanCutoutRecovery")),
                    lat=_ms(summary.get("p95LatencyMs")),
                    lclass=summary.get("latencyClass", "unknown"),
                    cost=_usd(summary.get("meanCostUsd")),
                    badge="YES" if earned else "-",
                )
            )
        lines.append("")

    stall_runs = [run for run in runs if run["_report"].get("stallSummary", {}).get("cases")]
    if stall_runs:
        lines.append("## Stall counting")
        lines.append("")
        lines.append(
            "| System | Automation | Cases | Pass | median |countΔ| | p90 |countΔ| | "
            "precision | recall | median loc. err | p95 latency | Latency class | mean cost |"
        )
        lines.append("|" + "---|" * 14)
        for run in stall_runs:
            summary = run["_report"]["stallSummary"]
            cases = int(summary.get("cases", 0))
            passes = int(summary.get("passes", 0))
            lines.append(
                "| {system} | {automation} | {cases} | {passrate} | {med} | {p90} | "
                "{prec} | {rec} | {loc} | {lat} | {lclass} | {cost} |".format(
                    system=run.get("system", "?"),
                    automation=run.get("automation", "-"),
                    cases=cases,
                    passrate=f"{passes}/{cases}",
                    med=_pct(_frac(summary.get("medianAbsCountErrorPct"))),
                    p90=_pct(_frac(summary.get("p90AbsCountErrorPct"))),
                    prec=_pct(summary.get("meanPrecision")),
                    rec=_pct(summary.get("meanRecall")),
                    loc=_num(summary.get("medianLocationErrorM"), suffix=" m") if summary.get("medianLocationErrorM") is not None else "-",
                    lat=_ms(summary.get("p95LatencyMs")),
                    lclass=summary.get("latencyClass", "unknown"),
                    cost=_usd(summary.get("meanCostUsd")),
                )
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _frac(pct: float | None) -> float | None:
    return None if pct is None else pct / 100.0


def write_leaderboard(runs_path: str | Path, out_path: str | Path) -> None:
    runs = load_runs(runs_path)
    Path(out_path).write_text(render_leaderboard(runs), encoding="utf-8")
