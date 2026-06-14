"""Tests for workout service: volume calculation, weekly stats aggregation."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date


class TestVolumeCalc:
    """Test the private volume calculation helper via the service module."""

    def test_volume_single_set(self):
        from services.workout_service import _calc_volume
        exercises = [{"exercise_id": "e1", "sets": [{"reps": 10, "weight": 80}]}]
        assert _calc_volume(exercises) == 800

    def test_volume_multiple_sets(self):
        from services.workout_service import _calc_volume
        exercises = [
            {"exercise_id": "e1", "sets": [
                {"reps": 10, "weight": 60},
                {"reps": 8,  "weight": 80},
                {"reps": 6,  "weight": 95},
            ]}
        ]
        assert _calc_volume(exercises) == 10*60 + 8*80 + 6*95

    def test_volume_empty(self):
        from services.workout_service import _calc_volume
        assert _calc_volume([]) == 0

    def test_volume_multiple_exercises(self):
        from services.workout_service import _calc_volume
        exercises = [
            {"exercise_id": "e1", "sets": [{"reps": 5, "weight": 100}]},
            {"exercise_id": "e2", "sets": [{"reps": 10, "weight": 50}]},
        ]
        assert _calc_volume(exercises) == 500 + 500


class TestGetWeekStats:
    @patch("services.workout_service.workout_repo")
    def test_empty_week_returns_zeros(self, mock_repo):
        mock_repo.list_in_range.return_value = []
        from services.workout_service import get_week_stats
        stats = get_week_stats("user-123")
        assert stats["week_count"] == 0
        assert stats["total_volume"] == 0
        assert len(stats["day_volumes"]) == 7

    @patch("services.workout_service.workout_repo")
    def test_week_count_from_data(self, mock_repo):
        from datetime import datetime, timezone, timedelta
        today = datetime.now(timezone.utc).date()
        monday = today - timedelta(days=today.weekday())
        mock_repo.list_in_range.return_value = [
            {
                "user_id": "u1",
                "date": monday.isoformat(),
                "workout_id": "w1",
                "exercises": [{"exercise_id": "e1", "sets": [{"reps": 10, "weight": 80}]}],
            }
        ]
        from services.workout_service import get_week_stats
        stats = get_week_stats("u1")
        assert stats["week_count"] == 1
        assert stats["total_volume"] == 800
