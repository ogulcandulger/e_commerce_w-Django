from django.urls import path
from . import views
from .views import (
    HomeView,
    ItemDetailView,
    OrderSummaryView,
    CheckoutView,
    PaymentView,
    AddCouponView,
    RequestRefundView
)

app_name = "my_app"

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('item_list/', views.item_list, name='item_list'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('products/', views.products, name='products'),
    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('payment/', PaymentView.as_view(), name='payment'),
    path('payment/<payment_option>', PaymentView.as_view(), name='payment'),
    path('add-to-cart/<slug>/', views.add_to_cart, name='add-to-cart'),
    path('add-coupon/', AddCouponView.as_view(), name='add-coupon'),
    path('request-refund/', RequestRefundView.as_view(), name='request-refund'),
    path('remove-from-cart/<slug>/', views.remove_from_cart, name='remove-from-cart'),
    path('remove-single-item-from-cart/<slug>/', views.remove_single_item_from_cart, name='remove-single-item-from-cart'),
    path('add-single-item-to-cart/<slug>/', views.add_single_item_to_cart, name='add-single-item-to-cart'),
]