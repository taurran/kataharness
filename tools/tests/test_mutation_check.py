import mutation_check


def test_mutation_verdict_nonvacuous_when_baseline_passed_mutated_failed():
    """green before, red after mutation → non-vacuous proof."""
    result = mutation_check.mutation_verdict(True, False)
    assert result["testWentRed"] is True
    assert result["nonVacuous"] is True


def test_mutation_verdict_vacuous_when_both_passed():
    """test still passes after mutation → vacuous (no bite)."""
    result = mutation_check.mutation_verdict(True, True)
    assert result["testWentRed"] is False
    assert result["nonVacuous"] is False


def test_mutation_verdict_nonvacuous_false_when_baseline_failed():
    """baseline already failed → can't claim non-vacuity."""
    result = mutation_check.mutation_verdict(False, False)
    assert result["testWentRed"] is False
    assert result["nonVacuous"] is False


def test_apply_line_removal_removes_first_occurrence():
    """Removes the first exact occurrence of target_line from source."""
    result = mutation_check.apply_line_removal("a\nB\nc\n", "B")
    assert "B" not in result
    assert "a" in result
    assert "c" in result


def test_apply_line_removal_raises_for_absent_line():
    """Raises ValueError if target_line is not present in source."""
    try:
        mutation_check.apply_line_removal("a\nB\nc\n", "Z")
        assert False, "Expected ValueError"
    except ValueError:
        pass
