"""Beider-Morse phonetic matching over a fixed name list.

A query matches a list name when their BMPM code sets share at least one code.
Codes are compared case-sensitively: exact mode emits codes such as ``Smit``
where case is significant.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from abydos.phonetic import BeiderMorse

NAME_MODES = {"generic": "gen", "ashkenazi": "ash", "sephardic": "sep"}
MATCH_MODES = ("approx", "exact")


class BMPMMatcher:
    def __init__(self, name_mode: str = "generic", match_mode: str = "approx", concat: bool = False):
        if name_mode not in NAME_MODES:
            raise ValueError(f"name_mode must be one of {sorted(NAME_MODES)}, got {name_mode!r}")
        if match_mode not in MATCH_MODES:
            raise ValueError(f"match_mode must be one of {list(MATCH_MODES)}, got {match_mode!r}")
        self.name_mode = name_mode
        self.match_mode = match_mode
        self.concat = concat
        # concat=False (library default) encodes multi-word names per word, so
        # "Garcia Rodriguez" shares codes with "Rodriguez".
        self._encoder = BeiderMorse(name_mode=NAME_MODES[name_mode], match_mode=match_mode, concat=concat)
        self._cache: dict[str, frozenset[str]] = {}
        self._index: dict[str, list[str]] | None = None
        self._order: dict[str, int] = {}

    def encode(self, name: str) -> frozenset[str]:
        codes = self._cache.get(name)
        if codes is None:
            codes = frozenset(self._encoder.encode(name).split())
            self._cache[name] = codes
        return codes

    def build_index(self, names: Iterable[str]) -> None:
        index: dict[str, list[str]] = defaultdict(list)
        self._order = {}
        for name in names:
            if name in self._order:
                continue
            self._order[name] = len(self._order)
            for code in self.encode(name):
                index[code].append(name)
        self._index = dict(index)

    def match(self, query: str) -> list[str]:
        """Return list names sharing a code with ``query``, in list order."""
        if self._index is None:
            raise RuntimeError("build_index() must be called before match()")
        found = {name for code in self.encode(query) for name in self._index.get(code, ())}
        return sorted(found, key=self._order.__getitem__)
