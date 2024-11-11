from django.test import TestCase, SimpleTestCase
from django.urls import reverse, resolve
from .models import Product, Order, OrderItem
from . import views

class ProductModelTest(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Test Product",
            description="Test Description",
            price=99.99,
            stock=10,
            available=True
        )

    def test_product_creation(self):
        self.assertEqual(self.product.name, "Test Product")

    def test_product_str_method(self):
        self.assertEqual(str(self.product), "Test Product")

class ProductListViewTest(TestCase):
    def test_product_list_view_status_code(self):
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)

    def test_product_list_view_template(self):
        response = self.client.get(reverse('product_list'))
        self.assertTemplateUsed(response, 'shop/product_list.html')

class AddProductViewTest(TestCase):
    def test_add_product_view_status_code(self):
        response = self.client.get(reverse('add_product'))
        self.assertEqual(response.status_code, 200)

    def test_add_product_post_request(self):
        data = {
            'name': "New Product",
            'description': "New Description",
            'price': 30.0,
            'stock': 10,
            'available': True
        }
        response = self.client.post(reverse('add_product'), data)
        self.assertEqual(response.status_code, 302)

class URLTests(SimpleTestCase):
    def test_product_list_url(self):
        url = reverse('product_list')
        self.assertEqual(resolve(url).func, views.product_list)

    def test_add_product_url(self):
        url = reverse('add_product')
        self.assertEqual(resolve(url).func, views.add_product)
