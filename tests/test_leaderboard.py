import json

from pavebench.cli import main
from pavebench.leaderboard import instant_badge, render_leaderboard


def _summary(cases, passes, latency_class, tiers):
    return {
        "cases": cases,
        "passes": passes,
        "meanIou": 0.9,
        "medianAreaDeltaPct": 0.05,
        "p90AreaDeltaPct": 0.12,
        "meanCutoutRecovery": 0.8,
        "p95LatencyMs": 5000 if latency_class == "INSTANT" else 90000,
        "latencyClass": latency_class,
        "meanCostUsd": 0.02,
        "byGsdTier": {tier: {} for tier in tiers},
    }


def test_instant_badge_requires_all_gates():
    good = _summary(cases=25, passes=24, latency_class="INSTANT", tiers=["<=8cm", "8-15cm", ">15cm"])
    earned, reasons = instant_badge(good, "full_auto")
    assert earned and reasons == []


def test_instant_badge_blocks_human_in_loop_and_batch():
    slow = _summary(cases=25, passes=24, latency_class="BATCH", tiers=["<=8cm", ">15cm"])
    earned, reasons = instant_badge(slow, "human_in_loop")
    assert not earned
    assert any("automation" in r for r in reasons)
    assert any("latencyClass" in r for r in reasons)


def test_instant_badge_blocks_thin_or_single_tier_eval():
    thin = _summary(cases=3, passes=3, latency_class="INSTANT", tiers=["<=8cm"])
    earned, reasons = instant_badge(thin, "full_auto")
    assert not earned
    assert any("cases" in r for r in reasons)
    assert any("GSD tiers" in r for r in reasons)


def test_render_and_cli_leaderboard(tmp_path):
    score = tmp_path / "score.json"
    score.write_text(
        json.dumps({"summary": _summary(25, 24, "INSTANT", ["<=8cm", "8-15cm"])}),
        encoding="utf-8",
    )
    runs = tmp_path / "runs.jsonl"
    runs.write_text(
        json.dumps(
            {
                "system": "instant-student-v0",
                "track": "pure_segmentation",
                "automation": "full_auto",
                "scorePath": "score.json",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "leaderboard.md"
    assert main(["leaderboard", "--runs", str(runs), "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "instant-student-v0" in text
    assert "INSTANT" in text
    assert "Paved-area takeoff" in text
