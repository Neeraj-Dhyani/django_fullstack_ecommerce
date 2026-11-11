from decimal import Decimal

from django.core.management.base import BaseCommand

from store.models import Category, Product

DATA = {
    ("Vegetables", "🥦"): [
        ("Tomato", "40", "kg", 120, True, "Juicy, ripe country tomatoes."),
        ("Onion", "35", "kg", 200, False, "Red onions, great for everyday cooking."),
        ("Potato", "30", "kg", 250, False, "Versatile potatoes for fries, curries and more."),
        ("Cauliflower", "45", "piece", 60, False, "Fresh white cauliflower heads."),
        ("Spinach", "20", "bunch", 80, True, "Tender organic spinach leaves."),
        ("Carrot", "50", "kg", 90, True, "Sweet, crunchy carrots."),
        ("Green Capsicum", "70", "kg", 50, False, "Crisp green bell peppers."),
        ("Brinjal", "40", "kg", 70, False, "Glossy purple brinjal."),
    ],
    ("Fruits", "🍎"): [
        ("Banana", "55", "dozen", 100, False, "Naturally ripened bananas."),
        ("Apple", "180", "kg", 60, False, "Crisp Kashmiri apples."),
        ("Mango", "120", "kg", 40, True, "Sweet seasonal mangoes."),
        ("Pomegranate", "160", "kg", 35, False, "Ruby-red, juicy pomegranates."),
    ],
    ("Herbs", "🌿"): [
        ("Coriander", "10", "bunch", 150, True, "Aromatic fresh coriander."),
        ("Mint", "10", "bunch", 120, True, "Cool, fragrant mint leaves."),
        ("Curry Leaves", "10", "bunch", 100, False, "Fresh curry leaves."),
    ],
    ("Roots & Tubers", "🥔"): [
        ("Ginger", "200", "kg", 45, False, "Pungent fresh ginger."),
        ("Garlic", "240", "kg", 55, False, "Strong, flavourful garlic."),
        ("Sweet Potato", "60", "kg", 50, True, "Naturally sweet shakarkandi."),
    ],
}


class Command(BaseCommand):
    help = "Seed Veggimart with sample categories and products."

    def handle(self, *args, **opts):
        created = 0
        for (cat_name, emoji), products in DATA.items():
            cat, _ = Category.objects.get_or_create(name=cat_name, defaults={"emoji": emoji})
            for name, price, unit, stock, organic, desc in products:
                _, was_created = Product.objects.get_or_create(
                    name=name,
                    defaults=dict(category=cat, price=Decimal(price), unit=unit, stock=stock,
                                  is_organic=organic, description=desc),
                )
                created += was_created
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} new products."))
