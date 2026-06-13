export const meta = {
  name: 'serbeval-seed-datasets',
  description: 'Author Serbian eval items per category, adversarially verify each, repair failures',
  phases: [
    { title: 'Author', detail: 'one agent per category writes candidate items' },
    { title: 'Verify', detail: 'adversarial dual-lens check per item batch' },
    { title: 'Repair', detail: 'fix or drop items that failed verification' },
    { title: 'Re-verify', detail: 'fresh verification of repaired items' },
  ],
}

const ITEM_PROPS = {
  question: { type: 'string' },
  choices: { type: 'array', items: { type: 'string' }, minItems: 4, maxItems: 4 },
  answer_index: { type: 'integer', minimum: 0, maximum: 3 },
  explanation: { type: 'string' },
}
const AUTHOR_SCHEMA = {
  type: 'object',
  properties: {
    items: {
      type: 'array',
      items: { type: 'object', properties: ITEM_PROPS, required: ['question', 'choices', 'answer_index', 'explanation'], additionalProperties: false },
    },
  },
  required: ['items'],
  additionalProperties: false,
}
const VERDICTS_SCHEMA = {
  type: 'object',
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        properties: { index: { type: 'integer' }, pass: { type: 'boolean' }, reason: { type: 'string' } },
        required: ['index', 'pass', 'reason'],
        additionalProperties: false,
      },
    },
  },
  required: ['verdicts'],
  additionalProperties: false,
}
const FIX_SCHEMA = {
  type: 'object',
  properties: {
    fixes: {
      type: 'array',
      items: {
        type: 'object',
        properties: { index: { type: 'integer' }, drop: { type: 'boolean' }, ...ITEM_PROPS },
        required: ['index', 'drop', 'question', 'choices', 'answer_index', 'explanation'],
        additionalProperties: false,
      },
    },
  },
  required: ['fixes'],
  additionalProperties: false,
}

const COMMON_RULES = `
PRAVILA ZA STAVKE (poštuj svako):
- Savremeni standardni srpski jezik, EKAVSKA varijanta, LATINICA.
- Tačno 4 ponuđena odgovora; TAČNO JEDAN je ispravan po normi (Pravopis srpskoga jezika MS, normativna gramatika). Distraktori moraju biti greške koje izvorni govornici zaista prave — uverljive, ali nedvosmisleno neispravne.
- NIKAD ne nudi ispravan ijekavski oblik kao "pogrešan" odgovor. Izbegavaj sporne norme oko kojih se normativisti ne slažu (npr. zadnji/poslednji) — drži se jasnih slučajeva.
- Pitanja moraju biti samostalna i raznovrsna po formi: "Koja je rečenica gramatički ispravna?", dopuna praznine "____", "U kojoj rečenici je pravilno...".
- Raznovrsna težina: od očiglednih do stavki koje greše i obrazovani govornici.
- explanation: 1-2 rečenice na srpskom zašto je tačan odgovor tačan.
- Ne ponavljaj istu ciljnu pojavu u više stavki ako spec navodi više pojava — pokrij ih ravnomerno.
Vrati JSON kroz StructuredOutput alat: {items: [{question, choices, answer_index, explanation}]}.`

