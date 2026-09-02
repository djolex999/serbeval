from serbeval.conllu import Token, parse_conllu

SAMPLE = """# sent_id = set-s1
# text = Proces privatizacije pod lupom
1\tProces\tproces\tNOUN\tNcmsn\tCase=Nom|Gender=Masc|Number=Sing\t4\tnsubj\t_\t_
2\tprivatizacije\tprivatizacija\tNOUN\tNcfsg\tCase=Gen|Gender=Fem|Number=Sing\t1\tnmod\t_\t_
3\tpod\tpod\tADP\tSi\tCase=Ins\t4\tcase\t_\t_
4\tlupom\tlupa\tNOUN\tNcfsi\tCase=Ins|Gender=Fem|Number=Sing\t0\troot\t_\tSpaceAfter=No

# sent_id = set-s2
# text = Kosovo analizira procese.
1\tKosovo\tKosovo\tPROPN\tNpnsn\tCase=Nom|Gender=Neut|Number=Sing\t2\tnsubj\t_\t_
2\tanalizira\tanalizirati\tVERB\tVmr3s\tTense=Pres\t0\troot\t_\t_
3\tprocese\tproces\tNOUN\tNcmpa\tCase=Acc|Gender=Masc|Number=Plur\t2\tobj\t_\tSpaceAfter=No
4\t.\t.\tPUNCT\tZ\t_\t3\tpunct\t_\t_
"""


def test_parses_every_sentence() -> None:
    assert len(parse_conllu(SAMPLE)) == 2


def test_keeps_sentence_id_and_text() -> None:
    first = parse_conllu(SAMPLE)[0]
    assert first.sent_id == "set-s1"
    assert first.text == "Proces privatizacije pod lupom"


def test_parses_token_fields() -> None:
    token = parse_conllu(SAMPLE)[0].tokens[3]
    assert token.id == 4
    assert token.form == "lupom"
    assert token.lemma == "lupa"
    assert token.upos == "NOUN"
    assert token.head == 0
    assert token.deprel == "root"


def test_parses_features_into_a_dict() -> None:
    token = parse_conllu(SAMPLE)[0].tokens[3]
    assert token.feats["Case"] == "Ins"
    assert token.feats["Number"] == "Sing"


def test_empty_features_become_an_empty_dict() -> None:
    token = parse_conllu(SAMPLE)[1].tokens[3]
    assert token.feats == {}


def test_tracks_no_space_after() -> None:
    tokens = parse_conllu(SAMPLE)[1].tokens
    assert tokens[2].space_after is False   # procese, then "." with no space
    assert tokens[0].space_after is True


def test_skips_multiword_and_empty_node_lines() -> None:
    # UD uses "1-2" for multiword tokens and "1.1" for empty nodes; neither is a
    # real token and both would corrupt id-based head lookups.
    text = (
        "# sent_id = x\n"
        "# text = test\n"
        "1-2\tdo\t_\t_\t_\t_\t_\t_\t_\t_\n"
        "1\tdo\tdo\tADP\tSg\tCase=Gen\t2\tcase\t_\t_\n"
        "2\tkraja\tkraj\tNOUN\tNcmsg\tCase=Gen\t0\troot\t_\t_\n"
        "2.1\t_\t_\t_\t_\t_\t_\t_\t_\t_\n"
    )
    tokens = parse_conllu(text)[0].tokens
    assert [t.id for t in tokens] == [1, 2]


def test_render_replaces_one_token_with_the_blank() -> None:
    sentence = parse_conllu(SAMPLE)[0]
    assert sentence.render_with_blank(4) == "Proces privatizacije pod ____"


def test_render_respects_no_space_before_punctuation() -> None:
    sentence = parse_conllu(SAMPLE)[1]
    assert sentence.render_with_blank(3) == "Kosovo analizira ____."


def test_token_is_a_frozen_record() -> None:
    token = parse_conllu(SAMPLE)[0].tokens[0]
    assert isinstance(token, Token)
