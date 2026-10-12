"""The official set: the items a published number is allowed to rest on.

An item enters with one of three statuses, recorded in data/official/MANIFEST.json:

    human      verified by the maintainer (blind baseline, or the disputed-item sheet)
    consensus  on the verification core list, and fewer than two of the four strongest
               models disagreed with its gold; NOT a human verification, and labelled so
    derived    a srb_correction item whose source item is itself official

Items off the core list never enter unverified: mined and synthesised cloze candidates were
never put in front of a human or the consensus check, so model agreement alone does not
admit them. Unsure (`?`) items stay unverified AND disputed, so they fall out.
"""

from collections.abc import Iterable, Mapping
from typing import Literal

Status = Literal["human", "consensus", "derived"]

# Item `task` values whose lm-eval tasks are split per category.
_SPLIT_BY_CATEGORY = {"srb_probe", "srb_pravopis", "srb_correction"}
_CATEGORY_SLUG = {"c-ć": "c_c"}


def lm_task_name(row: Mapping[str, object]) -> str:
    task = str(row["task"])
    if task not in _SPLIT_BY_CATEGORY:
        return task
    category = str(row["category"])
    return f"{task}_{_CATEGORY_SLUG.get(category, category.replace('-', '_'))}"


def official_status(
    rows: Iterable[Mapping[str, object]], *, core: set[str], disputed: set[str]
) -> dict[str, Status]:
    rows = list(rows)
    status: dict[str, Status] = {}
    for row in rows:
        item_id = str(row["id"])
        if row.get("task") == "srb_correction":
            continue
        if row.get("verified"):
            status[item_id] = "human"
        elif item_id in core and item_id not in disputed:
            status[item_id] = "consensus"
    for row in rows:
        if row.get("task") != "srb_correction":
            continue
        source = str(row.get("source", ""))
        if source.startswith("derived:") and source.split(":", 1)[1] in status:
            status[str(row["id"])] = "derived"
    return status