const GRAMMAR_SPECS = [
  { cat: 'padezi', n: 10, brief: 'Rekcija glagola i predloga i upotreba padeža: instrumental sredstva bez "sa" (pišem olovkom), akuzativ vs lokativ posle u/na (kretanje vs mirovanje), genitiv uz brojeve i količinske priloge, zbog/radi razlika, kod+genitiv, vokativ ličnih imena, slaganje predloga s padežom (protiv+gen, prema+dat).' },
  { cat: 'glagolski-vid', n: 8, brief: 'Glagolski vid: izbor svršenog/nesvršenog glagola u kontekstu (davati/dati, počinjati/početi, kupovati/kupiti), fazni glagoli traže nesvršeni vid (počeo je da piše, NE da napiše), iterativni/habitualni konteksti traže nesvršeni vid, jednokratna izvršena radnja traži svršeni.' },
  { cat: 'kongruencija', n: 10, brief: 'Kongruencija: paukal uz 2/3/4 (dva brata SU DOŠLA), brojevi 5+ (pet ljudi JE DOŠLO), zbirne imenice (deca SU se igrala), većina/manjina+gen (većina je glasala), slaganje prideva i imenice u rodu/broju/padežu, gospoda/braća kongruencija.' },
  { cat: 'enklitike', n: 10, brief: 'Red i položaj enklitika: drugo mesto u rečenici/klauzi, redosled li > glagolske (sam,si,je...) > dativske > akuzativske/genitivske > se > je, "se + je" se sažima u "se" (smejala se, NE smejala se je), enklitika ne sme posle pauze/apozicije ni na početku rečenice, položaj u zavisnoj rečenici posle veznika.' },
  { cat: 'komparacija', n: 7, brief: 'Poređenje prideva i priloga: nepravilni komparativi (dobar-bolji, zao-gori, mali-manji, velik-veći), visok-viši, strog-stroži, lak-lakši, komparativ priloga (mnogo-više), pogrešni oblici tipa "više bolji", superlativ s naj- (najjači se piše sa dva j).' },
  { cat: 'pravopis', n: 10, brief: 'Pravopis: sastavljeno/rastavljeno pisanje (ne znam — odvojeno; neznanje — spojeno; nažalost), futur I (radiću, pisaću — spojeno; videćeš), rečca li (da li, jesi li), č/ć i dž/đ u čestim rečima, veliko slovo (imena naroda — Srbin; prisvojni pridevi na -ov/-in veliko, na -ski malo: Markov, srpski), pisanje negacije uz glagole.' },
  { cat: 'standard', n: 9, brief: 'Standardna upotreba: bezlično "treba da" (treba da radim, NE trebam da radim), "s obzirom na to da" (NE "obzirom da"), "u vezi s tim" (NE "u vezi toga"), zahvaliti se vs zahvaliti (značenjska razlika), oba/obe, "za + infinitiv" germanizam (NE "za poneti"), kontakt-telefon konstrukcije, "ukoliko" vs "ako" stilistika — drži se jasnih normativnih slučajeva.' },
]
const IDIOM_SPECS = [
  { cat: 'idiomi-a', n: 12, brief: 'Frazeologizmi sa životinjama i delovima tela, npr: pasti s konja na magarca, praviti od muve slona, drži jezik za zubima, vuk dlaku menja ali ćud nikada, gledati kao tele u šarena vrata, kupiti mačku u džaku, dođe mi da skočim iz kože, nositi glavu u torbi. Pitanje: "Šta znači izraz ...?" sa 4 ponuđena značenja; distraktori = pogrešna ali uverljiva tumačenja (npr. doslovna ili izokrenuta).' },
  { cat: 'idiomi-b', n: 12, brief: 'Frazeologizmi sa svakodnevnim predmetima i radnjama, npr: mlatiti praznu slamu, ni luk jeo ni luk mirisao, prosuti pamet, obrati zelen bostan, doliti ulje na vatru, baciti rukavicu, trla baba lan, ispravljati krivu Drinu, tražiti iglu u plastu sena, preliti čašu. Format isti: značenje izraza, 4 opcije.' },
  { cat: 'idiomi-c', n: 12, brief: 'Apstraktni i situacioni frazeologizmi, npr: kud puklo da puklo, doći na zelenu granu, ko o čemu baba o uštipcima, od Kulina bana, mešati babe i žabe, spala knjiga na dva slova, naći se između čekića i nakovnja, obećavati kule i gradove — naći tačna ustaljena značenja; pazi da je izraz zaista uobičajen u srpskom. Format isti.' },
]

const specs = [
  ...GRAMMAR_SPECS.map(s => ({ ...s, task: 'srb_grammar' })),
  ...IDIOM_SPECS.map(s => ({ ...s, task: 'srb_idioms' })),
]

function chunk(arr, size) {
  const out = []
  for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size))
  return out
}

function verifyPrompt(items) {
  return `Ti si strogi recenzent za srpski jezički benčmark. Za SVAKU stavku primeni OBA testa:
TEST A — TAČNOST ZLATNOG ODGOVORA: pokušaj da opovrgneš da je označeni odgovor (answer_index) ispravan po normi standardnog srpskog. Proveri i da li je explanation tačno.
TEST B — JEDINSTVENOST I PRIRODNOST: pokušaj da dokažeš da je još neka opcija takođe prihvatljiva (uključujući ijekavske dublete i kolokvijalno prihvaćene varijante koje norma dopušta), ili da je pitanje dvosmisleno, ili da rečenice zvuče neprirodno/veštački.
Stavka PROLAZI (pass=true) samo ako prođe OBA testa. U nedoumici → pass=false sa jasnim razlogom (na srpskom). Odgovori za SVAKU stavku po njenom 'index'.
Stavke (JSON):
${JSON.stringify(items.map((it, i) => ({ index: i, question: it.question, choices: it.choices, answer_index: it.answer_index, explanation: it.explanation })), null, 1)}
Vrati kroz StructuredOutput: {verdicts: [{index, pass, reason}]}.`
}

