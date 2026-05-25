# tests/unit/domain/test_value_objects.py
"""Unit tests for bci_calib.domain.value_objects.

GO/NO-GO
--------
- AblationCondition has exactly 7 members.
- Members are exactly A, B, C, D, E, F, G.
- F == Platt scaling, G == Isotonic regression.
"""

from __future__ import annotations

from bci_calib.domain.value_objects import AblationCondition


class TestAblationCondition:
    def test_has_exactly_seven_members(self) -> None:
        """GO/NO-GO: AblationCondition must have exactly 7 values."""
        assert len(AblationCondition) == 7

    def test_all_seven_values_exist(self) -> None:
        """All members A through G must be present."""
        expected = {"A", "B", "C", "D", "E", "F", "G"}
        actual = {member.value for member in AblationCondition}
        assert actual == expected

    def test_member_f_is_platt_scaling(self) -> None:
        """F must exist and resolve correctly (Platt scaling)."""
        assert AblationCondition("F") is AblationCondition.F
        assert AblationCondition.F.value == "F"

    def test_member_g_is_isotonic_regression(self) -> None:
        """G must exist and resolve correctly (Isotonic regression)."""
        assert AblationCondition("G") is AblationCondition.G
        assert AblationCondition.G.value == "G"

    def test_is_str_enum(self) -> None:
        """AblationCondition members must behave as strings."""
        assert isinstance(AblationCondition.A, str)
        assert AblationCondition.A == "A"

    def test_all_members_are_single_uppercase_letter(self) -> None:
        for member in AblationCondition:
            assert len(member.value) == 1
            assert member.value.isupper()

    def test_member_ordering(self) -> None:
        """Members must iterate in definition order A→G."""
        values = [m.value for m in AblationCondition]
        assert values == ["A", "B", "C", "D", "E", "F", "G"]
