# from init file importing order_created
from .signals import order_created
from rest_framework import serializers
from decimal import Decimal
from  store.models import Order, OrderItem, Review,CartItem, Collection, Product, Cart, Customer
from rest_framework.viewsets import ModelViewSet
from django.db import transaction
# ! The objects we return in api is not important
# ! to be exactly like our models


# ! Another way to serilize objects using nested method {} with in {}
class CollectionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=255)

# class ProductSerializer(serializers.Serializer):
#     # ! What fields we want to serialize
#     id = serializers.IntegerField()
#     title = serializers.CharField(max_length=255)
#     price = serializers.DecimalField(max_digits=6, decimal_places=2, source = 'unit_price')
#     # ! Creating fields that are not available in the model
#     price_with_tax = serializers.SerializerMethodField(method_name='calculate_tax')
#     # !By this we include primary key of collection, related model
#     # ! This is one way to serilize a relationship
#     # collection = serializers.PrimaryKeyRelatedField(
#     #     queryset = Collection.objects.all(),
#     # )

#     # # ! Lets return the title/string representation of each collection
#     # collection = serializers.StringRelatedField( 
#     # )
#     # collection = CollectionSerializer()

#     # ! Hyperlink fields; 
#     collection = serializers.HyperlinkedRelatedField(
        
#         queryset=Collection.objects.all(),
#         view_name= "collection-detail"
#     )

#     def calculate_tax(self, product):
#         return product.unit_price * Decimal(1.1)
    
    
    
# ! How to use model serilizers instead serilizing each field
# ! In model serilizartion we dont need to define each field
# ! separate

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "title", "description","slug", "inventory" , "unit_price", "price_with_tax", "collection"]
        # fields = "__al__" #This is the bad practice
    price_with_tax = serializers.SerializerMethodField(
        method_name='calculate_tax'
    )

    def calculate_tax(self, product):
        return product.unit_price * Decimal(1.1)


    # ! Lets say users want to register, we can validate their data
    # ! Using this method and we will override validate method which
    # ! is inside the serializer
    # def validate(self, data):
    #     if data['password'] != data['confirm_password']:
    #         return serializers.ValidationError("Password dont match")
    #     return data
    

    def create(self, validated_data):
        product = Product(**validated_data)
        product.other = 1
        product.save()
        return product
    
    def update(self, instance, validated_data):
        instance.unit_price = validated_data.get("unit_price")
        instance.title = validated_data.get("title")
        instance.inventory = validated_data.get("inventory")
        instance.save()
        return instance
        

class CollectionSerializer(serializers.ModelSerializer):
    # ! Since the collection model does not have field products_count
    # ! So I define a field here  below, which is readonly not accept input data
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = ["id", "title", "products_count"]
        
    def get_products_count(self, obj):
        return obj.products_count

    def create(self, validated_data):
        collection = Collection(**validated_data)
        collection.save()
        return collection
    
    def update(self, instance, validated_data):
        instance.title = validated_data.get("title")
        instance.save()
        return instance

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["id", "date", "name", "description"]

    def create(self, validated_data):
        # Here we receiving product id from viewset context objects
        # so we can post reviews along id , pk will be readed from url
        # not from the form
        product_id = self.context['product_id']
        return Review.objects.create(
            product_id = product_id,
            **validated_data
        )

class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id','title','unit_price']

class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    total_price = serializers.SerializerMethodField()
    #This is convention to return value using method for above field
    # The method should follow the field name
    def get_total_price(self, cart_item:CartItem):
        return cart_item.quantity * cart_item.product.unit_price
    
    class Meta:
        model = CartItem
        fields = ["id","product" ,"quantity","total_price"]

        
class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart):
        return sum([item.quantity * item.product.unit_price for item in cart.items.all()])
    
    # This will show all items in cart, cart id and items
    items = CartItemSerializer(many = True, read_only = True )
    class Meta:
        model = Cart
        fields = ["id", "items", "total_price"]

class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()

    # how to handle if someone updating quantity for a product in cart that does not exists
    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError("No Product With The Given Id was found")
        return value
    
    def save(self, **kwargs):
        product_id = self.validated_data['product_id']
        quantity = self.validated_data['quantity']
        cart_id = self.context['cart_id']

        try:
            cart_item = CartItem.objects.get(cart_id=cart_id, product_id = product_id)
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        except CartItem.DoesNotExist:
            self.instance = CartItem.objects.create(cart_id= cart_id, **self.validated_data)
        return self.instance

    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'quantity']


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["quantity"]
        
class CustomerSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only = True)
    class Meta:
        model = Customer
        fields = ["id", "user_id", "phone", "birth_date", "membership"]

class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    class Meta:
        model = OrderItem
        fields = ["id","product","unit_price","quantity"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    class Meta:
        model = Order
        fields = ["id","customer","placed_at","payment_status","items"]

class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()
   
    # Creating an Order using with tranaction all will be done, or Rollback on failure
    def save(self,**kwargs):
        with transaction.atomic():
            cart_id = self.validated_data['cart_id']
            (customer, create) = Customer.objects.get(user_id = self.context['user_id'])
            order = Order.objects.create(customer = customer)

            cart_items = CartItem.objects.select_related('product') \
            .filter(cart_id= cart_id)

            order_items = [
                OrderItem(
                    order = order,
                    product = item.product,
                    unit_price = item.product.unit_price,
                    quantity = item.quantity
                ) for item in cart_items
            ]

            # This is how to create a bulk order
            OrderItem.objects.bulk_create(order_items)
            # Delete cart after creating the order
            Cart.objects.filter(pk = cart_id).delete()
            order_created.send_robust(self.__class__, order = order)
            return order
            

class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['payment_status']