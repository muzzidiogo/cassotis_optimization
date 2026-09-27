from __future__ import annotations

from dataclasses import dataclass

TRUCK_CAPACITY_KT = 2.0
TONNES_PER_KT = 1000.0


@dataclass(frozen=True)
class Mineral:
    mineral_id: str
    price_rs_per_t: float
    fet_pct: float
    sio2_pct: float
    al2o3_pct: float
    min_trucks: int
    max_trucks: int
    eligible_sinter1: bool
    eligible_sinter2: bool

    def is_eligible(self, group_id: str) -> bool:
        if group_id == "Sinter1":
            return self.eligible_sinter1
        if group_id == "Sinter2":
            return self.eligible_sinter2
        raise ValueError(f"Unknown group_id: {group_id}")


@dataclass(frozen=True)
class GroupSpec:
    group_id: str
    fet_min: float
    fet_target: float | None
    fet_max: float
    sio2_min: float
    sio2_target: float
    sio2_max: float
    al2o3_min: float
    al2o3_target: float
    al2o3_max: float


@dataclass(frozen=True)
class Pile:
    pile_id: str
    group_id: str
    mass_kt: float

    @property
    def n_trucks(self) -> int:
        value = self.mass_kt / TRUCK_CAPACITY_KT
        if not value.is_integer():
            raise ValueError(
                f"Pile {self.pile_id} mass {self.mass_kt} kt is not a multiple "
                f"of truck capacity {TRUCK_CAPACITY_KT} kt."
            )
        return int(value)


@dataclass(frozen=True)
class ProblemInstance:
    minerals: dict[str, Mineral]
    groups: dict[str, GroupSpec]
    piles: dict[str, Pile]
