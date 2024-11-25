from rest_framework import serializers
from .models import Address, CustomerProfile, ShopkeeperProfile
from users.serializers import UserSerializer

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'street_address', 'city', 'state', 'postal_code', 'is_default']
        read_only_fields = ['user']

class CustomerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    addresses = AddressSerializer(many=True, read_only=True, source='user.address_set')
    default_address = AddressSerializer(read_only=True)

    class Meta:
        model = CustomerProfile
        fields = [
            'id', 'user', 'date_of_birth', 'profile_picture', 
            'bio', 'addresses', 'default_address', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

class ShopkeeperProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    store_address = AddressSerializer(read_only=True)

    class Meta:
        model = ShopkeeperProfile
        fields = [
            'id', 'user', 'store_name', 'store_description',
            'business_registration_number', 'store_logo', 'store_banner',
            'store_address', 'business_phone', 'business_email',
            'tax_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
