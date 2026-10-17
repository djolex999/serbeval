# Pravopis srpskoga jezika 2010 (Matica srpska, ekavsko izmenjeno i dopunjeno izdanje): primary-text check

Source for every citation below: OCR text of Pravopis 2010, `scratchpad/dl/p2010.txt` (page markers `=====PAGE N` match the printed page numbers). "P2010 p. N" means printed page N; "L" is the line number in the OCR text file. The text is OCR'd Cyrillic. Italic example words come out with substituted letters (ш for т, й for п, u for и, а for п). I give the intended reading and flag the garbling. I could NOT check pages visually: PDF rendering (poppler) is not installed, so every reading below rests on the OCR text alone.

Abbreviations: t. = tačka (numbered rule); rečnik = the pravopisni rečnik (dictionary part, pp. ~259–500).

## 1. „на брзину“ vs „набрзину“

### Takeaway
Pravopis 2010 writes it apart, „на брзину“. The rečnik lists it that way and refers to t. 140в, the rule for prepositional phrases that are fixed adverbial expressions but are still written apart. „набрзину“ does not occur anywhere in the text. Confidence: high.

### Cited Findings
- Rečnik entry: „на брзину, т. 140в“. It sits between набрзо and набрстити — [P2010 p. 378, L23935](p2010.txt)
- The same phrase comes up as a definition: „навалице, прил. ('на брзину, нагло')“ — [P2010 p. 378, L23944](p2010.txt); and „на прешу (на журбу, на брзину), т. 140в“ — [P2010 p. 382, L24373](p2010.txt)
- T. 140в, governing rule: many prepositional phrases with nouns are not joined, „мада се ради о устаљеним прилошким изразима“ (even though they are fixed adverbial expressions). Examples in the list include на прескок, на прекид, на поглед, на срећу — [P2010 p. 96–97, L3955ff](p2010.txt). The OCR'd list does not itself include на брзину; the rečnik entry is what assigns it to 140в.
- T. 141, the contrast rule: writing as one word („спојено“) „по правилу подразумева ново односно померено значење“ (normally implies a new or shifted meaning). Examples are набоље, наглас, начас, напречац — [P2010 p. 97, L3969](p2010.txt)
- A search for every OCR variant of the stem брзин found only the three hits above. There is no „набрзину“ — [P2010 full-text grep](p2010.txt)

### Inferences
- An item that expects „набрзину“ would contradict Pravopis 2010. The correct form is „на брзину“.

### Gaps
- None for this question.

## 2. „црно-бели“ vs „црнобели“

### Takeaway
The general rule (t. 106) hyphenates combinations of different colours: црно-бели дрес, црно-бела одећа. Shades are written as one word: тамнозелен. The rečnik, however, lists BOTH forms by meaning: „црноб(иј)ели филм, црноб(иј)ели телевизор“ as one word, but „црно-б(иј)ели дрес“ with a hyphen. T. 106 itself gives „црно-б(иј)ели филм“ with a hyphen, so the book is internally inconsistent for film. Confidence: high for the hyphen in literal two-colour uses (dresovi, odeća, zastava). The film/TV case is disputed inside the book itself.

### Cited Findings
- T. 106: adjective compounds that mark shades are written as one word (мркожут, плавозелен, тамнозелен), „док се с цртицом пишу комбинације различитих боја“ (whereas combinations of different colours take a hyphen) — [P2010 p. 87, L3565–3568](p2010.txt)
- T. 106 examples with the hyphen: „црвено-б(иј)ели и црно-б(иј)ели дресови, црно-б(иј)ели поглед“, „црно-жута застава“, „црно-б(иј)ели филм, црно-б(иј)ела техника“ (OCR: шехника, йоглед) — [P2010 p. 87, L3570–3573](p2010.txt)
- Rečnik, headword „црно-“: one word for црноок, црнокос (t. 103а). Then „црноб(иј)ели филм, црноб(иј)ели телевизор“ as one word, but „црно-жут, црно-црвен; црно-б(иј)ели дрес, црно-б(иј)ела од(ј)ећа, црно-б(иј)ели дресови, т. 106“ with a hyphen — [P2010 p. 497, L36364–36369](p2010.txt)
- T. 107: adjectives in a coordinate relation („равноправним односом“), meaning parallel or opposed, take a hyphen. Examples are српско-француски, природно-математички — [P2010 p. 87–88, L3574ff](p2010.txt)
- T. 108: some compounds are written either together or with a hyphen, depending on whether the meaning is a single concept or two concepts — [P2010 p. 88, L3596ff](p2010.txt)
- Rečnik: „црно-жута застава ... т. 106“ — [P2010 p. 497, L36373](p2010.txt)

