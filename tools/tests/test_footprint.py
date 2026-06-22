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


# ---------------------------------------------------------------------------
# code_bearing — new pure function (MAJOR-3)
# ---------------------------------------------------------------------------

def test_code_bearing_py_file():
    assert footprint.code_bearing(["tools/x.py"]) is True


def test_code_bearing_js_file():
    assert footprint.code_bearing(["src/app.js"]) is True


def test_code_bearing_ts_file():
    assert footprint.code_bearing(["src/index.ts"]) is True


def test_code_bearing_tsx_file():
    assert footprint.code_bearing(["components/App.tsx"]) is True


def test_code_bearing_jsx_file():
    assert footprint.code_bearing(["components/Button.jsx"]) is True


def test_code_bearing_go_file():
    assert footprint.code_bearing(["cmd/main.go"]) is True


def test_code_bearing_rs_file():
    assert footprint.code_bearing(["src/lib.rs"]) is True


def test_code_bearing_java_file():
    assert footprint.code_bearing(["Main.java"]) is True


def test_code_bearing_md_only_false():
    assert footprint.code_bearing(["docs/x.md"]) is False


def test_code_bearing_json_only_false():
    assert footprint.code_bearing(["config.json"]) is False


def test_code_bearing_mixed_docs_only_false():
    assert footprint.code_bearing(["docs/x.md", "a.json"]) is False


def test_code_bearing_empty_false():
    assert footprint.code_bearing([]) is False


def test_code_bearing_mixed_code_and_docs_true():
    # A mix of code and docs is still code-bearing
    assert footprint.code_bearing(["docs/README.md", "tools/footprint.py"]) is True


def test_code_bearing_case_insensitive():
    # Extensions are matched case-insensitively
    assert footprint.code_bearing(["tools/X.PY"]) is True


def test_code_bearing_txt_only_false():
    assert footprint.code_bearing(["notes.txt"]) is False


def test_code_bearing_yml_only_false():
    assert footprint.code_bearing([".github/ci.yml"]) is False


def test_code_bearing_backslash_path():
    # Windows-style separators are handled via _normalize
    assert footprint.code_bearing(["tools\\footprint.py"]) is True


# ---------------------------------------------------------------------------
# manifest — codeBearing field (MAJOR-3)
# ---------------------------------------------------------------------------

def test_manifest_code_bearing_true_for_py_change():
    result = footprint.manifest(["tools/footprint.py"], ["tools/"])
    assert "codeBearing" in result
    assert result["codeBearing"] is True


def test_manifest_code_bearing_false_for_docs_only():
    result = footprint.manifest(["docs/README.md", "config.json"], ["docs/"])
    assert "codeBearing" in result
    assert result["codeBearing"] is False


def test_manifest_code_bearing_false_for_empty():
    result = footprint.manifest([], [])
    assert "codeBearing" in result
    assert result["codeBearing"] is False
