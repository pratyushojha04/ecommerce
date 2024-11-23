from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
import logging
from .models import User, Product, CartItem, Order
from .serializers import (
    UserSerializer, ProductSerializer,
    CartItemSerializer, OrderSerializer,
    LoginSerializer
)

logger = logging.getLogger(__name__)

class SignUpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info(f"Registration attempt with data: {request.data}")
        
        try:
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                refresh = RefreshToken.for_user(user)
                
                response_data = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': serializer.data
                }
                
                logger.info(f"Registration successful for user: {user.email}")
                return Response(response_data, status=status.HTTP_201_CREATED)
            
            logger.error(f"Registration validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return Response(
                {'error': 'Registration failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SignInView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info(f"Login attempt with data: {request.data}")
        
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            logger.info("Login data validated successfully")
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            response_data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            }
            logger.info(f"Login successful for user: {user.email}")
            return Response(response_data)
            
        logger.error(f"Login validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SignOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class RefreshTokenView(TokenRefreshView):
    pass

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'SHOPKEEPER':
            return Product.objects.filter(created_by=user)
        return Product.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'SHOPKEEPER':
            return Order.objects.filter(items__product__created_by=user).distinct()
        return Order.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    user = request.user
    if user.role == 'SHOPKEEPER':
        # Shopkeeper dashboard
        products = Product.objects.filter(created_by=user)
        orders = Order.objects.filter(items__product__created_by=user).distinct()
        
        total_sales = sum(order.total_amount for order in orders)
        total_products = products.count()
        recent_orders = orders.order_by('-created_at')[:5]
        
        data = {
            'total_sales': total_sales,
            'total_products': total_products,
            'recent_orders': OrderSerializer(recent_orders, many=True).data,
            'products': ProductSerializer(products, many=True).data
        }
    else:
        # Customer dashboard
        orders = Order.objects.filter(user=user)
        cart_items = CartItem.objects.filter(user=user)
        
        total_orders = orders.count()
        cart_total = sum(item.total_price for item in cart_items)
        recent_orders = orders.order_by('-created_at')[:5]
        
        data = {
            'total_orders': total_orders,
            'cart_total': cart_total,
            'recent_orders': OrderSerializer(recent_orders, many=True).data,
            'cart_items': CartItemSerializer(cart_items, many=True).data
        }
    
    return Response(data)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def cart(request):
    """Handle cart operations."""
    try:
        if request.method == 'GET':
            # Get user's cart items
            cart_items = CartItem.objects.filter(user=request.user)
            serializer = CartItemSerializer(cart_items, many=True)
            return Response(serializer.data)
            
        elif request.method == 'POST':
            # Add item to cart
            product_id = request.data.get('product_id')
            quantity = request.data.get('quantity', 1)
            
            if not product_id:
                return Response({'error': 'Product ID is required'}, status=status.HTTP_400_BAD_REQUEST)
                
            product = Product.objects.get(id=product_id)
            cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
            cart_item.quantity += quantity
            cart_item.save()
            return Response({'message': 'Item added to cart'}, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Error in cart: {str(e)}")
        return Response({'error': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def cart_item(request, item_id):
    """Handle individual cart item operations."""
    try:
        cart_item = CartItem.objects.get(id=item_id)
        
        if request.method == 'PUT':
            # Update cart item quantity
            quantity = request.data.get('quantity')
            if not quantity:
                return Response({'error': 'Quantity is required'}, status=status.HTTP_400_BAD_REQUEST)
                
            cart_item.quantity = quantity
            cart_item.save()
            return Response({'message': 'Cart item updated'})
            
        elif request.method == 'DELETE':
            # Remove item from cart
            cart_item.delete()
            return Response({'message': 'Item removed from cart'})
            
    except Exception as e:
        logger.error(f"Error in cart_item: {str(e)}")
        return Response({'error': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def orders(request):
    """Handle orders operations."""
    try:
        if request.method == 'GET':
            # Get user's orders
            orders = Order.objects.filter(user=request.user)
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data)
            
        elif request.method == 'POST':
            # Create new order from cart
            cart_items = CartItem.objects.filter(user=request.user)
            order = Order.objects.create(user=request.user)
            for item in cart_items:
                order.items.add(item)
                item.delete()
            return Response({'message': 'Order created successfully'}, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Error in orders: {str(e)}")
        return Response({'error': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, order_id):
    """Get detailed information about a specific order."""
    try:
        order = Order.objects.get(id=order_id)
        serializer = OrderSerializer(order)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error in order_detail: {str(e)}")
        return Response({'error': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def shopkeeper_dashboard(request):
    """Get dashboard data for shopkeepers."""
    try:
        if request.user.role != 'SHOPKEEPER':
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
            
        products = Product.objects.filter(created_by=request.user)
        orders = Order.objects.filter(items__product__created_by=request.user).distinct()
        
        total_sales = sum(order.total_amount for order in orders)
        total_products = products.count()
        recent_orders = orders.order_by('-created_at')[:5]
        
        data = {
            'total_sales': total_sales,
            'total_products': total_products,
            'recent_orders': OrderSerializer(recent_orders, many=True).data,
            'products': ProductSerializer(products, many=True).data
        }
        return Response(data)
        
    except Exception as e:
        logger.error(f"Error in shopkeeper_dashboard: {str(e)}")
        return Response({'error': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_dashboard(request):
    """Get dashboard data for customers."""
    try:
        if request.user.role != 'CUSTOMER':
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
            
        orders = Order.objects.filter(user=request.user)
        cart_items = CartItem.objects.filter(user=request.user)
        
        total_orders = orders.count()
        cart_total = sum(item.total_price for item in cart_items)
        recent_orders = orders.order_by('-created_at')[:5]
        
        data = {
            'total_orders': total_orders,
            'cart_total': cart_total,
            'recent_orders': OrderSerializer(recent_orders, many=True).data,
            'cart_items': CartItemSerializer(cart_items, many=True).data
        }
        return Response(data)
        
    except Exception as e:
        logger.error(f"Error in customer_dashboard: {str(e)}")
        return Response({'error': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
