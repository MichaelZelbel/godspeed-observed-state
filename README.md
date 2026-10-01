# The observed state of the world, in one line

One line for the morning brief of [Godspeed Mission Control](https://godspeedmissioncontrol.com):

> The observed state of the world: nothing to flag today. https://observedstate.com/en/

or, on a day something is out of its normal range:

> The observed state of the world: 2 things to flag today. Internet, in Mexico; a magnitude 6.4 earthquake (45 km SW of Sola, Vanuatu). https://observedstate.com/en/

## Where it comes from

Every fact in it comes from **[Observed State](https://observedstate.com/en/)**, a site by
Angel Cabrera that checks the world each day and compares each thing only against its own
history. This project only reads it, with his permission (October 2026), and links back to it on
every line. The data is his; please do not reuse it from here for anything else.

The line uses three of his files, the three he chose for it:

- **air traffic** at 30 airports, flagged when one is more than 3.5 standard deviations from its own last 90 days,
- **internet** in 52 countries, flagged past 5 standard deviations from its own last 90 days,
- **earthquakes** of magnitude 6 or more in the last 24 hours.

## The one rule

**Count and name, never weigh.** The line adds the three up and names each item. It never turns
them into a score, an index or a severity ranking, and it never puts "the worst" first: air,
then internet, then earthquakes, names alphabetical, earthquakes in the order they happened.
That is the condition the site's author gave, and the reason the site exists.

## How it runs

`build.py` runs once an hour on GitHub (`.github/workflows/hourly.yml`) for every reader at
once, so the author's site sees one visitor an hour from all of Godspeed Mission Control, not
one per reader. It first asks whether each file changed since the last hour; when it has not,
the answer is empty. It writes:

- `latest.json`: the line, the link, what it was built from and when (`checked_utc`, and each
  file's own `calculado_utc`),
- `latest.txt`: the line and the link, nothing else.

A reader's mission control reads `latest.json` with the `mc-observed-state` command from the
[Godspeed Mission Control download](https://github.com/MichaelZelbel/godspeed-mission-control).
When something went wrong, the line says "not available right now" instead of looking like a
quiet day.

Tests: `python3 -m unittest -v`.

## Licence

The code is MIT. The data belongs to Observed State.
