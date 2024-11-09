from django import forms
from django.contrib.auth.models import User

from .models import CartItem, Customer, Order, OrderItem, Payment, Product


# Formularz rejestracji nowego użytkownika
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(
        widget=forms.PasswordInput, label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def clean_password_confirm(self):
        password = self.cleaned_data.get("password")
        password_confirm = self.cleaned_data.get("password_confirm")
        if password != password_confirm:
            raise forms.ValidationError("Passwords do not match.")
        return password_confirm

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


# Formularz do tworzenia zamówienia
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["customer", "paid"]

    def save_order(self, cart, customer):
        order = self.save(commit=False)
        order.customer = customer
        order.save()
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order, product=cart_item.product, quantity=cart_item.quantity
            )
        return order


# Formularz do edytowania zamówienia
class OrderEditForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["paid"]

    def save(self, commit=True):
        order = super().save(commit=False)
        if order.paid:
            order.mark_as_paid()
        if commit:
            order.save()
        return order


# Formularz płatności
class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount"]

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0")
        return amount


# Formularz do adresu dostawy
class DeliveryAddressForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["address"]

    def clean_address(self):
        address = self.cleaned_data["address"]
        if not address.strip():
            raise forms.ValidationError("Address is required.")
        return address


# Formularz do edytowania produktów w koszyku
class CartItemUpdateForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ["quantity"]

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        if quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than 0.")
        if quantity > self.instance.product.stock:
            raise forms.ValidationError(
                f"Only {self.instance.product.stock} items available."
            )
        return quantity


# Formularz do dodawania produktu do koszyka
class CartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ["product", "quantity"]


# Formularz dla produktu (dodawanie/edycja)
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "description", "price", "stock", "available"]
