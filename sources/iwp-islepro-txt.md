# Islepro.txt (Isle Wars Pro game directions)

- **Set**: `iwp-2.0-996e86c5` (`artifacts/known.json`)
- **File**: `Islepro.txt`, 10572 bytes, sha256 `f1e71098a0fb83c17891ed7a5d95acd0a129e1a0712cba3e8148f70c5ca7b4b7`
  (the manifest's value, re-checked on the install on 2026-10-02)
- **Read**: 2026-10-02, in place in the install directory, offline. Decoded as cp1252.
- **What it is**: the in-game directions of the *unregistered* Isle Wars Pro, version 2.0, by Soleau
  Software, Inc. A primary source (the publisher's own help text), basis `doc`: it can make a claim
  `documented` and nothing higher. It says what the game is meant to do, not what it does.
- **Scope**: *Isle Wars Pro* only. It says nothing about DOS *Isle Wars* and no claim here holds
  for DOS. Its words describe the unregistered build; what registration unlocks is only as far as
  [the registration section](#registration) says.
- **Citation**: each quote is followed by `Islepro.txt:<line>`, the line numbers of the file as
  decoded. Quotes are short fragments, kept to what a map row needs; a fragment is not the whole
  sentence, so read the line before relying on more than the fragment says.
  `tools/check_quotes.py` checks every `>` line against the original and caps the share quoted at 25%.
- **Reading caution**: the text says "country", "territory" and "grid" for what appears to be one
  thing, and "island" for the group. This file records the words and does not unify them.

## Title and publisher

The title block names the game, "Version 2.0" and "Soleau Software, Inc." (`Islepro.txt:1-3`). Nothing
is quoted here: the version is recorded in the set manifest, and the publisher's name is quoted from
[the order form](iwp-order-txt.md).

## Objective

> conquer all nine islands

Islepro.txt:10

## Setup

> level of difficulty, color to play, number of starting armies possible, frequency of natural disasters and game speed

Islepro.txt:19-21

> In the unregistered version you play Blue and the computer will play the other three opponents

Islepro.txt:21-22

Tension kept, not resolved: lines 19-21 list "color to play" and "number of starting armies" among the
options, and lines 223-226 (see Registration) list "starting levels of armies" and "changing your
color to play" as things the registered version lets you control. Which of these the unregistered
build locks is not stated.

## Starting state and turn order

> distribute the various armies

Islepro.txt:24-25

> randomly decide who will take the first turn

Islepro.txt:25

## Reinforcement and resources

> you are given armies for the number of countries you occupy. That number is divided by 3

Islepro.txt:26-27

> number of armies to place onto the board

Islepro.txt:28

> Each island gives you extra armies, if you totally control all its countries

Islepro.txt:28-29

> armies you have received for that turn. (Minimum is 2)

Islepro.txt:41-42

The "island values are shown below" (line 30) is a figure of numbers laid out in rows with no island
names (lines 32-36). The text does not say which number belongs to which island; this file does not
guess.

Islepro.txt:32-36

## Attack and combat

> [ATTACK] [MOVE] [PASS] [CARDS] [CANCEL]

Islepro.txt:56

> it must be adjacent to the country you're attacking from

Islepro.txt:58-59

> lines from island to island which allow you to travel across the water

Islepro.txt:59-60

> total number of armies in that grid is equal or greater than the number you're attacking

Islepro.txt:61-62

> The computer then rolls dice (not shown)

Islepro.txt:69

> then one army will be subtracted from the defending country

Islepro.txt:70-71

> A tie will count as a loss for the attacking army

Islepro.txt:72-73

## Losing the attacking army, conquest, move

> If your attacking army ever gets down to 1, then you will forfeit not only the turn, but also the country

Islepro.txt:79-80

> deplete the enemy to 0 armies

Islepro.txt:85

> move at least one army into the conquered territory

Islepro.txt:88

> finish your turn by pressing, either the [MOVE] button or the [PASS] button

Islepro.txt:89-90

> move troops between two adjacent countries

Islepro.txt:95-96

## Cards

> captured a country then you will be given a card

Islepro.txt:113-114

## Trading in cards

> A match is 3 cards which are the same

Islepro.txt:141-142

> If you have a set, they must be exchanged at the top of your turn

Islepro.txt:152

> You can only hold 5 cards in your hand at once

Islepro.txt:159

The text does not say what a trade-in is worth, and this file quotes none of the card types; lines
120-135 list them and lines 144-148 give examples of matches.

## Situations, disasters and production centres

> These events are random

Islepro.txt:167

> An Earthquake has hit the Islands

Islepro.txt:171

> Flooding has inundated some grids

Islepro.txt:172

> A rebellion has occurred in one of the countries

Islepro.txt:173

> Rebels have taken control from an opposing army

Islepro.txt:174

> Production Centers move to other locations

Islepro.txt:175

> Armies located on the Production Centers will be doubled

Islepro.txt:176-177

> a light blue color shown for the army total instead of the normal white

Islepro.txt:177-178

## End of game

> concede that game and play another one

Islepro.txt:189-190

> If you are the victor, the game will end

Islepro.txt:196

> if you decide to quit in the middle of a game and you do not control at least 10 countries then your score WILL be recorded as a loss

Islepro.txt:212-213

## Registration

> The registered version of ISLE WARS PRO allows for up to four human players to compete against each other

Islepro.txt:223-224

> You can control various options such as starting levels of armies, frequency of disasters, clearing scoreboards, and changing your color to play and more...

Islepro.txt:224-226
