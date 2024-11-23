from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SignUpView, SignInView, SignOutView, RefreshTokenView,
    CartViewSet, OrderViewSet, dashboard,
    ProductViewSet
)

router = DefaultRouter()
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('signin/', SignInView.as_view(), name='signin'),
    path('signout/', SignOutView.as_view(), name='signout'),
    path('token/refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path('dashboard/', dashboard, name='dashboard'),
]