### Inferences
- Literal black-and-white colouring (a jersey, a flag, clothes, a cat): „црно-бели“ is safe.
- „црно-бели филм / телевизор“: t. 106 hyphenates it, while the rečnik writes it as one word (presumably reading it as a single concept, per t. 108). A benchmark item should not hinge on that distinction.
- A bare „црнобели“ for two literal colours is wrong under t. 106.

### Gaps
- The hyphen vs one-word readings on pp. 87 and 497 could not be checked visually against the PDF. Given the rest of that block, the OCR there looks clean.

## 3. „научнофантастични“ vs „научно-фантастични“

### Takeaway
One word. The rečnik lists „научнофантастични, т. 103б“, the rule for adjective compounds derived from a two-word phrase that has merged in meaning (научна фантастика). Confidence: high.

### Cited Findings
- Rečnik: „научнофантастични, т. 103б“. Neighbouring entries are научноистраживачки, научностручни and научнотехнички, all one word and all citing t. 103б — [P2010 p. 384, L24575–24578](p2010.txt)
- T. 103: adjective compounds that are merged in pronunciation and meaning are written as one word. Under б, they are derived from two-word phrases in which the first part is usually subordinate to the second, e.g. „спољнотрговински (: спољна трговина)“, „кривичноправни (: кривично право)“ — [P2010 p. 86, L3499–3519](p2010.txt)
- T. 108 contrasts that with a hyphen when the meaning is „и ... и“ (both X and Y), e.g. књижевно-историјски списи — [P2010 p. 88, L3596ff](p2010.txt)
- No hyphenated „научно-фантастични“ appears anywhere in the text (grep for научно / фантаст).

### Inferences
- „научно-фантастични“ would only fit a reading of "both scientific and fantastic" under t. 108. For the genre sense the answer is „научнофантастични“.

### Gaps
- None.

## 4. „експрес-лонац“, „експрес-пошиљка“ vs written apart

### Takeaway
Written apart, „експрес лонац“ and „експрес пошиљка“, under t. 86а. The rečnik entry for експрес („прид. непром.“, an indeclinable adjective) spells these exact examples apart. Hyphenated forms do not occur. Confidence: high.

### Cited Findings
- Rečnik, headword експрес: „експрес (прид. непром.); одвојено писање“ (written apart). Train names follow under t. 86б, then „експрес линија, експрес лонац, експрес лутрија, експрес пошиљка, експрес ресторан, експрес чистионица, т. 86а“. OCR garbles the italics: ексарес = експрес, uошшька = пошиљка, лушрија = лутрија — [P2010 pp. 311–312, L17002–17009](p2010.txt)
- T. 86: two-word combinations where the first word determines the second and does not decline are written „одвојено“. Under а, the first member is an indeclinable word, mostly foreign, „која се схвата као придев“ (understood as an adjective). Examples are фер игра, бордо боја, гала ручак — [P2010 p. 81, L3288–3299](p2010.txt)
- T. 86б: Балкан експрес, Оријент експрес (names) — [P2010 p. 81, L3300–3304](p2010.txt); rečnik „Балкан експрес, т. 86б“ — [P2010 p. 263, L11990](p2010.txt)

