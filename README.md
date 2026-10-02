# isle-wars-archaeology (private)

An evidence-backed behavioural specification of *Isle Wars* (DOS, 1994) and *Isle Wars Pro* (Win9x)
by Soleau Software, built by controlled experiments on the original games. It is not a remake, and
not a reconstruction: the games are explored, never replicated (U2). The method, record formats and
vocabularies are [game-archaeologist](https://github.com/diegoami/game-archaeologist)'s, at the
commit [archaeology.json](archaeology.json) pins.

- [knowledge-map.md](knowledge-map.md): what is known about each area, per game, and how it is
  known. Today, nothing: every cell is `unknown`.
- [spec/](spec/README.md): reviewed claims, written only by promotion.
- [docs/tasks/](docs/tasks/README.md): the tasks; their status is on the GitHub issues.
  [docs/process.md](docs/process.md) is the process.

**No original game file is ever committed here, attached to a release, or sent to a cloud session.**
The reference copies are the shareware/unregistered releases, which stay on the user's own machines.
They are identified by hash in [artifacts/known.json](artifacts/README.md). CI enforces this with
`tools/check_no_originals.py`.
