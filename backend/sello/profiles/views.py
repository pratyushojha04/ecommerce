from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Address, CustomerProfile, ShopkeeperProfile
from .serializers import AddressSerializer, CustomerProfileSerializer, ShopkeeperProfileSerializer
from rest_framework.exceptions import ValidationError

# Create your views here.

class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        address = self.get_object()
        # Remove default status from other addresses
        Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
        # Set this address as default
        address.is_default = True
        address.save()
        return Response({'status': 'Default address set'})

class CustomerProfileViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self.request.user, 'customer_profile', None):
            return CustomerProfile.objects.filter(user=self.request.user)
        return CustomerProfile.objects.none()

    def perform_create(self, serializer):
        # Ensure one profile per user
        if hasattr(self.request.user, 'customer_profile'):
            raise ValidationError('Profile already exists for this user')
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def upload_picture(self, request, pk=None):
        profile = self.get_object()
        if 'profile_picture' not in request.FILES:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        profile.profile_picture = request.FILES['profile_picture']
        profile.save()
        return Response({'status': 'Profile picture updated'})

class ShopkeeperProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ShopkeeperProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self.request.user, 'shopkeeper_profile', None):
            return ShopkeeperProfile.objects.filter(user=self.request.user)
        return ShopkeeperProfile.objects.none()

    def perform_create(self, serializer):
        # Ensure one profile per user
        if hasattr(self.request.user, 'shopkeeper_profile'):
            raise ValidationError('Profile already exists for this user')
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def upload_logo(self, request, pk=None):
        profile = self.get_object()
        if 'store_logo' not in request.FILES:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        profile.store_logo = request.FILES['store_logo']
        profile.save()
        return Response({'status': 'Store logo updated'})

    @action(detail=True, methods=['post'])
    def upload_banner(self, request, pk=None):
        profile = self.get_object()
        if 'store_banner' not in request.FILES:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        profile.store_banner = request.FILES['store_banner']
        profile.save()
        return Response({'status': 'Store banner updated'})