// Two independent verifier agents per batch; an item must pass BOTH to be kept.
async function verifyBatch(items, phase) {
  if (items.length === 0) return []
  const runs = await parallel([
    () => agent(verifyPrompt(items), { label: 'verify:1', phase, schema: VERDICTS_SCHEMA }),
    () => agent(verifyPrompt(items), { label: 'verify:2', phase, schema: VERDICTS_SCHEMA }),
  ])
  const valid = runs.filter(Boolean)
  return items.map((it, i) => {
    if (valid.length === 0) return { ...it, pass: false, reasons: ['verifikacija nije uspela (nema odgovora)'] }
    const reasons = []
    let pass = true
    for (const run of valid) {
      const v = (run.verdicts || []).find(x => x.index === i)
      if (!v || !v.pass) { pass = false; if (v && v.reason) reasons.push(v.reason) }
    }
    return { ...it, pass, reasons }
  })
}

phase('Author')
const authored = await pipeline(
  specs,
  spec => agent(
    `Ti si lingvista za srpski jezik i autor stavki za benčmark "${spec.task}".
Napiši tačno ${spec.n} stavki višestrukog izbora za kategoriju "${spec.cat}".
SPEC KATEGORIJE: ${spec.brief}
${COMMON_RULES}`,
    { label: `author:${spec.cat}`, phase: 'Author', schema: AUTHOR_SCHEMA },
  ),
  async (result, spec) => {
    if (!result || !result.items) return { spec, kept: [], failed: [] }
    const items = result.items.map(it => ({ ...it, task: spec.task, category: spec.cat }))
    const checked = (await parallel(
      chunk(items, 6).map(c => () => verifyBatch(c, 'Verify')),
    )).filter(Boolean).flat()
    return { spec, kept: checked.filter(x => x.pass), failed: checked.filter(x => !x.pass) }
  },
)

const results = authored.filter(Boolean)
const kept = results.flatMap(r => r.kept)
const failed = results.flatMap(r => r.failed)
log(`Verify pass 1: ${kept.length} kept, ${failed.length} failed`)

// Repair is best-effort: any failure here must NOT lose the first-pass kept items.
let repairedKept = []
const dropped = []
try {
  if (failed.length > 0) {
    phase('Repair')
    const fixResults = (await parallel(chunk(failed, 6).map(batch => () =>
      agent(
        `Ti si lingvista za srpski jezik. Sledeće stavke za benčmark su PALE recenziju. Za svaku: ili je popravi (novo pitanje/opcije/odgovor/objašnjenje koje otklanja SVE navedene primedbe, ista kategorija i ciljna pojava), ili označi drop=true ako se ne može spasti.
${COMMON_RULES}
Stavke sa primedbama (JSON):
${JSON.stringify(batch.map((it, i) => ({ index: i, category: it.category, question: it.question, choices: it.choices, answer_index: it.answer_index, explanation: it.explanation, primedbe: it.reasons })), null, 1)}
Vrati kroz StructuredOutput: {fixes: [{index, drop, question, choices, answer_index, explanation}]} — za drop=true svejedno popuni polja (kopiraj original).`,
        { label: 'repair', phase: 'Repair', schema: FIX_SCHEMA },
      ).then(res => ({ batch, res })).catch(() => ({ batch, res: null })),
    ))).filter(Boolean)

    const candidates = []
    for (const { batch, res } of fixResults) {
      if (!res || !res.fixes) {
        for (const orig of batch) dropped.push({ ...orig, dropReason: 'repair agent failed' })
        continue
      }
      const fixedIdx = new Set()
      for (const f of res.fixes) {
        const orig = batch[f.index]
        if (!orig) continue
        fixedIdx.add(f.index)
        if (f.drop) { dropped.push({ ...orig, dropReason: 'unfixable' }); continue }
        candidates.push({ task: orig.task, category: orig.category, question: f.question, choices: f.choices, answer_index: f.answer_index, explanation: f.explanation })
      }
      batch.forEach((orig, i) => { if (!fixedIdx.has(i)) dropped.push({ ...orig, dropReason: 'no fix returned' }) })
    }
    log(`Repair: ${candidates.length} repaired, ${dropped.length} dropped`)

    if (candidates.length > 0) {
      phase('Re-verify')
      const reverified = (await parallel(
        chunk(candidates, 6).map(c => () => verifyBatch(c, 'Re-verify')),
      )).filter(Boolean).flat()
      repairedKept = reverified.filter(x => x.pass)
      for (const r of reverified.filter(x => !x.pass)) dropped.push({ ...r, dropReason: 'failed re-verify' })
    }
  }
} catch (err) {
  log(`Repair phase error (non-fatal): ${err.message}`)
}

const all = [...kept, ...repairedKept].map(({ pass, reasons, ...it }) => it)
log(`Final: ${all.length} items kept, ${dropped.length} dropped`)
return {
  items: all,
  dropped: dropped.map(d => ({ task: d.task, category: d.category, question: d.question, reasons: d.reasons || [], dropReason: d.dropReason })),
}