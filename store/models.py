from django.db import models
from django.core.validators import MinValueValidator
from uuid import uuid4
from django.conf import settings
from django.contrib import admin

from store import permissions
# Django automatically create id models

# many to many
class Promotion(models.Model):
    description = models.CharField(max_length=255)
    discount = models.FloatField()

class Collection(models.Model):
    title = models.CharField(max_length=255)
    """+ means no reverse relationship with Product model"""
    featured_product = models.ForeignKey('Product', 
                                         on_delete=models.SET_NULL,
                                         null=True, 
                                         related_name="+"
                                         )    
    def __str__(self) -> str:
        return self.title

    # Ordering / sorting the collections
    class Meta:
        ordering = ["title"]


class Product(models.Model):
    # sku = models.CharField(max_length=10,primary_key=True) #Django will create default primary key
    title = models.CharField(max_length=255)               # For this one model
    slug = models.SlugField()
    description = models.TextField(null=True, blank= True)
    # 2222.22
    unit_price = models.DecimalField(max_digits=6, decimal_places=2, validators= [MinValueValidator(1)]) #These two are always required for decimal_places field
    inventory = models.IntegerField( validators= [MinValueValidator(0)])
    last_update = models.DateTimeField(auto_now=True)
    # when delete a collection will not delete all products in that collection PROTECT
    collection = models.ForeignKey(Collection, on_delete=models.PROTECT, related_name="products")
    promotions = models.ManyToManyField(Promotion, blank= True)
    def __str__(self):
        return self.title
   

class Customer(models.Model):
    MEMBERSHIP_BRONZE = "B"
    MEMBERSHIP_SILVER = "S"
    MEMBERSHIP_GOLD = "G"

    MEMBERSHIP_CHOICES = [
        (MEMBERSHIP_BRONZE,"Bronze"),
        (MEMBERSHIP_SILVER,"Silver"),
        (MEMBERSHIP_GOLD,"Gold"),   
    ]
    # first_name = models.CharField(max_length=255)
    # last_name = models.CharField(max_length=255)
    # email = models.EmailField(unique=True)
    phone = models.CharField(max_length=255)
    birth_date = models.DateField(null=True)
    membership = models.CharField(max_length=1,choices=MEMBERSHIP_CHOICES,
                                                default=MEMBERSHIP_BRONZE)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete= models.CASCADE)
    
    def __str__(self) -> str:
        return f"{self.user.first_name} {self.user.last_name}"
    
    @admin.display(ordering='user__first_name') #sort by name
    def first_name(self):
        return self.user.first_name
    @admin.display(ordering='user__first_name')
    def last_name(self):
        return self.user.last_name
    
    class Meta:
        ordering = ["user__first_name", "user__last_name"]

        permissions = [
            ('view_history', 'Can View history')
        ]

class Order(models.Model):
    PAYMENT_PENDING = "P"
    PAYMENT_COMPLETED = "C"
    PAYMENT_FAILED = "F"

    PAYMENT_STATUS = [
        (PAYMENT_PENDING,"Pending"),
        (PAYMENT_COMPLETED,"Completed"),
        (PAYMENT_FAILED,"Failed")
    ]
    # ! This field is auto populated by django, so wont show in forms
    placed_at = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=1,choices=PAYMENT_STATUS, default= PAYMENT_PENDING)
    customer = models.ForeignKey(Customer,on_delete= models.PROTECT )

    class Meta:
        permissions = [
            ('cancel_order', 'can_cancel_order')
        ]

class Address(models.Model):
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    zip = models.CharField(max_length=10)
    """one to one relationship"""
    # customer = models.OneToOneField(Customer, on_delete=models.CASCADE, primary_key=True)
    """one to many relationships"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

class OrderItem(models.Model):
    # With this implamentation order class will have a field items, so that can be 
    # Use for reverse relation from order class to orderitem, so we can fectch the
    # order items for an order.
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name = "items")
    # order = models.ForeignKey(Order, on_delete=models.PROTECT, )
    # ! I set related_name here, so I can use term orderitems in views.py
    # ! where we can use product.orderitems.count() instead of product.orderitem_set.count
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="orderitems")
    quantity = models.PositiveSmallIntegerField( validators= [MinValueValidator(1)] )
    unit_price = models.DecimalField(max_digits=6, decimal_places=2, validators= [MinValueValidator(0)] )

class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )
    #This will not allow duplicate product in one cart; only increase quantity
    class Meta:
        unique_together = [['cart','product']]

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name= "reviews")
    name = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

