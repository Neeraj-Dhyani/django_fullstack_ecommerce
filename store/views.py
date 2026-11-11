from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .cart import Cart
from .forms import CheckoutForm, SignUpForm
from .models import Category, Order, OrderItem, Product


def home(request):
    featured = Product.objects.filter(is_active=True, stock__gt=0).order_by("-created_at")[:8]
    return render(request, "store/home.html", {"featured": featured, "categories": Category.objects.all()})


def product_list(request, category_slug=None):
    products = Product.objects.filter(is_active=True).select_related("category")
    category = None
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    q = request.GET.get("q", "").strip()
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if request.GET.get("organic") == "1":
        products = products.filter(is_organic=True)
    sort = request.GET.get("sort", "name")
    products = products.order_by({"price_low": "price", "price_high": "-price"}.get(sort, "name"))
    page = Paginator(products, 12).get_page(request.GET.get("page"))
    return render(request, "store/product_list.html", {
        "page": page, "category": category, "q": q, "sort": sort,
        "organic": request.GET.get("organic") == "1",
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = Product.objects.filter(category=product.category, is_active=True).exclude(pk=product.pk)[:4]
    return render(request, "store/product_detail.html", {"product": product, "related": related})


def cart_detail(request):
    cart = Cart(request)
    return render(request, "store/cart.html", {"items": cart.items(), "total": cart.total})


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    if not product.in_stock:
        messages.error(request, f"{product.name} is out of stock.")
    else:
        try:
            qty = max(1, int(request.POST.get("quantity", 1)))
        except ValueError:
            qty = 1
        Cart(request).add(product, qty)
        messages.success(request, f"Added {product.name} to your cart.")
    return redirect(request.POST.get("next") or "store:cart")


@require_POST
def cart_update(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    try:
        qty = int(request.POST.get("quantity", 1))
    except ValueError:
        qty = 1
    Cart(request).set(product, qty)
    return redirect("store:cart")


@require_POST
def cart_remove(request, product_id):
    Cart(request).remove(get_object_or_404(Product, pk=product_id))
    return redirect("store:cart")


@transaction.atomic
def _place_order(form, cart, user):
    order = form.save(commit=False)
    order.user = user if user.is_authenticated else None
    order.save()
    total = 0
    for row in cart.items():
        # Lock the row so concurrent checkouts can't oversell stock.
        product = Product.objects.select_for_update().get(pk=row["product"].pk)
        qty = min(row["quantity"], product.stock)
        if qty <= 0:
            continue
        product.stock -= qty
        product.save(update_fields=["stock"])
        OrderItem.objects.create(order=order, product=product, product_name=product.name,
                                 unit_price=product.price, quantity=qty)
        total += product.price * qty
    order.total = total
    order.save(update_fields=["total"])
    return order


def checkout(request):
    cart = Cart(request)
    if not cart.items():
        messages.info(request, "Your cart is empty.")
        return redirect("store:products")
    initial = {}
    if request.user.is_authenticated:
        initial["full_name"] = request.user.get_full_name() or request.user.username
    form = CheckoutForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        order = _place_order(form, cart, request.user)
        cart.clear()
        request.session["my_orders"] = request.session.get("my_orders", []) + [order.pk]
        return redirect("store:order_done", order_id=order.pk)
    return render(request, "store/checkout.html", {"form": form, "items": cart.items(), "total": cart.total})


def order_done(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    mine = request.user.is_authenticated and order.user_id == request.user.id
    if not mine and order.pk not in request.session.get("my_orders", []):
        return redirect("store:home")
    return render(request, "store/order_done.html", {"order": order})


@login_required
def order_history(request):
    return render(request, "store/order_history.html", {"orders": request.user.orders.prefetch_related("items")})


def signup(request):
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome to Veggimart!")
        return redirect("store:home")
    return render(request, "registration/signup.html", {"form": form})
