from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.user_register, name="user_register"),
    path("login/", views.user_login, name="user_login"),
    path("logout/", views.user_logout, name="user_logout"),
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("", views.product_list, name="product_list"),
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
    path("orders/", views.order_list, name="order_list"),
    path("order/<int:pk>/", views.order_detail, name="order_detail"),
    path("add_product/", views.add_product, name="add_product"),
    path("edit_product/<int:pk>/", views.edit_product, name="edit_product"),
    path("delete_product/<int:pk>/", views.delete_product, name="delete_product"),
    path("create_order/", views.create_order, name="create_order"),
    path(
        "order/<int:order_id>/process_payment/",
        views.process_payment,
        name="process_payment",
    ),
    path("checkout/", views.checkout, name="checkout"),
]