### Inferences
- An item with „експрес-лонац“ or „експрес-пошиљка“ as the gold answer contradicts Pravopis 2010.

### Gaps
- None.

## 5. „викенд-кућа“ vs „викенд кућа“

### Takeaway
Hyphenated, „викенд-кућа“. The rečnik lists викенд-аранжман, викенд-кућа and викенд-насеље with a hyphen ("the first part does not decline") and cites t. 82в. Confidence: high. The OCR garbles „кућа“ as „кylia“, but the entry is unambiguous.

### Cited Findings
- Rečnik: „викенд-аранжман, викенд-кућа, викенд-насеље (прва састав. је непром.), т. 82в“. OCR reads викенд-кylia and викенд-иасеље — [P2010 p. 280, L13741–13744](p2010.txt)
- T. 82: compounds whose parts keep „известан степен значењске аутономности“ (a degree of semantic autonomy), with a separate accent and an indeclinable first part, take a hyphen — [P2010 pp. 75–76, L3033ff](p2010.txt)
- T. 82в: stylistic shortenings in which the first part, a noun, „осећа као замена за придев“ (is felt as standing in for an adjective). Examples are гас-маска, шах-клуб, гол-линија — [P2010 p. 76, L3055–3062](p2010.txt)

### Inferences
- Pravopis 2010 treats викенд as hyphen-forming (t. 82в), while експрес and контакт are written apart (t. 86а/в). The split is lexical, so each word has to be checked separately.

### Gaps
- The OCR garbling of „кућа“ could not be checked visually against the PDF.

## 6. „контакт-особа“, „контакт-телефон“ vs written apart

### Takeaway
Pravopis 2010 writes контакт compounds apart (t. 86в), with the examples „контакт програм, контакт сочива“. Neither „контакт особа“ nor „контакт телефон“ appears in the text in any spelling. Confidence: high for the rule. For the specific words it is medium (inferred from the rule).

### Cited Findings
- Rečnik: „контакт у спојевима: контакт програм, контакт сочива, т. 86в“ (OCR: коншакш йрограм, коншакш сочuва) — [P2010 p. 349, L20870–20871](p2010.txt)
- T. 86в: combinations whose first member also declines and has general independent use, outside such pairings, are written apart. Examples are вестерн филм, интернет адреса, „контакт програм“ — [P2010 pp. 81–82, L3307–3317](p2010.txt)
- The only hyphenated контакт form is the loanword „фул-контакт“ under t. 88б — [P2010 p. 82, L3348](p2010.txt)
- Searches for контакт / коншакш followed by особа or телефон: no hits.

### Inferences
- By t. 86в, „контакт особа“ and „контакт телефон“ are written apart. A hyphenated gold answer would contradict Pravopis 2010.

### Gaps
- The specific compounds контакт особа / контакт телефон are not listed in the text.

## 7. „хтео - не хтео“ / „хтео не хтео“ / „хтео-не хтео“

### Takeaway
T. 125 prescribes a spaced dash (crta), not a hyphen, because the parts have more than one word: „хтео – не хтео“. The rečnik repeats it with the plural. One-word doublets take a hyphen: „хоћу-нећу“, „хоћеш-нећеш“. The book also calls the dash superfluous in „радио не радио“-type phrases. „милом-силом“ is not in the text. Confidence: high.

