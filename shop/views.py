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
            return redirect("user_login")  
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
                )  
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


@login_required(login_url='/login/')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)  
    cart, created = Cart.objects.get_or_create(user=request.user)  
    
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product) 
    
    if not created:
        cart_item.quantity += 1  
        cart_item.save()  

    return redirect("cart_detail")  

@login_required(login_url='/login/')
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

@login_required(login_url='/login/')
def order_list(request):
    orders = Order.objects.filter(customer=request.user.customer)
    return render(request, "shop/order_list.html", {"orders": orders})


def order_detail(request, pk):
    orders = get_object_or_404(Order, pk=pk)
    return render(request, "shop/order_detail.html", {"orders": orders})


@login_required
def create_order(request):
    # Sprawdzamy, czy użytkownik ma koszyk
    cart, created = Cart.objects.get_or_create(user=request.user)

    if request.method == "POST":
        # Tworzymy formularz na podstawie przesłanych danych
        form = OrderForm(request.POST)
        if form.is_valid():
            customer = request.user.customer  # Zakładamy, że użytkownik ma przypisanego klienta
            try:
                # Tworzymy zamówienie i pozycje zamówienia
                order = form.save_order(cart, customer)
                
                # Przekierowujemy użytkownika do szczegółów zamówienia
                return redirect('order_detail', pk=order.id)
            except Exception as e:
                messages.error(request, f"Error while creating order: {e}")
                return redirect('create_order')
        else:
            messages.error(request, "Form submission failed. Please try again.")
    else:
        # Jeśli metoda GET, po prostu tworzymy pusty formularz
        form = OrderForm()

    return render(request, "shop/create_order.html", {"form": form, "cart": cart})


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
        if not hasattr(request.user, 'customer'):
            return HttpResponse("You must be assigned a customer profile.", status=400)
        
        customer = request.user.customer

        # Tworzenie zamówienia
        order = Order.objects.create(customer=customer)

        # Tworzenie pozycji zamówienia i zmniejszenie stanu magazynowego
        for item in cart.items.all():
            # Tworzymy OrderItem dla każdego produktu w koszyku
            OrderItem.objects.create(
                order=order, 
                product=item.product, 
                quantity=item.quantity
            )

            # Aktualizacja stanu magazynowego produktu
            if not item.product.update_stock(item.quantity):
                return HttpResponse(f"Not enough stock for {item.product.name}.", status=400)

        # Usuwanie pozycji z koszyka po utworzeniu zamówienia
        cart.items.all().delete()

        return redirect('order_detail', pk=order.id)

    return render(request, 'shop/checkout.html', {'cart': cart})