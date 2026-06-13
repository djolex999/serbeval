---
name: New item proposal
about: Propose a new benchmark item (or batch)
title: "[item] <task>/<category>: short description"
labels: ["new-item"]
---

**Task / category:** <!-- e.g. srb_grammar / enklitike -->

**Proposed item(s)** (JSON, one per line — must validate against the schema):

```json
{"id": "srb-grammar-enklitike-00XX", "task": "srb_grammar", "category": "enklitike", "question": "...", "choices": ["...", "...", "...", "..."], "answer_index": 0, "explanation": "...", "script": "latin", "pair_id": null, "source": "handwritten-<you>", "verified": false, "license": "CC-BY-4.0"}
```

**Norm reference for the gold answer:** <!-- Pravopis MS rule, grammar section, etc. -->

**Checklist:**
- [ ] Exactly one defensibly-correct answer
- [ ] Distractors are realistic mistakes, not nonsense
- [ ] `verified: false`
- [ ] `serbeval validate` passes locally
