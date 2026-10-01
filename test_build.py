"""Tests for build.py. Run: python3 -m unittest -v"""

import json
import os
import tempfile
import unittest
from unittest import mock

import build


def adsb(out=(), n=None):
    return {"fuente": "adsb", "fuera_de_rango": len(out) if n is None else n,
            "nodos_fuera_de_rango": list(out), "calculado_utc": "2026-10-01T19:36:51+00:00"}


def ioda(out=(), n=None):
    return {"fuente": "ioda", "fuera_de_rango": len(out) if n is None else n,
            "paises_fuera_de_rango": list(out), "calculado_utc": "2026-10-01T17:16:21+00:00"}


def usgs(quakes=()):
    return {"fuente": "usgs", "sismos": list(quakes), "calculado_utc": "2026-10-01T22:33:58+00:00"}


class Compose(unittest.TestCase):
    def test_nothing(self):
        line, count, items = build.compose(adsb(), ioda(), usgs())
        self.assertEqual(line, "The observed state of the world: nothing to flag today.")
        self.assertEqual((count, items), (0, []))

    def test_the_example_the_author_gave(self):
        line, count, _ = build.compose(adsb(), ioda(["MX"]), usgs([{"magnitud": 6.4, "momento": "2026-10-01T03:00:00"}]))
        self.assertEqual(line, "The observed state of the world: 2 things to flag today. "
                               "Internet, in Mexico; a magnitude 6.4 earthquake.")
        self.assertEqual(count, 2)

    def test_one_thing_is_singular(self):
        line, _, _ = build.compose(adsb(["fra_frankfurt"]), ioda(), usgs())
        self.assertEqual(line, "The observed state of the world: 1 thing to flag today. Air traffic, at Frankfurt.")

    def test_every_item_counts_and_groups_read_as_one_list(self):
        line, count, items = build.compose(
            adsb(["lhr_london", "cdg_paris"]), ioda(["PE", "MX", "DE"]),
            usgs([{"magnitud": 6.1, "lugar": "45 km SW of Sola, Vanuatu", "momento": "2026-10-01T09:00:00"},
                  {"magnitud": 7.0, "lugar": "Kuril Islands", "momento": "2026-10-01T02:00:00"}]))
        self.assertEqual(count, 7)
        self.assertEqual(line, "The observed state of the world: 7 things to flag today. "
                               "Air traffic, at London and Paris; internet, in Germany, Mexico and Peru; "
                               "a magnitude 7.0 earthquake (Kuril Islands); "
                               "a magnitude 6.1 earthquake (45 km SW of Sola, Vanuatu).")
        self.assertEqual(len(items), 7)

    def test_never_weighs_quakes_follow_the_clock_not_the_magnitude(self):
        _, _, items = build.compose(adsb(), ioda(), usgs([
            {"magnitud": 6.0, "lugar": "A", "momento": "2026-10-01T01:00:00"},
            {"magnitud": 7.5, "lugar": "B", "momento": "2026-10-01T02:00:00"}]))
        self.assertEqual([i["name"] for i in items],
                         ["a magnitude 6.0 earthquake (A)", "a magnitude 7.5 earthquake (B)"])

    def test_no_score_words_ever(self):
        line, _, _ = build.compose(adsb(["fra_frankfurt"]), ioda(["MX"]), usgs([{"magnitud": 6.4}]))
        for word in ("score", "index", "severity", "worst", "%", "risk"):
            self.assertNotIn(word, line.lower())

    def test_alphabetical_ignores_the(self):
        line, _, _ = build.compose(adsb(), ioda(["US", "MX", "NL"]), usgs())
        self.assertTrue(line.endswith("Internet, in Mexico, the Netherlands and the United States."), line)

    def test_unknown_codes_are_shown_as_they_arrive(self):
        line, _, _ = build.compose(adsb(["xyz_nowhere"]), ioda(["ZZ"]), usgs())
        self.assertIn("at xyz_nowhere", line)
        self.assertIn("in ZZ", line)

    def test_count_comes_from_the_site_even_when_names_are_missing(self):
        line, count, _ = build.compose(adsb(n=2), ioda(), usgs())
        self.assertEqual(count, 2)
        self.assertIn("2 things to flag today. Air traffic, at 2 air corridors.", line)

    def test_a_missing_field_is_an_error_not_a_quiet_day(self):
        with self.assertRaises(ValueError):
            build.compose({"fuente": "adsb"}, ioda(), usgs())


class Main(unittest.TestCase):
    def run_main(self, fake_fetch):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(build, "HERE", d), mock.patch.object(build, "fetch", fake_fetch):
            code = build.main()
            with open(os.path.join(d, "latest.json"), encoding="utf-8") as f:
                out = json.load(f)
            with open(os.path.join(d, "latest.txt"), encoding="utf-8") as f:
                txt = f.read()
        return code, out, txt

    def test_writes_line_link_and_timestamps(self):
        files = {"adsb": adsb(), "ioda": ioda(), "usgs": usgs()}
        code, out, txt = self.run_main(lambda n: (files[n], "changed"))
        self.assertEqual(code, 0)
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["text"], "The observed state of the world: nothing to flag today. https://observedstate.com/en/")
        self.assertEqual(txt, out["text"] + "\n")
        self.assertEqual(out["sources"]["usgs"]["calculado_utc"], "2026-10-01T22:33:58+00:00")
        self.assertTrue(out["checked_utc"].endswith("Z"))

    def test_a_failed_fetch_says_unavailable_and_exits_nonzero(self):
        def boom(_):
            raise OSError("network down")
        code, out, _ = self.run_main(boom)
        self.assertEqual(code, 1)
        self.assertEqual(out["status"], "unavailable")
        self.assertEqual(out["text"], "The observed state of the world: not available right now. https://observedstate.com/en/")


if __name__ == "__main__":
    unittest.main()
