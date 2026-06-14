"""Tests for exercise service: grouping, CRUD logic."""
import pytest
from unittest.mock import patch, MagicMock

from services.exercise_service import group_by_part, PARTS


class TestGroupByPart:
    def test_all_parts_always_present(self):
        """Even with zero exercises, all 5 parts must appear in the grouped result."""
        grouped = group_by_part([])
        part_ids = [g["id"] for g in grouped]
        expected = [p["id"] for p in PARTS]
        assert part_ids == expected

    def test_exercises_assigned_to_correct_part(self):
        exercises = [
            {"exercise_id": "e1", "name": "ベンチプレス", "body_part": "chest"},
            {"exercise_id": "e2", "name": "スクワット",   "body_part": "legs"},
        ]
        grouped = group_by_part(exercises)
        chest_group = next(g for g in grouped if g["id"] == "chest")
        legs_group  = next(g for g in grouped if g["id"] == "legs")
        assert len(chest_group["exercises"]) == 1
        assert len(legs_group["exercises"]) == 1
        assert chest_group["exercises"][0]["exercise_id"] == "e1"

    def test_part_order_matches_canonical(self):
        grouped = group_by_part([])
        assert [g["id"] for g in grouped] == ["chest", "back", "legs", "shoulders", "arms"]


class TestSeedDefaultExercises:
    @patch("services.exercise_service.exercise_repo")
    def test_seeds_13_exercises(self, mock_repo):
        mock_repo.create.return_value = {}
        from services.exercise_service import seed_default_exercises
        seed_default_exercises("user-id-123")
        assert mock_repo.create.call_count == 13
