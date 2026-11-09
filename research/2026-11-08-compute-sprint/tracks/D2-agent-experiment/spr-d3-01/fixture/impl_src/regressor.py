

# ---- regressor overrides (regression-detection validation only): breaks step-1 shipping late in the chain ----
def priced(lines, member):
    subtotal = sum(l["unit_cents"] * l["qty"] for l in lines)
    discount = subtotal * 10 // 100 if member else 0
    shipping = 0 if subtotal > 5000 else 499  # wrong at exactly 5000 (R1-4)
    return {"subtotal": subtotal, "discount": discount, "shipping": shipping, "total": subtotal - discount + shipping}
