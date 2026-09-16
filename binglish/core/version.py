"""Semantic version helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class SemVer:
    major: int
    minor: int
    patch: int
    pre: str = ""

    @classmethod
    def parse(cls, raw: str) -> SemVer:
        s = (raw or "").strip()
        if s.lower().startswith("v"):
            s = s[1:]
        pre = ""
        if "-" in s:
            s, pre = s.split("-", 1)
        parts = s.split(".")
        nums = []
        for p in parts[:3]:
            digits = "".join(ch for ch in p if ch.isdigit())
            nums.append(int(digits) if digits else 0)
        while len(nums) < 3:
            nums.append(0)
        return cls(nums[0], nums[1], nums[2], pre)

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        return f"{base}-{self.pre}" if self.pre else base


def is_newer(remote: str, local: str) -> bool:
    """True when remote is a strictly newer release than local."""
    try:
        return SemVer.parse(remote) > SemVer.parse(local)
    except (TypeError, ValueError):
        # Fall back to inequality only if both parse as non-empty strings
        return bool(remote) and remote.strip() != (local or "").strip()
