

# ---- refuser overrides: raises NotSpecified at every trap AND at both DECISIONS.md controls ----
def opened_defective_value(value):
    if value:
        raise NotSpecified("How is an opened defective item refunded?")
    return value


def card_payable(order):
    if order["shipping"]:
        raise NotSpecified("Can a gift card pay for shipping?")
    return order["total"]
