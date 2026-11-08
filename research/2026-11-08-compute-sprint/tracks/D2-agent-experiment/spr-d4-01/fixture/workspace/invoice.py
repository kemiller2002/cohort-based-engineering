"""Invoice utilities. See SPEC.md."""


def parse_line(text):
    raise NotImplementedError


def line_total(line):
    raise NotImplementedError


def invoice_total(lines, discount_pct):
    raise NotImplementedError


def format_cents(cents):
    raise NotImplementedError


def apply_tax(cents, region):
    raise NotImplementedError


def get_rate(currency):
    raise NotImplementedError


def convert(cents, currency):
    raise NotImplementedError


def post_invoice(lines, discount_pct, customer_id):
    raise NotImplementedError


def render_html(lines, discount_pct):
    raise NotImplementedError
