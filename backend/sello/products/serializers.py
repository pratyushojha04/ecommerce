from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=True)
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero")
        return value

    def validate_name(self, value):
        if len(value.strip()) == 0:
            raise serializers.ValidationError("Name cannot be empty")
        return value

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'image', 'created_at', 'updated_at']
        read_only_fields = ['shopkeeper', 'created_at', 'updated_at']
