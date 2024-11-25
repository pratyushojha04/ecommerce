from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'addresses', views.AddressViewSet, basename='address')
router.register(r'customer', views.CustomerProfileViewSet, basename='customer-profile')
router.register(r'shopkeeper', views.ShopkeeperProfileViewSet, basename='shopkeeper-profile')

urlpatterns = [
    path('', include(router.urls)),
]
