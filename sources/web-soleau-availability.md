# Whether the publisher's site and shortcut URLs are live (Soleau Software)

- **Kind**: a primary source (the publisher's own home page, live and archived) plus a record of
  what the shortcut URLs did when probed. Basis `doc` for the page text only; the probe results are
  observations of 2026-10-02 and are not a status for any map cell.
- **Retrieved**: 2026-10-02, about 21:25 to 21:30 UTC. Page text and HTTP status lines only; no file
  was downloaded.
- **Scope**: the publisher's web presence, for both games alike. It does not bear on how either game
  plays.
- **What it bears on**: the "still sold" row of the secondary table in `knowledge-map.md`. That row
  stays `unknown`: no page here says the publisher has stopped selling, and none says it still sells.

## What the shortcut URLs did

The two URLs are the ones the Pro install's shortcuts point to ([iwp-shortcuts.md](iwp-shortcuts.md)).

| URL | Live, 2026-10-02 | Archived |
| --- | --- | --- |
| `http://www.soleau.com` | HTTP 200, a one-line page (below); `Last-Modified` 2020-11-12; server header `Apache/2.2.15 (CentOS)` | captures from 1996-12-27; the one-line page from 2021-01-06 |
| `http://www.soleau.com/order.html` | HTTP 404 | 200 on 1997-10-22 and on 2020-02-17 ([ordering](web-soleau-ordering.md)) |

Other live probes, same minute: `games/islepro.html`, `wingame.html`, `dosgame.html`, `order1.html`
and `order2.html` each answered HTTP 404; `faq.html` answered 200
([FAQ](web-soleau-faq.md)); `https://www.soleau.com/` did not connect within 20 seconds.

## The home page, live and archived

Live 2026-10-02, and archived 2021-01-06
(<https://web.archive.org/web/20210106122812/http://www.soleau.com/>):

> Thank-you for 30 years

The page holds only that line, a logo image and a table. It does not say the company has closed,
nor that sales have stopped, nor who wrote it.

Archived 2020-08-12 (<https://web.archive.org/web/20200812182849/http://www.soleau.com/>), the last
capture before the one above:

> Welcome to Soleau Games

> Our New Secure Online Store Is Now Open

So the publisher's own home page changed from a store front to the one line between 2020-08-12 and
2021-01-06, and the live page's `Last-Modified` date, 2020-11-12, falls in that gap. The cause is
not stated.

## A different site on the same address, in later captures

Captures of `http://www.soleau.com/` after 2021-01-06 alternate between the line above and an
unrelated page for a New York online community. The Wayback Machine's digest of its content is
the same for the captures of 2021-04-25, 2022-07-07, 2023-02-14, 2025-04-17, 2025-04-25 and 2025-09-15
(the digest, not each page, was compared). The 2021-04-25 capture
(<https://web.archive.org/web/20210425164440/http://www.soleau.com/>):

> Welcome to Echo!

Pages of `https://www.soleau.com/about/`, `/join/`, `/conferences/` and `/events/` in the archive
belong to that other site. They are not Soleau Software's and say nothing of it. Why the address
served them is not known; a shared host answering to more than one name is a guess, not a finding.
