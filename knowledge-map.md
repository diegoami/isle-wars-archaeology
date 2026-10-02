# Knowledge map

What is known about each area of *Isle Wars* (DOS, 1994) and *Isle Wars Pro* (Win9x), and how it
is known. **Everything starts `unknown`.** A cell moves only by evidence:
- to `documented`, when W2 finds a primary source;
- beyond that, only through a reviewed finding and its promotion into `spec/`.

Statuses, basis tags and scope follow game-archaeologist's `vocabulary/` (`status.md`, `basis.md`)
at the commit [`archaeology.json`](archaeology.json) pins. The two games are scoped separately: a
claim holds for both only when it is shown for each (CLAUDE.md rule 19). The reference copies are
the shareware/unregistered releases (U11), so what registration unlocks is `unknown` too.

## Areas

| Area | DOS *Isle Wars* | *Isle Wars Pro* | Basis | Sources and findings |
| --- | --- | --- | --- | --- |
| Setup | unknown | unknown | — | — |
| Players | unknown | unknown | — | — |
| Map and topology | unknown | unknown | — | — |
| Starting state | unknown | unknown | — | — |
| Turn sequence | unknown | unknown | — | — |
| Reinforcement and resources | unknown | unknown | — | — |
| Movement | unknown | unknown | — | — |
| Combat | unknown | unknown | — | — |
| Ownership change | unknown | unknown | — | — |
| Production centres | unknown | unknown | — | — |
| Bonuses (island/continent groups, cards) | unknown | unknown | — | — |
| Hazards | unknown | unknown | — | — |
| AI | unknown | unknown | — | — |
| Randomness | unknown | unknown | — | — |
| Victory and loss | unknown | unknown | — | — |
| Surrender | unknown | unknown | — | — |
| User interface (screens, input, feedback, presentation) | unknown | unknown | — | Added 2026-10-02: malpaco's UI must be at least as good as Pro's. Behaviour is observed; timing, rendering and UI claims need V3 or V4 (U8). |

## Secondary assertions (malpaco, unverified)

[malpaco](https://github.com/diegoami/malpaco) is an earlier re-take of the Isle Wars ruleset, not a
study of it. Its own `RULES.md` warns that "nothing in this document was reverse-engineered". These
are its statements about the original games, kept so that W2 and the research questions can test
them. **None is evidence. Each stays `unknown` until a primary source or a finding settles it.** All
citations are at malpaco `6b533d7`.

| Assertion | Game it names | Status | Source |
| --- | --- | --- | --- |
| *Isle Wars* is by Soleau Software, 1994; *Isle Wars Pro* is its Win9x sequel | both | unknown | `RULES.md:13-14` |
| *Isle Wars* runs in DOSBox in a browser (playdosgames.com, Internet Archive) | DOS | unknown | `DECISIONS.md:27-28` |
| The ruleset's "shape" includes a match rule, hazards, production centres and a three-card idea | unspecified ("Isle Wars … and its sequel") | unknown | `RULES.md:14-15` |
| Kept "from the original": the match rule, the failed-attack penalty, hazards, roaming production centres, the AI's collective surrender offer | unspecified ("the original") | unknown | `DECISIONS.md:399-401` |
| The AI's surrender offer is "*Isle Wars Pro*'s best idea" | Pro | unknown | `RULES.md:189` |
| The board is "46 countries divided between 9 continents" (landmasses subdivided, not separate islands) | DOS ("*Isle Wars*") | unknown | `DECISIONS.md:254` |
| *Isle Wars Pro* is not abandonware; Soleau still sells the registered version | Pro | unknown | `DECISIONS.md:512-513` |
