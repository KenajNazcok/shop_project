from django.db import models

# Create your models here.


class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.TextField()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def place_order(self, product_quantities):
        order = Order.objects.create(customer=self)
        for product, quantity in product_quantities.items():
            product_instance = Product.objects.get(id=product)
            if product_instance.update_stock(quantity):
                OrderItem.objects.create(
                    order=order, product=product_instance, quantity=quantity
                )
            else:
                raise ValueError(
                    f"Product {product_instance.name} is not available in this quantity."
                )
        return order


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    available = models.BooleanField(default=True)

    def _str_(self):
        return self.name

    def update_stock(self, quantity):
        if self.stock >= quantity:
            self.stock -= quantity
            self.save()
            return True
        return False


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=True)
    customer = models.ForeignKey(
        Customer, related_name="orders", on_delete=models.CASCADE, null=False, default=1
    )

    def _str_(self):
        return f"Order {self.id}"

    def mark_as_paid(self):
        self.paid = True
        self.save()

    def get_total_price(self):
        total = sum(item.get_total_price() for item in self.items.all())
        return total


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, related_name="order_items", on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)

    def get_total_price(self):
        return self.product.price * self.quantity


class Payment(models.Model):
    order = models.OneToOneField(
        Order, related_name="payment", on_delete=models.CASCADE
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order {self.order.id}"

    def process_payment(self):
        if self.amount >= self.order.get_total_price():
            self.order.mark_as_paid()
            self.save()
            return True
        return False


from django.contrib.auth.models import User


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    def get_total(self):
        total = sum(item.get_total_price() for item in self.items.all())
        return total


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_total_price(self):
        return self.product.price * self.quantity
