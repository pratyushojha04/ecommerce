from django.db import models
from django.conf import settings

# Create your models here.

class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Addresses'

    def __str__(self):
        return f"{self.street_address}, {self.city}"

class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_profile')
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    default_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True, related_name='default_for_customers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Customer Profile - {self.user.email}"

class ShopkeeperProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shopkeeper_profile')
    store_name = models.CharField(max_length=255)
    store_description = models.TextField(max_length=1000, blank=True)
    business_registration_number = models.CharField(max_length=100, blank=True)
    store_logo = models.ImageField(upload_to='store_logos/', null=True, blank=True)
    store_banner = models.ImageField(upload_to='store_banners/', null=True, blank=True)
    store_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True, related_name='store_address')
    business_phone = models.CharField(max_length=20, blank=True)
    business_email = models.EmailField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Shopkeeper Profile - {self.store_name}"
