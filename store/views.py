from multiprocessing import context
from re import S
from urllib import request
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status

from store.permissions import FullDjangoModelPermissions, IsAdminOrReadOnly, ViewCustomerHistoryPermission
from .models import Order, Product, Collection, OrderItem, Review, Cart, CartItem
from .serializers import *
from django.db.models import Count
from rest_framework.viewsets import ModelViewSet, GenericViewSet
# Generic filtering, by this third party library we can filter any
# listings by any field of the model 
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ProductFilter
#using for searching productsd using text
from rest_framework.filters import SearchFilter, OrderingFilter
# implement pagination
from rest_framework.pagination import PageNumberPagination
from .pagination import DefaultPagination
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, ListModelMixin, UpdateModelMixin
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
#Level 4 Viewsets ########################################################
# ! we use view sets to combine different generic APIViews into one viewset
# ! This help to reduce duplicate code and methods that are same in logic but 
# ! in different  Generic APIview. Generic APIS Views using different mixins
# ! Now for viewsets we use Routers instead of urls, and we can list, update, create 
# ! and can do any kind of operations
# simple api views using methods> APIViews > Generic views > Viewsets

class ProductViewSet(ModelViewSet):
    # This implementation combine queryset and serialized class from productList 
    # and ProductDetail Generic APIView, also use one delete method
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["title", "description" ] #search products based on text title, desc
    ordering_fields = ["unit_price", "last_update"] #sorting
    pagination_class = DefaultPagination
    # filterset_fields = ["collection_id"] #on which field we want filter

    #Customer permissions to endpoints for this view
    permission_classes = [IsAdminOrReadOnly]


    # ! After implementing generic filtering using django_filter liabrary
    # ! I have removed/commented the following code which was for filtering
    # ! to simple queryset
    # def get_queryset(self):
    #     queryset = Product.objects.all()
    #     collection_id = self.request.query_params.get('collection_id')
    #     if collection_id:
    #         queryset = queryset.filter(collection_id=collection_id)
    #     return queryset
        
    def destroy(self, request, *args, **kwargs):
       
        if OrderItem.objects.filter(product_id=kwargs['pk']).count() > 0:
            return Response({"error":"product can't be deleted, bcs it is linked with ordered item"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().destroy(request, *args, **kwargs)
    
    
class CollectionViewSet(ModelViewSet):
    queryset = Collection.objects.annotate(products_count=Count("products"))
    serializer_class = CollectionSerializer
    permission_classes = [IsAdminOrReadOnly] #My customer permission class

    def delete(self, request, pk):
        collection = get_object_or_404(Collection, pk = pk)
        if collection.products.count() > 0:
            return Response({"error":"Collection can't be deleted, bcs it is linked with products"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        collection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(product_id = self.kwargs['product_pk']) 

    def get_serializer_context(self):
        return {"product_id": self.kwargs["product_pk"]}

class CartViewSet(
                    CreateModelMixin,
                    RetrieveModelMixin, 
                    GenericViewSet,
                    DestroyModelMixin ):
    queryset = Cart.objects.prefetch_related("items__product").all()
    serializer_class = CartSerializer


class CartItemsViewSet(ModelViewSet):
    #The methods we allow for this endpoint
    http_method_names = ['get', "post", "patch", "delete"]

    #This is how to customly get Serializer based on scenario
    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCartItemSerializer

        elif self.request.method == "PATCH":
            return UpdateCartItemSerializer
        
        return CartItemSerializer
    #This is how to pass some context to serialzer from url 
    def get_serializer_context(self):
        return {"cart_id": self.kwargs['cart_pk']}
    # How to create a custom query set
    def get_queryset(self):
        return CartItem.objects.\
            filter(cart_id = self.kwargs['cart_pk']). \
            select_related('product')
    

# This is how can We get and update the customer profile data
# When we login to our profile, so view and update our profile data
# Like Phone number, dob , membership etc

# Permissions in this view said that authenticated users can update their profile
# and Only Admin Users Can delete add update etc customers, so IsAdminUser is on all view
# And IsAuthenticated is only for one updateing action
class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    # Now all actions in this view are close to anonymous users
    # permission_classes = [IsAdminUser] 
    #Model permissions not only access to endpoint but admin panel activity whi
    # can perform what operations
    permission_classes = [FullDjangoModelPermissions] 
    

    # This is how to override the Permissions For example I want to 
    # Restrict all actions to anonymous users except Get list (viewing) 
    # I can't update only can View with this permission for this veiw
    # def get_permissions(self):
    #     if self.request.method == "GET":
    #         return [AllowAny()]
    #     return [IsAuthenticated()] #Retunning Objects not classes that means ()
    
    # Anyone who have permission from admin can see customers history
    # The permission is give in from admin panel, and is implemented here
    @action(detail=True, permission_classes = [ViewCustomerHistoryPermission])
    def history(self, request, pk):
        return Response("OK")


    @action(detail=False, methods=['GET', 'PUT'],
            permission_classes=[IsAuthenticated]) #Action on list view not detail view
    def me(self, request):
        (customer, created) = Customer.objects.get(user_id = request.user.id)

        if request.method == 'GET':
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer, data = request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


class OrderViewSet(ModelViewSet):
    # queryset = Order.objects.all()
    http_method_names = ["get","post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.request.method in ['PATCH',"DELETE"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def validate_cart_id(self, cart_id):
        if not Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError("No cart with given id found")
        
        if CartItem.objects.filter(cart_id=cart_id).count() == 0:
            raise serializers.ValidationError("No Items founds in cart")

        return cart_id


    def create(self, request, *args, **kwargs):
        # here we mentioning and passing data ot serializer because its in 
        # create method otherwise we create a global serializer_class = ''
        serializer = CreateOrderSerializer(
            data = request.data,
            context = {'user_id':self.request.user.id}    
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    
    
    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateOrderSerializer
        
        elif self.request.method == "PATCH":
            return UpdateOrderSerializer
        
        return OrderSerializer

   
    #! This is violation of command query separation principle
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
       
        # If the customer is not created it will create it & avoid throwing error
        # This is query method to get some data but here we are potentially changing
        # The state of data by create
        customer_id = Customer.objects.only('id').get(user_id=user.id)
        return Order.objects.filter(customer_id = customer_id)
    
    

    
    







#Level 3############################################################################
# ! So here we are using Generic views, and generic views using mixins
# ! This is more cleaner and concise, first we use simnple apiviews
# ! Then we used class based views in level 2 and now in level 3 
# ! We are using generic api views, where we overide methods

# class ProductList(ListCreateAPIView):
#     # if we don't have specific conditions and logics so we can directly pass
#     # queryset and serializerlike below, and delete the methods
#     # queryset = Product.objects.select_related("collection").all()
#     # serializer_class = ProductSerializer

#     def get_queryset(self):
#         return Product.objects.select_related("collection").all() 
#     def get_serializer_class(self):
#         return ProductSerializer
#     def get_serializer_context(self):
#         return {"request": self.request}

# class CollectionList(ListCreateAPIView):
#     def get_queryset(self):
#         return Collection.objects.annotate(products_count = Count("products")).all()
#     def get_serializer_class(self):
#         return CollectionSerializer

# # ! Customizing out generic apiviews
# class ProductDetail(RetrieveUpdateDestroyAPIView):
#     queryset = Product.objects.all()
#     serializer_class = ProductSerializer
    
#     #This is the method we override
#     def delete(self, request, pk):
#         product = get_object_or_404(Product, pk=pk)
#         if product.orderitem_set.count() > 0:
#             return Response({"error":"product can't be deleted, bcs it is linked with ordered item"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
#         product.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)
    
# class CollectionDetail(RetrieveUpdateDestroyAPIView):
#     queryset = Collection.objects.annotate(products_count=Count("products"))
#     serializer_class = CollectionSerializer

#     def delete(self, request, pk):
#         collection = get_object_or_404(Collection, pk = pk)
#         if collection.products.count() > 0:
#             return Response({"error":"Collection can't be deleted, bcs it is linked with products"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
#         collection.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)




#LEVEL 2############################################################################
# ! wE CAN ALSO CREATE CLASS BASED VIEWAS INSTEAD OF METHOD BASED VIEWS SO LETS SEE
# ! The benifit of class based viwes is that here we dont need that if statements
# ! Help us writting clean code
####################################################################################
# class ProductList(APIView):
#     # This is out get method which handle get request
#     def get(self, request):
#         query_set = Product.objects.select_related('collection').all()
#         serilizer = ProductSerializer(
#             query_set, many= True, context={'request': request}    )
#         return  Response(serilizer.data)
    
#     def post(self, request):
#         serializer = ProductSerializer(data = request.data)
#         if serializer.is_valid(raise_exception=True):
#             serializer.save()
#             print(serializer.validated_data)
#             # convention when you create a object, return response with 201
#             return Response(serializer.data, status=status.HTTP_201_CREATED)


# class ProductDetail(APIView):
#     def get(self, request, id):
#         product = get_object_or_404(Product, pk = id)
#         serilizer  = ProductSerializer(product)
#         return  Response(serilizer.data)

#     def put(self, request, id):
#         product = get_object_or_404(Product, pk = id)
#         serializer = ProductSerializer(product, data = request.data) 
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         print(serializer.data)
#         return Response(serializer.data)
    
#     def delete(self, request, id):
#         product = get_object_or_404(Product, pk = id)
#         if product.orderitem_set.count() > 0:
#             return Response({"error":"product can't be deleted, bcs it is linked with ordered item"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
#         product.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


#LEVEL 1####################################################
# ! This is simple implemenntation of model view where we create
# ! views using methods not by classes and we create if statments 
# ! for get post put etc requests

# @api_view(['GET', "POST"])
# def product_list(request):

#     if request.method == 'GET':
#         query_set = Product.objects.select_related('collection').all()
#         serilizer = ProductSerializer(
#             query_set, many= True, context={'request': request}
#             )
#         return  Response(serilizer.data)
    
#     elif request.method == 'POST': 
#         # # ! One method to validate and handle error
#         # serilizer = ProductSerializer(data = request.data)
#         # if serilizer.is_valid():
#         #     serilizer.validated_data
#         #     return Response("OK")
#         # else:
#         #     return Response(
#         #         serilizer.errors,
#         #         status = status.HTTP_400_BAD_REQUEST
#         #     )
#         # ! Another way to validate and hande the errors
#         serializer = ProductSerializer(data = request.data)
#         if serializer.is_valid(raise_exception=True):
#             serializer.save()
#             print(serializer.validated_data)
#             # convention when you create a object, return response with 201
#             return Response(serializer.data, status=status.HTTP_201_CREATED)

# @api_view(["GET", "PUT", "DELETE"])
# def product_detail(request, id):
#     # ! Method number 1 to get product
#     # ! Serialized fields and catch error to return data
#     # try:
#     #     product = Product.objects.get(pk=id)
#     #     serilizer  = ProductSerializer(product)
#     #     return  Response(serilizer.data)
#     # except Product.DoesNotExist:
#     #     return Response(status=status.HTTP_404_NOT_FOUND) ]
#     product = get_object_or_404(Product, pk = id)

#     if request.method == 'GET':
#         # ! Method number 2 (shortest)
#         # product = get_object_or_404(Product, pk = id)
#         serilizer  = ProductSerializer(product)
#         return  Response(serilizer.data)
    
#     elif request.method == "PUT":
#         serializer = ProductSerializer(product, data = request.data) 
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)
    
#     # product.orderitem_set is the reverse relationship accessor
#     # provided by Django. It allows you to access all OrderItem instances
#     # that have a foreign key pointing to this particular Product.

#     elif request.method == 'DELETE':
#         if product.orderitem_set.count() > 0:
#             return Response({"error":"product can't be deleted, bcs it is linked with ordered item"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
#         product.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


# @api_view(['GET', 'POST'])
# def collection_list(request):
#     if request.method == 'GET':
#         query_set = Collection.objects.annotate(products_count = Count("products")).all()
#         serilizer = CollectionSerializer(
#             query_set, many= True )
#         return  Response(serilizer.data)
    
#     elif request.method == 'POST':
#         serializer = CollectionSerializer(data = request.data)
#         if serializer.is_valid(raise_exception=True):
#                 serializer.save()
#                 return Response(serializer.data, status=status.HTTP_201_CREATED) 

# @api_view(['GET' ,'PUT', 'DELETE'])
# def collection_detail(request, id):
#     collection = get_object_or_404(Collection.objects.annotate(products_count=Count("products")), pk = id)
    
#     if request.method == 'GET':
#         serializer = CollectionSerializer(collection)
#         return  Response(serializer.data)
    
#     elif request.method == 'PUT':
#         serializer = CollectionSerializer(collection, data = request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)
    
#     elif request.method == "DELETE":
#         if collection.products.count() > 0:
#             return Response({"error":"Collection can't be deleted, bcs it is linked with products"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
#         collection.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)



