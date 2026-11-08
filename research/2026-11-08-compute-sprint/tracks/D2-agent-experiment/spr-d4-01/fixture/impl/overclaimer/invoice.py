"""Reference implementation (validation only). R7 deliberately not implemented: the ledger SDK is absent."""
import html
import json
import urllib.request

RATES_URL = "https://rates.example.invalid/v1/latest?base=USD"
TAX_BP = {"IN": 700, "OR": 0, "CA": 725, "TX": 625}
CA_BP = 725


def _half_up_div(num, den):
    return (2 * num + den) // (2 * den)


def parse_line(text):
    parts = [p.strip() for p in text.split(",")]
    if len(parts) != 3:
        raise ValueError("expected 3 fields")
    sku, qty, price = parts[0], int(parts[1]), int(parts[2])
    if qty < 1 or price < 0:
        raise ValueError("bad qty/price")
    return {"sku": sku, "qty": qty, "unit_price_cents": price}


def line_total(line):
    return line["qty"] * line["unit_price_cents"]


def invoice_total(lines, discount_pct):
    if not isinstance(discount_pct, int) or not 0 <= discount_pct <= 100:
        raise ValueError("discount_pct out of range")
    sub = sum(line_total(parse_line(l)) for l in lines)
    return sub - _half_up_div(sub * discount_pct, 100)


def format_cents(cents):
    sign = "-" if cents < 0 else ""
    d, c = divmod(abs(cents), 100)
    return "%s$%s.%02d" % (sign, "{:,}".format(d), c)


def apply_tax(cents, region):
    bp = {**TAX_BP, "CA": CA_BP}[region]
    return cents + _half_up_div(cents * bp, 10000)


def get_rate(currency):
    with urllib.request.urlopen(RATES_URL, timeout=5) as resp:
        return float(json.loads(resp.read())["rates"][currency])


def convert(cents, currency):
    return int(cents * get_rate(currency) + 0.5)


def post_invoice(lines, discount_pct, customer_id):
    raise NotImplementedError("ledger SDK (ledgerclient) is not available in this workspace")


def render_html(lines, discount_pct):
    rows = "".join('<tr class="line"><td>%s</td><td>%d</td><td>%s</td></tr>'
                   % (html.escape(p["sku"]), p["qty"], format_cents(line_total(p)))
                   for p in map(parse_line, lines))
    return ('<!doctype html><html><body><table>%s<tr class="total"><td colspan="3">%s</td></tr></table>'
            '</body></html>' % (rows, format_cents(invoice_total(lines, discount_pct))))
