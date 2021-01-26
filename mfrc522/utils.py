from collections import OrderedDict
from dataclasses import dataclass
from enum import IntEnum

from typing import List, Union

Sector = IntEnum("Sector", {f"SECTOR_{i}": i for i in range(16)})
Block = IntEnum("Block", {f"BLOCK_{i}": i for i in range(64)})


@dataclass
class SectorKey:
    A: bytes = b"\xFF" * 6
    B: bytes = b"\xFF" * 6


class MifareKeys:
    def __init__(self, keys: Union[List[bytes], bytes]):
        self.sectors = OrderedDict()

        if isinstance(keys, bytes):
            for i, sector in enumerate(keys[i : i + 12] for i in range(0, 192, 12)):
                self.sectors[Sector(i)] = SectorKey(sector[:6], sector[6:])
        else:
            for sector_num, (key_a, key_b) in (
                (i / 2, keys[i : i + 2]) for i in range(0, 32, 2)
            ):
                self.sectors[Sector(sector_num)] = SectorKey(key_a, key_b)

    def __getitem__(self, item):
        if isinstance(item, Block):
            return self.sectors[Sector(item // 4)]
        if isinstance(item, (Sector, int)):
            return self.sectors[item]
        if isinstance(item, tuple):
            return getattr(self[item[0]], item[1])

        raise IndexError(item)

    def __setitem__(self, key, value):
        if isinstance(key, (Sector, int)):
            self.sectors[key] = value
        if isinstance(key, Block):
            self.sectors[Sector(key // 4)] = value
        if isinstance(key, tuple):
            setattr(self.sectors[key[0]], key[1], value)

        raise IndexError(key)

    def __eq__(self, other):
        return self.sectors == other

    @classmethod
    def fill_blank(cls):
        return cls(b"\xFF" * 192)
