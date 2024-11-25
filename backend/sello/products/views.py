from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer
import logging

# Create your views here.

logger = logging.getLogger(__name__)

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.action == 'my_products':
            return Product.objects.filter(shopkeeper=self.request.user)
        return Product.objects.all()

    def perform_create(self, serializer):
        logger.info(f"Creating product with data: {self.request.data}")
        serializer.save(shopkeeper=self.request.user)
        logger.info(f"Product created successfully: {serializer.data}")

    def create(self, request, *args, **kwargs):
        logger.info(f"Received product creation request with data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            logger.info(f"Product created successfully: {serializer.data}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"Product creation failed. Errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def my_products(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
