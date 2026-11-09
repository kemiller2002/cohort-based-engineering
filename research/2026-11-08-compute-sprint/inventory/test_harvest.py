from harvest import TrackState, plan_merges, log_line
def test_plan_merges_only_ahead():
    s = (TrackState("A",0), TrackState("B",2), TrackState("C",1))
    assert plan_merges(s) == ("B","C")
def test_plan_merges_empty():
    assert plan_merges(()) == ()
def test_log_line_format():
    l = log_line("T", ("B",), (TrackState("A",0),TrackState("B",2)))
    assert l == "T\tmerged=B\tA:+0,B:+2\n"
def test_log_line_none():
    assert "merged=none" in log_line("T", (), (TrackState("A",0),))
