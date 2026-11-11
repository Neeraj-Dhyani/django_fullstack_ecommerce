from decimal import Decimal

from .models import Product

CART_KEY = "cart"


class Cart:
    """Session-backed cart: {product_id: quantity}."""

    def __init__(self, request):
        self.session = request.session
        self.data = self.session.setdefault(CART_KEY, {})

    def _save(self):
        self.session.modified = True

    def add(self, product, quantity=1):
        pid = str(product.id)
        new_qty = self.data.get(pid, 0) + quantity
        self.data[pid] = max(1, min(new_qty, product.stock))
        self._save()

    def set(self, product, quantity):
        if quantity <= 0:
            self.remove(product)
            return
        self.data[str(product.id)] = min(quantity, product.stock)
        self._save()

    def remove(self, product):
        self.data.pop(str(product.id), None)
        self._save()

    def clear(self):
        self.session[CART_KEY] = {}
        self.data = self.session[CART_KEY]
        self._save()

    def items(self):
        products = Product.objects.filter(id__in=[int(i) for i in self.data], is_active=True)
        rows = []
        for p in products:
            qty = min(self.data[str(p.id)], p.stock) or 0
            if qty:
                rows.append({"product": p, "quantity": qty, "subtotal": p.price * qty})
        return rows

    def __len__(self):
        return sum(self.data.values())

    @property
    def total(self):
        return sum((r["subtotal"] for r in self.items()), Decimal("0"))
