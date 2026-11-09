from preflight import Probe, classify, latest_semver, build_record, problems

OK = Probe(True, "main", "abc", "v1.0.0", True, ("README.md",), None)
NOFILES = Probe(True, "main", "abc", None, False, (), "clone failed")
AUTH = Probe(False, None, None, None, False, (), "fatal: could not read Username for 'https://github.com': terminal prompts disabled")
MISSING = Probe(False, None, None, None, False, (), "remote: Repository not found.")

def test_read_write():
    assert classify({"permissions": {"push": True, "pull": True}}, OK) == "READ_WRITE"

def test_read_only():
    assert classify({"permissions": {"push": False, "pull": True}}, OK) == "READ_ONLY"

def test_refs_but_no_content_is_unknown():
    assert classify({"permissions": {"push": True}}, NOFILES) == "UNKNOWN"

def test_metadata_only_when_search_sees_it_but_git_refuses():
    assert classify({"permissions": {"push": True, "pull": True}}, AUTH) == "METADATA_ONLY"

def test_auth_failure_without_metadata_is_denied_not_missing():
    assert classify(None, AUTH) == "ACCESS_DENIED"

def test_not_found():
    assert classify(None, MISSING) == "NOT_FOUND"

def test_latest_semver():
    assert latest_semver(["v1.2.0", "v1.10.0", "v1.9.9", "nightly"]) == "v1.10.0"
    assert latest_semver(["release-3.25.0", "3.4.1"]) == "release-3.25.0"
    assert latest_semver(["latest"]) is None

def test_problems_flags_scope_gap():
    p = problems({"permissions": {"push": True}}, OK, "READ_WRITE", False)
    assert any("not scoped" in x for x in p)

def test_build_record_prs_filtered():
    prs = [{"repo": "forma", "number": 1, "title": "t", "draft": True}, {"repo": "other", "number": 2, "title": "u"}]
    r = build_record(("forma", "C", 1, "", "system"), {"full_name": "kemiller2002/forma", "permissions": {"push": True, "pull": True},
                                                       "visibility": "public", "archived": False}, OK, prs)
    assert r.open_prs == ("#1 [draft] t",) and r.classification == "READ_WRITE" and not r.write_in_session_scope

def test_empty_repo_is_readable_with_problem_noted():
    e = Probe(True, "main", None, None, True, ("(empty repository: no commits)",), None)
    assert classify({"permissions": {"push": True}}, e) == "READ_WRITE"
    assert any("empty" in x for x in problems({"permissions": {"push": True}}, e, "READ_WRITE", False))
