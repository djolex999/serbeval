from serbeval.conllu import parse_conllu
from serbeval.mine import mine_cloze_items


def corpus(*sentences: str, filler: int = 25) -> list:
    """Real sentences plus filler.

    The filler clears the miner's min_count threshold for "zbog" and is itself minable
    (6 tokens, distinct noun lemma per sentence), so `limit` has something to cap.
    """
    filler_block = "".join(
        f"# sent_id = f{i}\n# text = f\n"
        f"1\tRadnici{i}\tradnik{i}\tNOUN\tNcmpn\tCase=Nom|Gender=Masc|Number=Plur\t3\tnsubj\t_\t_\n"
        f"2\tsu\tbiti\tAUX\tVar3p\tTense=Pres\t3\taux\t_\t_\n"
        f"3\tprotestovali\tprotestovati\tVERB\tVmp-pm\tTense=Past\t0\troot\t_\t_\n"
        f"4\tzbog\tzbog\tADP\tSg\tCase=Gen\t5\tcase\t_\t_\n"
        f"5\tplate{i}\tplata{i}\tNOUN\tNcfsg\tCase=Gen|Gender=Fem|Number=Sing\t3\tobl\t_\tSpaceAfter=No\n"
        f"6\t.\t.\tPUNCT\tZ\t_\t3\tpunct\t_\t_\n\n"
        for i in range(filler)
    )
    return parse_conllu(filler_block + "\n".join(sentences))


PURE = (
    "# sent_id = s1\n# text = Otkazali su put zbog nevremena.\n"
    "1\tOtkazali\totkazati\tVERB\tVmp-pm\tTense=Past\t0\troot\t_\t_\n"
    "2\tsu\tbiti\tAUX\tVar3p\tTense=Pres\t1\taux\t_\t_\n"
    "3\tput\tput\tNOUN\tNcmsan\tCase=Acc|Gender=Masc|Number=Sing\t1\tobj\t_\t_\n"
    "4\tzbog\tzbog\tADP\tSg\tCase=Gen\t5\tcase\t_\t_\n"
    "5\tnevremena\tnevreme\tNOUN\tNcnsg\tCase=Gen|Gender=Neut|Number=Sing\t1\tobl\t_\tSpaceAfter=No\n"
    "6\t.\t.\tPUNCT\tZ\t_\t1\tpunct\t_\t_\n"
)


def test_mines_an_item_from_a_pure_preposition() -> None:
    items = mine_cloze_items(corpus(PURE))
    mined = [i for i in items if i.answers == ["nevremena"]]
    assert len(mined) == 1
    assert mined[0].cue == "nevreme, jednina"
    assert "____" in mined[0].question
    assert "nevremena" not in mined[0].question


def test_mined_item_carries_share_alike_license_and_source() -> None:
    item = next(i for i in mine_cloze_items(corpus(PURE)) if i.answers == ["nevremena"])
    # CC BY-SA is viral: items derived from the treebank cannot claim plain CC-BY.
    assert item.license == "CC-BY-SA-4.0"
    assert item.source == "ud-serbian-set"
    assert item.verified is False


def test_explanation_names_the_preposition_and_the_case() -> None:
    item = next(i for i in mine_cloze_items(corpus(PURE)) if i.answers == ["nevremena"])
    assert "zbog" in item.explanation
    assert "genitiv" in item.explanation


def test_skips_ambiguous_prepositions() -> None:
    # "u" governs Loc or Acc depending on the verb, so the preposition alone does not
    # determine the answer.
    ambiguous = (
        "# sent_id = s2\n# text = Sedeli smo u bašti.\n"
        "1\tSedeli\tsedeti\tVERB\tVmp-pm\tTense=Past\t0\troot\t_\t_\n"
        "2\tsmo\tbiti\tAUX\tVar1p\tTense=Pres\t1\taux\t_\t_\n"
        "3\tu\tu\tADP\tSl\tCase=Loc\t4\tcase\t_\t_\n"
        "4\tbašti\tbašta\tNOUN\tNcfsl\tCase=Loc|Gender=Fem|Number=Sing\t1\tobl\t_\t_\n"
    )
    acc = ambiguous.replace("Case=Loc\t4", "Case=Acc\t4").replace(
        "Case=Loc|Gender=Fem", "Case=Acc|Gender=Fem"
    ).replace("s2", "s3").replace("bašti", "baštu")
    items = mine_cloze_items(parse_conllu("\n".join([ambiguous, acc] * 15)))
    assert all(i.cue != "bašta" for i in items)