### Cited Findings
- T. 125: stylistically marked doublings of verb forms take a hyphen: „хоћу-нећу, рекла-казала, повуци-потегни“ — [P2010 p. 92, L3766–3768](p2010.txt)
- T. 125, continued: with multi-word parts „треба писати црту с белинама (не цртицу)“ (a dash with spaces, not a hyphen). Examples are „хтео – не хтео“, ijekavian „хтио – не хтио“, „иди ми – дођи ми“ — [P2010 p. 92, L3769–3772](p2010.txt)
- T. 125, continued: „Сувишна је црта (и запета такође)“ (the dash, and the comma, are superfluous) in phrases like „радио не радио, исто му“ and „учио не учио, једнако пролази“ — [P2010 p. 92, L3773–3774](p2010.txt)
- T. 124а lists „био не био, дошао не дошао“ (negation written apart, no punctuation) — [P2010 p. 92, L3746–3748](p2010.txt)
- Rečnik: „хтео – не хтео, хтели – не хтели и сл., т. 125“ — [P2010 p. 493, L35898–35899](p2010.txt); „хоћу-нећу; хоћеш-нећеш, т. 125“ — [P2010 p. 492, L35793](p2010.txt)
- „милом-силом“: no hit for милом anywhere in the text.

### Inferences
- Correct by Pravopis 2010: „хтео – не хтео“ (spaced dash). „хтео-не хтео“ (hyphen) is wrong. „хтео не хтео“ without a dash fits the t. 125 remark about „радио не радио“, but the book's own named example for хтео uses the dash. Treat the dashed form as the gold answer and avoid items that require rejecting the bare form.
- The OCR renders the crta as " - ". The rule text makes clear it is a spaced crta.

### Gaps
- „милом-силом“ is not covered. T. 125 only governs verb-form doublings, so it does not settle the case directly.

## 8. „до касно (у ноћ)“ vs „до касна“ / „докасно“

### Takeaway
The rečnik has the one-word adverb „докасно“ (задржати се докасно) and glosses it as „до касно у ноћ“ written apart. It cites t. 141. „до касна“ does not occur anywhere. Confidence: high that „докасно“ and „до касно у ноћ“ are the attested forms. Pravopis says nothing about „до касна“.

### Cited Findings
- Rečnik: „докасно, прил. (задржати се докасно – до касно у ноћ), т. 141“. The OCR shows a capital Д at the line start, most likely an artefact — [P2010 p. 304, L16224–16225](p2010.txt)
- Rečnik: „касно, касније, не кашње“ — [P2010 p. 342, L20146](p2010.txt)
- T. 141: one-word spelling implies a new or shifted meaning — [P2010 p. 97, L3969](p2010.txt)
- Searches for касна / до касна / докасна: no hits.

### Inferences
- Pravopis 2010 supports „до касно у ноћ“ (apart, with the indeclinable касно) and „докасно“ on its own. It gives no basis for marking „до касна“ right or wrong, because it is a grammar or usage question the book does not address.

### Gaps
- No ruling on „до касна“; a grammar or usage manual would have to settle it.

## 9. Agreement: „двадесет два ученика је учествовало / су учествовала“

### Takeaway
Pravopis 2010 does not address verb agreement with compound numerals like двадесет два. The only agreement notes near this topic are rečnik remarks on collective numerals („двоје се родило“) and on двојица. Confidence: high that the book does not rule on this.

### Cited Findings
- Rečnik под двоје: „двоје се родило (не двоје су се родили); тако и уз троје, четворо“ — [P2010 p. 297, L15449–15451](p2010.txt)
- Rečnik под двојица: „двојица су дошла и двојица су дошли“ (both allowed; OCR дО/J!..l/а) — [P2010 p. 297, L15453–15455](p2010.txt)
- Rečnik под пут: „двадесет један пут, двадесет два пута“ (noun form after a compound numeral, not verb agreement) — [P2010 p. 431, L29418–29420](p2010.txt)
- Rečnik под сваки: „слагање с бројевима: сваки сат, свака два сата“ (agreement of сваки, not of the verb) — [P2010 p. 444, L30847–30848](p2010.txt)
- Searches for „двадесет два“ + verb, „ученика је/су“ and конгруенц*: no relevant hits.

### Inferences
- Any gold answer for this item has to cite a grammar (e.g. Stanojčić–Popović, or Piper–Klajn Normativna gramatika), not Pravopis 2010.

### Gaps
- Pravopis 2010 does not cover it, so a grammar source is required.
