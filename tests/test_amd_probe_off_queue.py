"""Regression for AMD's slow pipeline-cache probe fallback, without game data.

Run: python3 -I -B tests/test_amd_probe_off_queue.py
Checks source contracts and models the queue's single-large-build rule.
"""
from pathlib import Path
import argparse


def select(queue, running, limit, probe_on, take=False):
    """Only a cache probe may bypass the large-build slot, while probes remain enabled."""
    chosen = next((j for j in queue if not (j["large"] and
                  (j["probed"] or not probe_on) and running >= limit)), None)
    if chosen is not None and take and chosen["large"] and not probe_on:
        chosen["probed"] = True
    return chosen


def check_model():
    a = {"large": True, "probed": False}
    b = {"large": True, "probed": False}
    small = {"large": False, "probed": False}
    assert select([a, b], 1, 1, False) is None  # old code incorrectly runs a probe
    assert select([a, small], 1, 1, False) is small
    assert select([a, small], 0, 1, False) is a
    assert a["probed"] is False  # a readiness poll must not consume the slot
    assert select([a], 0, 1, False, take=True) is a
    assert a["probed"] is True  # selected job skips its probe and holds the slot
    assert select([b], 1, 1, False) is None
    assert select([b], 1, 1, True) is b  # cache hits may bypass a busy build slot
    assert b["probed"] is False
    assert select([small], 1, 1, False) is small
    print("PASS: nine queue and fallback assertions")


def check_source(src):
    pick = src.split("static Job *low_pick(int take)", 1)[1].split("static void pipe_worker", 1)[0]
    assert "(j->probed || !probe_on) && large_running >= big_workers" in pick
    assert "if (j->large && !probe_on) j->probed = 1;" in pick
    assert "// P.lock protects this switch" in src
    worker = src.split("static void pipe_worker(void *arg)", 1)[1]
    disable = worker.split("if (dt > 10000)", 1)[1].split("if (!pipe && !j->slot)", 1)[0]
    lock = disable.index("plat_mutex_lock(&P.lock);")
    write = disable.index("probe_on = 0;")
    unlock = disable.index("plat_mutex_unlock(&P.lock);")
    assert lock < write < unlock
    print("PASS: source checks on queue selection and synchronized probe disable")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path,
                        default=Path(__file__).resolve().parents[1] / "runtime" / "vk_pipeline.c")
    args = parser.parse_args()
    check_model()
    check_source(args.source.read_text(encoding="utf-8"))
