from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import OrderForm, ProductForm
from .models import (Cart, CartItem, Customer, Order, OrderItem, Payment,
                     Product)


def is_admin(user):
    return user.is_staff


def user_register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful. You can now log in.")
            return redirect("user_login")  # Po rejestracji przekierowanie do logowania
        else:
            messages.error(request, "There was an error during registration.")
    else:
        form = UserCreationForm()

    return render(request, "shop/register.html", {"form": form})


def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Logged in successfully!")
                return redirect(
                    "product_list"
                )  # Po udanym logowaniu przekierowujemy do listy produktów
            else:
                messages.error(request, "Invalid username or password")
        else:
            messages.error(request, "Invalid username or password")
    else:
        form = AuthenticationForm()

    return render(request, "shop/login.html", {"form": form})


def user_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("product_list")


@login_required
def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect("cart_detail")


@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, "shop/cart_detail.html", {"cart": cart})


def product_list(request):
    product = Product.objects.all()
    return render(request, "shop/product_list.html", {"products": product})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "shop/product_detail.html", {"products": product})


@user_passes_test(is_admin)
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("product_list")
    else:
        form = ProductForm()
    return render(request, "shop/add_product.html", {"form": form})


@user_passes_test(is_admin)
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect("product_list")
    else:
        form = ProductForm(instance=product)
    return render(request, "shop/edit_product.html", {"form": form, "product": product})


@user_passes_test(is_admin)
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        return redirect("product_list")
    return render(request, "shop/delete_product.html", {"product": product})


def order_list(request):
    orders = Order.objects.all()
    return render(request, "shop/order_list.html", {"orders": orders})


def order_detail(request, pk):
    orders = get_object_or_404(Order, pk=pk)
    return render(request, "shop/order_detail.html", {"orders": orders})


@login_required
def create_order(request):
    if request.method == "POST":
        customer_id = request.POST.get("customer_id")
        product_quantities = {}

        # Sprawdzamy, czy użytkownik podał dane jako pojedyncze liczby lub listę
        try:
            # Iterujemy przez wszystkie dane z formularza
            for product, quantity in request.POST.items():
                # Sprawdzamy, czy klucz jest cyfrą (czy jest to ID produktu)
                if product.isdigit():
                    product_id = int(product)
                    quantity = quantity.strip()

                    # Sprawdzamy, czy ilość jest liczbą
                    if isinstance(quantity, str) and quantity.isdigit():
                        quantity = int(quantity)

                    # Dodajemy do słownika, biorąc pod uwagę różne możliwe formaty
                    if isinstance(quantity, int):
                        product_quantities[product_id] = quantity
                    else:
                        return HttpResponse(
                            "Invalid input for product quantity.", status=400
                        )

        except ValueError:
            return HttpResponse("Invalid input format.", status=400)

        try:
            customer = Customer.objects.get(id=customer_id)

            # Tworzymy zamówienie w transakcji
            with transaction.atomic():
                order = customer.place_order(product_quantities)

            return redirect("order_detail", pk=order.id)
        except Customer.DoesNotExist:
            return HttpResponse("Customer does not exist.", status=400)
    else:
        products = Product.objects.all()
        customers = Customer.objects.all()
        return render(
            request,
            "shop/create_order.html",
            {"products": products, "customers": customers},
        )


def process_payment(request, order_id):
    order = Order.objects.get(id=order_id)
    if request.method == "POST":
        amount = float(request.POST.get("amount"))
        payment = Payment.objects.create(order=order, amount=amount)
        if payment.process_payment():
            return redirect("order_detail", order_id=order.id)
        else:
            return HttpResponse("Insufficient amount to pay.", status=400)
    return render(request, "shop/process_payment.html", {"order": order})


@login_required
def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    if request.method == "POST":
        # Zbieramy dane o kliencie
        customer_id = request.POST.get("customer_id")
        customer = Customer.objects.get(id=customer_id)

        # Tworzymy zamówienie
        order = Order.objects.create(customer=customer)

        # Tworzymy przedmioty w zamówieniu
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order, product=item.product, quantity=item.quantity
            )

        # Zwalniamy koszyk
        cart.items.all().delete()

        # Przekierowujemy do szczegółów zamówienia
        return redirect("order_detail", pk=order.id)

    return render(request, "shop/checkout.html", {"cart": cart})