def test_skips_proper_nouns() -> None:
    propn = PURE.replace("nevremena\tnevreme\tNOUN", "Kosova\tKosovo\tPROPN")
    assert not [i for i in mine_cloze_items(corpus(propn)) if i.cue == "Kosovo"]


def test_skips_when_the_answer_equals_the_cue() -> None:
    # Form identical to the lemma makes the item trivial: the cue IS the answer.
    same = PURE.replace(
        "5\tnevremena\tnevreme\tNOUN\tNcnsg", "5\tnevreme\tnevreme\tNOUN\tNcnsg"
    )
    assert not [i for i in mine_cloze_items(corpus(same)) if i.cue == "nevreme"]


def test_skips_when_the_answer_form_appears_elsewhere_in_the_sentence() -> None:
    leaky = PURE.replace(
        "3\tput\tput\tNOUN\tNcmsan\tCase=Acc|Gender=Masc|Number=Sing\t1\tobj\t_\t_\n",
        "3\tnevremena\tnevreme\tNOUN\tNcnsg\tCase=Gen|Gender=Neut|Number=Sing\t1\tobj\t_\t_\n",
    )
    assert not [i for i in mine_cloze_items(corpus(leaky)) if i.cue == "nevreme"]


def test_skips_a_noun_that_has_an_agreeing_modifier() -> None:
    # An agreeing adjective spells out case, number and gender, so the item would no
    # longer test whether the preposition's government is known.
    modified = PURE.replace(
        "6\t.\t.\tPUNCT\tZ\t_\t1\tpunct\t_\t_\n",
        "6\tjakog\tjak\tADJ\tAgpnsg\tCase=Gen|Gender=Neut|Number=Sing\t5\tamod\t_\t_\n",
    )
    assert not [i for i in mine_cloze_items(corpus(modified)) if i.cue == "nevreme"]


def test_the_cue_always_states_grammatical_number() -> None:
    # Genitive singular "želje" and genitive plural "želja" are both grammatical after
    # "zbog", so a bare lemma leaves the item with two defensible answers. Number is
    # stated on every item, singular included, rather than only on plurals.
    plural = (
        "# sent_id = p1\n# text = Inspektori su reagovali zbog pritužbi.\n"
        "1\tInspektori\tinspektor\tNOUN\tNcmpn\tCase=Nom|Gender=Masc|Number=Plur\t3\tnsubj\t_\t_\n"
        "2\tsu\tbiti\tAUX\tVar3p\tTense=Pres\t3\taux\t_\t_\n"
        "3\treagovali\treagovati\tVERB\tVmp-pm\tTense=Past\t0\troot\t_\t_\n"
        "4\tzbog\tzbog\tADP\tSg\tCase=Gen\t5\tcase\t_\t_\n"
        "5\tpritužbi\tpritužba\tNOUN\tNcfpg\tCase=Gen|Gender=Fem|Number=Plur\t3\tobl\t_\tSpaceAfter=No\n"
        "6\t.\t.\tPUNCT\tZ\t_\t3\tpunct\t_\t_\n"
    )
    items = mine_cloze_items(corpus(plural))
    assert "množina" in next(i for i in items if i.cue.startswith("pritužba")).cue
    assert "jednina" in next(i for i in items if i.cue.startswith("plata")).cue


def test_mined_items_pass_dataset_validation() -> None:
    from serbeval.data import validate_cloze_dataset

    assert validate_cloze_dataset(mine_cloze_items(corpus(PURE))) == []


def test_limit_caps_the_number_of_items() -> None:
    assert len(mine_cloze_items(corpus(PURE), limit=3)) == 3
