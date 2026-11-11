from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Order, Product


class StoreFlowTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Vegetables")
        self.tomato = Product.objects.create(category=cat, name="Tomato", price=Decimal("40"), stock=10)
        self.out = Product.objects.create(category=cat, name="Rare Root", price=Decimal("99"), stock=0)

    def test_pages_render(self):
        for url in [reverse("store:home"), reverse("store:products"),
                    reverse("store:category", args=["vegetables"]),
                    self.tomato.get_absolute_url(), reverse("store:cart"),
                    reverse("login"), reverse("store:signup")]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_search(self):
        r = self.client.get(reverse("store:products"), {"q": "tom"})
        self.assertContains(r, "Tomato")
        self.assertNotContains(r, "Rare Root")

    def test_cart_and_stock_cap(self):
        self.client.post(reverse("store:cart_add", args=[self.tomato.id]), {"quantity": 50})
        r = self.client.get(reverse("store:cart"))
        self.assertEqual(r.context["items"][0]["quantity"], 10)  # capped at stock
        self.client.post(reverse("store:cart_add", args=[self.out.id]))
        self.assertEqual(len(self.client.get(reverse("store:cart")).context["items"]), 1)

    def test_guest_checkout_reduces_stock(self):
        self.client.post(reverse("store:cart_add", args=[self.tomato.id]), {"quantity": 3})
        data = dict(full_name="Asha", phone="9876543210", address="12 MG Road", city="Delhi",
                    pincode="110001", payment_method="cod")
        r = self.client.post(reverse("store:checkout"), data)
        order = Order.objects.get()
        self.assertRedirects(r, reverse("store:order_done", args=[order.pk]))
        self.assertEqual(order.total, Decimal("120"))
        self.tomato.refresh_from_db()
        self.assertEqual(self.tomato.stock, 7)
        self.assertEqual(self.client.get(reverse("store:cart")).context["items"], [])
        self.assertEqual(self.client.get(reverse("store:order_done", args=[order.pk])).status_code, 200)

    def test_other_session_cannot_view_order(self):
        order = Order.objects.create(full_name="X", phone="1", address="a", city="c", pincode="110001")
        r = self.client.get(reverse("store:order_done", args=[order.pk]))
        self.assertRedirects(r, reverse("store:home"))

    def test_checkout_validation(self):
        self.client.post(reverse("store:cart_add", args=[self.tomato.id]))
        r = self.client.post(reverse("store:checkout"), dict(full_name="A", phone="12", address="x",
                             city="d", pincode="12", payment_method="cod"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)

    def test_signup_login_history(self):
        r = self.client.post(reverse("store:signup"), dict(username="neeraj", email="n@x.com",
                             password1="Str0ng!Pass99", password2="Str0ng!Pass99"))
        self.assertRedirects(r, reverse("store:home"))
        self.client.post(reverse("store:cart_add", args=[self.tomato.id]))
        self.client.post(reverse("store:checkout"), dict(full_name="N", phone="9876543210", address="a",
                         city="d", pincode="110001", payment_method="upi"))
        self.assertContains(self.client.get(reverse("store:orders")), "Order #")
        self.assertEqual(User.objects.get().orders.count(), 1)
