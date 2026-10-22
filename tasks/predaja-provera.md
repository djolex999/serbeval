# Nezavisna provera paketa „serbeval-predaja“ (2026-10-22)

Paket: mašinska revizija v2 nacrta (90 pasusa) od drugog alata, osnova `d54f29b`. Ništa nije
spojeno u repo. Skripte iz paketa nisu pokretane; zakrpa je primenjena samo u odvojenom klonu.

## Provereno

| Tvrdnja | Nalaz |
|---|---|
| Izvorni tekst svih 90 pasusa nepromenjen | **Tačno** (isti ID-jevi, nijedan izvor promenjen; zlatni tekst promenjen u 15) |
| Ništa nije `verified: true` | **Tačno** |
| Zakrpa se čisto primenjuje na `d54f29b` | **Tačno**; identična fajlovima u `repository-fixes/` |
| „Sve provere prolaze“ | **Delimično**: `pytest` prolazi (i 9 novih testova), ali **`mypy` strict pada (3 greške: `errors` je prvo int pa lista)** i **`ruff` pada (2× B023)**. Sitno, ali po našim pravilima ne bi smelo u `main` ovako. |
| Uticaj zakrpe na pilot | Zanemarljiv: tačnost po pasusu ista za sva 4 modela; Gemma FP 2 → 3 |

## Preuzimamo

- **Zakrpu za bodovanje** (granične umetnute reči, zamene preko granice mesta, ostatak „će“), uz ispravku tipova i B023.
- **Prave greške iz originala kao obavezna mesta:** gov-0018 *poljoprivrivrednog*, gov-0036 *koji … otkriven* → *koje … otkriveno* (odnosi se na *obeležje*, srednji rod).
- **Uklanjanje mesta *низашта*** (passage-0034): spojeni prilog „bez razloga“ je ispravan (P2010 t. 127).
- **Isključenje 6 pasusa sa oštećenom sintaksom** (gov-0006, 0008, 0012, 0019, 0029, 0038) i 3 sa greškama koje bodovanje ne meri (gov-0021, 0022, 0037). Time otpadaju i sporne gramatičke ispravke u njima (*zamenika*, *budi*, *intervenisaće će*, *С обзиром да*).
- **Isključenje 5 foto-/auto- pasusa**: to traži naš v2 plan (princip 4: „ako se Pravopis 2010 i Klajn razilaze — izbaci“). v1.2 je za te reči prihvatao oba oblika; v2 je stroži, i to je u redu.
- **Citate za 29 č/ć mesta** (samo reference; knjige ostaju van repoa).
- **Ispravku datuma** gov-0034 (2015-03-01 → 2023-04-08), ako se potvrdi na originalu.

## Odbijamo

- **Isključenje 4 pasusa samo zbog „ni jedan“** (gov-0004, 0009, 0023, 0040): ta mesta su kod nas već slobodna (bez boda i bez kazne), pa pasusi ne moraju napolje. Ostala tri (0012, 0019, 0038) izlaze i tako, zbog sintakse.
- **gov-0028 izvan skupa zbog nedostupnog izvora**: tekst je preuzet sa zvaničnog sajta kad je bio dostupan; današnji 403 ne menja poreklo. Zadržati, uz napomenu.
- **gov-0034 *Милосава → Милосав* kao obavezno**: to je ispravka imena (traži znanje o osobi), ne pravopis. Predlog: slobodno mesto (oba oblika, bez boda).

## Ti odlučuješ

1. **gov-0011 *SAD-a → SAD* kao obavezno.** Paket kaže da P2010 tretira SAD kao nepromenljivo; nisam mogao da proverim (tekst Pravopisa trenutno nije dostupan). Ako nema citata — slobodno mesto.
2. **Nova HTML stranica iz paketa** (286 KB, mnoge popravke uvoza/čuvanja, ugrađen **Zod**, MIT). Alternativa: ostati na našoj stranici i preneti samo bitne popravke (npr. prazan uvoz ne briše stare ocene). Zod je nova zavisnost — tvoja odluka.
3. **Samostalni uvoznik `parse_passage_review.py` iz paketa**: dupliran posao sa `serbeval.passage_review`; predlog je da ga ne preuzimamo.

## Rezultat ako se prihvati gore

Evaluacioni skup: 71 + 4 (ni jedan) + 1 (gov-0028) = **76 pasusa**.
