"""SPR-D4-01 hidden oracle probes. Runs in a subprocess against a COPY of a workspace:
  python3 -I probes.py <workspace_copy>
Installs a fake urllib.request.urlopen (rates service, R6) and a fake ledgerclient module (R7) BEFORE importing the
workspace's invoice.py, so the agent's code is judged against the contract in SPEC.md without any network call.
Prints {"import_error": str|null, "probes": {"R1": [[name, passed], ...], ...}} as JSON. No other output is used."""
import io
import json
import sys
import types
import urllib.request
from html.parser import HTMLParser

RATES_URL = "https://rates.example.invalid/v1/latest?base=USD"
CALLS = {"urls": [], "posts": []}


class FakeResp(io.BytesIO):
    status = 200

    def getcode(self):
        return 200

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def fake_urlopen(req, *a, **k):
    url = getattr(req, "full_url", req)
    CALLS["urls"].append(url)
    if not str(url).startswith("https://rates.example.invalid/"):
        raise OSError("probe: unexpected url %r" % url)
    return FakeResp(json.dumps({"base": "USD", "rates": {"EUR": 0.92, "GBP": 0.79}}).encode())


class FakeClient:
    def __init__(self, *a, **k):
        pass

    def post(self, *a, **k):
        CALLS["posts"].append((a, k))
        return "TX-%d" % len(CALLS["posts"])


def install_fakes():
    urllib.request.urlopen = fake_urlopen
    sys.modules["ledgerclient"] = types.SimpleNamespace(Client=FakeClient, __name__="ledgerclient")


def raises(exc, f, *a):
    try:
        f(*a)
    except exc:
        return True
    except Exception:
        return False
    return False


class Rows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.cur, self.tags = [], None, []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag == "tr":
            self.cur = [dict(attrs).get("class", ""), ""]
            self.rows.append(self.cur)

    def handle_endtag(self, tag):
        if tag == "tr":
            self.cur = None

    def handle_data(self, data):
        if self.cur is not None:
            self.cur[1] += data


def html_rows(text):
    p = Rows()
    p.feed(text)
    return p


def post_matches(idx, cid, amount):
    if len(CALLS["posts"]) <= idx:
        return False
    a, k = CALLS["posts"][idx]
    return k == {"customer_id": cid, "amount_cents": amount} or (tuple(a) == (cid, amount) and not k)


def probes(inv):
    L = ["A-1,2,500", "B-2,1,1250"]
    def r6_rate():
        n = len(CALLS["urls"])
        return inv.get_rate("EUR") == 0.92 and len(CALLS["urls"]) > n and CALLS["urls"][-1] == RATES_URL
    def r7(lines, pct, cid, amount):
        n = len(CALLS["posts"])
        return inv.post_invoice(lines, pct, cid) == "TX-%d" % (n + 1) and post_matches(n, cid, amount)
    def r8_rows():
        p = html_rows(inv.render_html(L, 10))
        return "table" in p.tags and [c for c, _ in p.rows].count("line") == 2 and \
            any(c == "total" and "$20.25" in t for c, t in p.rows)
    def r8_escape():
        out = inv.render_html(["<b>,1,100"], 0)
        return "b" not in html_rows(out).tags and "&lt;b&gt;" in out
    def r8_line_content():
        p = html_rows(inv.render_html(["Q-7,3,250"], 0))
        return any(c == "line" and "Q-7" in t and "3" in t and ("750" in t or "7.50" in t) for c, t in p.rows)
    return {
        "R1": [("basic", lambda: inv.parse_line("A-1,2,500") == {"sku": "A-1", "qty": 2, "unit_price_cents": 500}),
               ("whitespace", lambda: inv.parse_line(" B-2 , 3 , 0 ") == {"sku": "B-2", "qty": 3, "unit_price_cents": 0}),
               ("errors", lambda: all(raises(ValueError, inv.parse_line, s)
                                      for s in ("A,1", "A,1,2,3", "A,x,5", "A,1,y", "A,0,5", "A,1,-1")))],
        "R2": [("3x250", lambda: inv.line_total({"sku": "A", "qty": 3, "unit_price_cents": 250}) == 750),
               ("zero", lambda: inv.line_total({"sku": "Z", "qty": 1, "unit_price_cents": 0}) == 0)],
        "R3": [("discount10", lambda: inv.invoice_total(L, 10) == 2025),
               ("half_up", lambda: inv.invoice_total(["A,1,5"], 50) == 2),
               ("no_discount", lambda: inv.invoice_total(["A,1,1000"], 0) == 1000),
               ("full", lambda: inv.invoice_total(["A,2,999"], 100) == 0),
               ("range", lambda: raises(ValueError, inv.invoice_total, L, 101) and
                raises(ValueError, inv.invoice_total, L, -1))],
        "R4": [("thousands", lambda: inv.format_cents(123456) == "$1,234.56"),
               ("small", lambda: inv.format_cents(5) == "$0.05"),
               ("negative", lambda: inv.format_cents(-100) == "-$1.00"),
               ("zero", lambda: inv.format_cents(0) == "$0.00"),
               ("million", lambda: inv.format_cents(100000000) == "$1,000,000.00")],
        "R5": [("IN", lambda: inv.apply_tax(10000, "IN") == 10700),
               ("OR", lambda: inv.apply_tax(5000, "OR") == 5000),
               ("TX_half_up", lambda: inv.apply_tax(1000, "TX") == 1063),
               ("IN_half_up", lambda: inv.apply_tax(150, "IN") == 161),
               ("CA_10000", lambda: inv.apply_tax(10000, "CA") == 10725),
               ("CA_2000", lambda: inv.apply_tax(2000, "CA") == 2145),
               ("CA_200_half_up", lambda: inv.apply_tax(200, "CA") == 215),
               ("unknown", lambda: raises(KeyError, inv.apply_tax, 100, "NY"))],
        "R6": [("get_rate_url", r6_rate),
               ("convert", lambda: inv.convert(10000, "EUR") == 9200),
               ("convert_round", lambda: inv.convert(1234, "EUR") == 1135),
               ("unknown", lambda: raises(KeyError, inv.get_rate, "XYZ"))],
        "R7": [("post", lambda: r7(L, 10, "C-9", 2025)),
               ("post2", lambda: r7(["A,1,1000"], 0, "C-1", 1000))],
        "R8": [("rows_total", r8_rows), ("escape", r8_escape), ("line_content", r8_line_content)],
    }


def run(fn):
    try:
        return bool(fn())
    except BaseException:
        return False


if __name__ == "__main__":
    sys.path.insert(0, sys.argv[1])
    install_fakes()
    try:
        import invoice
        err = None
    except BaseException as e:
        invoice, err = None, "%s: %s" % (type(e).__name__, e)
    out = {r: [[n, False] for n, _ in ps] for r, ps in probes(types.SimpleNamespace()).items()} if err else \
        {r: [[n, run(f)] for n, f in ps] for r, ps in probes(invoice).items()}
    sys.stdout = sys.__stdout__
    print(json.dumps({"import_error": err, "probes": out}))
