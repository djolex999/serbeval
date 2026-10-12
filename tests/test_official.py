from serbeval.official import lm_task_name, official_status


def row(item_id: str, task: str, category: str = "c", **extra: object) -> dict[str, object]:
    return {"id": item_id, "task": task, "category": category, "verified": False, **extra}


def test_human_verified_items_are_in_whatever_the_models_said() -> None:
    rows = [row("a", "srb_probe", verified=True)]
    assert official_status(rows, core={"a"}, disputed={"a"}) == {"a": "human"}


def test_core_items_the_strong_models_agree_on_enter_as_consensus() -> None:
    rows = [row("a", "srb_probe"), row("b", "srb_probe")]
    assert official_status(rows, core={"a", "b"}, disputed={"b"}) == {"a": "consensus"}


def test_items_outside_the_core_never_enter_unverified() -> None:
    # Mined and synthesised cloze candidates were never on a sheet; agreement alone is
    # not enough to admit them.
    assert official_status([row("m", "srb_grammar_cloze")], core=set(), disputed=set()) == {}


def test_correction_items_follow_their_source() -> None:
    rows = [
        row("src", "srb_pravopis", verified=True),
        row("c1", "srb_correction", source="derived:src"),
        row("c2", "srb_correction", source="derived:not-official"),
    ]
    status = official_status(rows, core=set(), disputed=set())
    assert status == {"src": "human", "c1": "derived"}


def test_lm_task_names_match_the_task_yamls() -> None:
    assert lm_task_name(row("x", "srb_probe", "aorist-imperfekat")) == "srb_probe_aorist_imperfekat"
    adj = row("x", "srb_pravopis", "slozeni-pridevi")
    assert lm_task_name(adj) == "srb_pravopis_slozeni_pridevi"
    assert lm_task_name(row("x", "srb_correction", "c-ć")) == "srb_correction_c_c"
    assert lm_task_name(row("x", "srb_grammar", "padezi")) == "srb_grammar"
