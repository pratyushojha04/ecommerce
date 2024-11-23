from rest_framework import serializers
from .models import User, Product, CartItem, Order, OrderItem
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re

User = get_user_model()

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError('Please provide both email and password.')

        # Convert email to lowercase for case-insensitive comparison
        email = email.lower()
        
        # Try to authenticate the user
        user = authenticate(email=email, password=password)
        
        if not user:
            raise serializers.ValidationError('Invalid email or password.')
        
        if not user.is_active:
            raise serializers.ValidationError('This account has been disabled.')
            
        attrs['user'] = user
        return attrs

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'confirm_password', 'first_name', 
                 'last_name', 'phone', 'role', 'date_joined', 'last_login')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'date_joined': {'read_only': True},
            'last_login': {'read_only': True}
        }

    def validate_email(self, value):
        """
        Validate email format and uniqueness
        """
        # Convert email to lowercase
        value = value.lower()
        
        # Check if email already exists
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        
        return value

    def validate_password(self, value):
        """
        Validate password strength
        """
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError([str(error) for error in e.error_list])
        return value

    def validate(self, attrs):
        """
        Validate that the passwords match and all required fields are present
        """
        if not attrs.get('email'):
            raise serializers.ValidationError({"email": "Email is required."})
            
        if not attrs.get('first_name'):
            raise serializers.ValidationError({"first_name": "First name is required."})
            
        if not attrs.get('last_name'):
            raise serializers.ValidationError({"last_name": "Last name is required."})
            
        if not attrs.get('password'):
            raise serializers.ValidationError({"password": "Password is required."})
            
        if not attrs.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Please confirm your password."})
            
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        
        # Validate phone number format if provided
        phone = attrs.get('phone')
        if phone:
            phone_regex = r'^\+?1?\d{9,15}$'
            if not re.match(phone_regex, phone):
                raise serializers.ValidationError({
                    "phone": "Phone number must be in format: +1234567890"
                })
        
        # Remove confirm_password from the attributes
        attrs.pop('confirm_password', None)
        return attrs

    def create(self, validated_data):
        """
        Create and return a new user instance
        """
        try:
            user = User.objects.create_user(
                email=validated_data['email'].lower(),
                password=validated_data['password'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                phone=validated_data.get('phone', ''),
                role=validated_data.get('role', 'CUSTOMER')
            )
            return user
        except Exception as e:
            raise serializers.ValidationError({
                "error": f"Failed to create user: {str(e)}"
            })

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if password:
            instance.set_password(password)
            
        instance.save()
        return instance

class ProductSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    created_by_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'category', 
                 'subcategory', 'stock', 'image', 'created_at', 
                 'updated_at', 'created_by', 'created_by_id']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative.")
        return value

    def validate_category(self, value):
        valid_categories = dict(Product.CATEGORY_CHOICES).keys()
        if value not in valid_categories:
            raise serializers.ValidationError(
                f"Invalid category. Choose from {', '.join(valid_categories)}"
            )
        return value

    def validate_subcategory(self, value):
        category = self.initial_data.get('category')
        if category == 'Dairy':
            valid_subcategories = ['Milk', 'Cheese', 'Butter', 'Yogurt', 'Paneer', 'Cream']
        elif category == 'Grocery':
            valid_subcategories = ['Rice', 'Pulses', 'Flour', 'Oil', 'Spices', 'Sugar', 'Salt']
        else:
            raise serializers.ValidationError("Please select a category first.")
            
        if value not in valid_subcategories:
            raise serializers.ValidationError(
                f"Invalid subcategory for {category}. Choose from {', '.join(valid_subcategories)}"
            )
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        if not user.is_shopkeeper:
            raise serializers.ValidationError(
                "Only shopkeepers can create products."
            )
        validated_data['created_by'] = user
        return super().create(validated_data)

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True, required=False)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'product_id', 'quantity', 'total_price', 'added_at')
        read_only_fields = ('id', 'added_at')

    def create(self, validated_data):
        user = self.context['request'].user
        product_id = validated_data.pop('product_id')
        product = Product.objects.get(id=product_id)
        
        cart_item, created = CartItem.objects.get_or_create(
            user=user,
            product=product,
            defaults={'quantity': validated_data.get('quantity', 1)}
        )
        
        if not created:
            cart_item.quantity += validated_data.get('quantity', 1)
            cart_item.save()
            
        return cart_item

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'quantity', 'price', 'product_name', 'total_price')
        read_only_fields = ('id', 'price', 'product_name', 'total_price')

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ('id', 'user', 'status', 'total_amount', 'shipping_address', 'created_at', 'items')
        read_only_fields = ('id', 'user', 'created_at', 'total_amount')

    def create(self, validated_data):
        user = self.context['request'].user
        cart_items = CartItem.objects.filter(user=user)
        
        if not cart_items.exists():
            raise serializers.ValidationError("Cart is empty")
            
        total_amount = sum(item.total_price for item in cart_items)
        order = Order.objects.create(
            user=user,
            total_amount=total_amount,
            shipping_address=validated_data['shipping_address']
        )
        
        # Create order items from cart items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price,
                product_name=cart_item.product.name
            )
            
        # Clear the cart
        cart_items.delete()
        
        return order
