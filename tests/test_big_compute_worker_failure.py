"""Source-level regression for big compute worker failure handling (no game/GPU).

The worker runs expensive compute compilation off the replay thread. An unsuccessful
compile or a failed pipeline-table allocation must never set its state to ready:
otherwise a later dispatch compiles the same giant shader synchronously.
"""
from pathlib import Path
import re

source = (Path(__file__).resolve().parents[1] / "runtime/vk_pipeline.c").read_text(encoding="utf-8")
worker = source.split("static void big_cs_worker(", 1)[1].split("int vk_pipeline_compute_ready(", 1)[0]
ready = source.split("int vk_pipeline_compute_ready(", 1)[1].split("VkPipeline vk_pipeline_compute(", 1)[0]

# Guards against removing the production-state distinction. This is a static
# source contract, not a Vulkan test or a proof of shader correctness.
assert re.search(r"if\s*\(pipe_add\(&k,[^;]+\)\)\s*\{", worker, re.S), "pipe_add failure unchecked"
assert "published = 1;" in worker, "no explicit published state"
assert re.search(r"done,\s*published\s*\?\s*1\s*:\s*-1", worker), "worker marks failures ready"
assert re.search(r"done,\s*__ATOMIC_ACQUIRE\)\s*>\s*0", ready), "replay accepts failed worker as ready"

# Simple failure-injection truth table (the state protocol, not actual Vulkan).
def status(compiled, present, inserted):
    published = compiled and (present or inserted)
    return 1 if published else -1

for compiled, present, inserted, expected in (
    (False, False, False, -1), # shader compile failed
    (True, False, False, -1),  # insertion failed (e.g. calloc)
    (True, False, True, 1),    # built and inserted
    (True, True, False, 1),    # another worker already inserted
):
    actual = status(compiled, present, inserted)
    assert actual == expected
    assert (actual > 0) == (expected == 1)
print("big compute worker failure protocol: 4 synthetic cases + source contract passed")
