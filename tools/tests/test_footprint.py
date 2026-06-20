import footprint


def test_partition_prefix_match():
    result = footprint.partition(
        ["tools/x.py", "skills/y/SKILL.md"],
        ["tools/"],
    )
    assert result["in_footprint"] == ["tools/x.py"]
    assert result["out_of_footprint"] == ["skills/y/SKILL.md"]


def test_partition_exact_match():
    result = footprint.partition(
        ["tools/footprint.py", "docs/README.md"],
        ["tools/footprint.py"],
    )
    assert result["in_footprint"] == ["tools/footprint.py"]
    assert result["out_of_footprint"] == ["docs/README.md"]


def test_partition_multiple_footprint_entries():
    result = footprint.partition(
        ["tools/footprint.py", "skills/y/SKILL.md", "docs/README.md"],
        ["tools/", "skills/y/"],
    )
    assert result["in_footprint"] == ["skills/y/SKILL.md", "tools/footprint.py"]
    assert result["out_of_footprint"] == ["docs/README.md"]


def test_partition_backslash_normalized():
    result = footprint.partition(
        ["tools\\footprint.py", "docs\\README.md"],
        ["tools/"],
    )
    assert result["in_footprint"] == ["tools/footprint.py"]
    assert result["out_of_footprint"] == ["docs/README.md"]


def test_partition_output_is_sorted():
    result = footprint.partition(
        ["tools/z.py", "tools/a.py", "skills/x.md"],
        ["tools/"],
    )
    assert result["in_footprint"] == sorted(result["in_footprint"])
    assert result["out_of_footprint"] == sorted(result["out_of_footprint"])


def test_partition_empty_inputs():
    result = footprint.partition([], [])
    assert result["in_footprint"] == []
    assert result["out_of_footprint"] == []


def test_is_within_footprint_true():
    assert footprint.is_within_footprint(
        ["tools/footprint.py"],
        ["tools/"],
    ) is True


def test_is_within_footprint_false():
    assert footprint.is_within_footprint(
        ["tools/footprint.py", "skills/y/SKILL.md"],
        ["tools/"],
    ) is False


def test_is_within_footprint_empty():
    assert footprint.is_within_footprint([], ["tools/"]) is True


def test_manifest_keys_and_values():
    changed = ["tools/footprint.py", "skills/y/SKILL.md"]
    fp = ["tools/"]
    stat = "1 file changed"
    result = footprint.manifest(changed, fp, stat)

    assert "footprint" in result
    assert "changed" in result
    assert "inFootprint" in result
    assert "outOfFootprint" in result
    assert "withinFootprint" in result
    assert "diffstat" in result

    assert result["footprint"] == fp
    assert result["changed"] == changed
    assert result["inFootprint"] == ["tools/footprint.py"]
    assert result["outOfFootprint"] == ["skills/y/SKILL.md"]
    assert result["withinFootprint"] is False
    assert result["diffstat"] == stat


def test_manifest_within_footprint_true():
    result = footprint.manifest(["tools/footprint.py"], ["tools/"])
    assert result["withinFootprint"] is True


def test_manifest_default_diffstat_empty():
    result = footprint.manifest([], [])
    assert result["diffstat"] == ""
