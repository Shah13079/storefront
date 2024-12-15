from django.shortcuts import render
from django.http import HttpResponse
from store.models import Product, OrderItem, Order, Customer, Collection
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, F 

# Aggretation
from django.db.models.aggregates import Count, Max, Min, Avg, Sum
from django.db.models import Value, Func, ExpressionWrapper, DecimalField
from django.db.models.functions import Concat

#Generic relationships
from django.contrib.contenttypes.models import ContentType
from tags.models import TaggedItem
from store.models import Product

from django.db import connection

# Used for transactions
#We are gonna use its 
from django.db import transaction
#All the code which is in function will be run inside the transaction 
# @transaction.automic()

def say_hello(request):
    # all(),get(),filter(), count()
    # list(query_set)
    # query_set = Product.objects.all()  # return query set
    # for product in query_set:
    #     print(product)
    #! we use query_set for complex aueries to filter, slice results
    # query_set.filter().filter().order_by()
    #! To get a single object
    # product = query_set.filter().get(id=2)  # pk=1 "primary key"
    #! Get Bolean values
    # exited = Product.objects.filter(pk=0).exists()
    #! Get products with 20 dollar price
    #! __gt>, __lt<, __lse , __range=(20, 40 )
    # products = Product.objects.filter(unit_price=20)
    # products = Product.objects.filter(unit_price__range=(20, 40))
    # ! products that contains a text in title, title__startswith
    # products = Product.objects.filter(title__icontains='coffe')
    # ! Products that were added or updated on specific date,time
    # products = Product.objects.filter(last_update__year=2021)

    """ Complex Lookups Using using Q objects"""
    # products = Product.objects.filter(inventory__lt=10).filter(unit_price__lt=20)
    #! Using Q objects ~ means not | means OR
    # products = Product.objects.filter(Q(inventory__lt=10) &~ Q(unit_price__lt=20))
    # ! Comparing two db fields like if unit_price == inventory referencing fields
    # products = Product.objects.filter(inventory=F('unit_price'))

    """SORTING DATA"""
    # ! query set for ascending order, descending order, .reverse() change sort direction
    # products = Product.objects.order_by("unit_price","title")[0]
    # ! This return object, not query set, (latest, earliest)
    # products = Product.objects.earliest("unit_price")

    """Limiting resuts"""
    #! Page size 5 ,[5:10], [10:15], [15:20]
    # products = Product.objects.all()[:5]

    """Selecting fields to query using values"""
    # ! selecting fields and approaching another table column innerjoin
    # products = Product.objects.values("id","title","collection__title")
    # ! return list of items instead of dictionary
    # products = Product.objects.values_list("id","title","collection__title")
    # ! Products that were ordered, get order id lists and display products with that ids
    # ! Second django automa create id field for OrderItem table 
    # query_set = OrderItem.objects.values_list("product__id").distinct()
    # products = Product.objects.filter(id__in=(query_set))

    """Defering fields"""
    # ! Using only method
    # ! if we  accessing unit_price field in template, 
    # ! it separtely sending query requests for each item. so care about that
    # products = Product.objects.only('id','title')
    # ! Using defer means get all fields except description, again it will request for
    # ! each item if we access description in the template
    # products = Product.objects.defer('description')

    """Selecting related objects"""
    # ! If we accessing collection fields, again sending requests for item
    # products = Product.objects.all()
    # ! to preload from collection (other models) we use select_related 
    # ! It will get fields of Products model along collection
    # products = Product.objects.select_related("collection").all()
    # ! We need load some other related field to collection 
    # products = Product.objects.select_related("collection__someOtherField").all()
    # ! prefetch_related (Use for fetching many to many relation for a model)
    # products = Product.objects.prefetch_related("promotions").all()
    # ! Now getting products promotions along collection
    # products = Product.objects.prefetch_related("promotions"
    #                                             ).select_related('collection').all()
    # ! Getting latest top orders along their Customers Names.
    # products = Order.objects.select_related('customer').order_by('-placed_at')[:5]
    # ! Getting items of each order bcz each order could have many items
    # ! Now i need reverase relationship from Order -> OrderItem to get items of each order
    # products = Order.objects.select_related('customer').prefetch_related('orderitem_set'
    #     ).order_by('-placed_at')[:5]
    # ! Now I want to get all the products fields so following is the code
    # products = Order.objects.select_related('customer').prefetch_related('orderitem_set__product'
    #     ).order_by('-placed_at')[:5]
    """AGGREGATING OBJECTS"""
    # ! Calculating total products that have description
    # results = Product.objects.aaggregate(Count('description'))
    # ! Calculating total number of records
    # results = Product.objects.aggregate(Count = Count('id'), min_price= Min('unit_price'))

    """ANNOTATING OBJECTS"""
    # ! We are creating a new 
    # ! Here is_new is a new column which value is product id with addition of 2
    # query_set = Product.objects.annotate(is_new=F('id')+2)
    # ! Concatenating two columns as new column, wrapping '  ' by Value so django will
    # ! not deal it as a separate column
    # query_set = Customer.objects.annotate(
    #     full_name = Func(F('first_name'), Value(' '), F('last_name') , function="CONCAT")
    #     )
    
    # ! Second way of annotating and concatination of two fields
    # query_set = Customer.objects.annotate(
    #     full_name = Concat('first_name', Value(' '),'last_name' )
    #     )
    """Grouping the data"""
    # ! The number of orders each customer has placed
    # ! Reverse relationship
    # query_set = Customer.objects.annotate(
    #     orders_count = Count("order")
    # )

    """Expression Wrappers"""
    # ! The purpose is to result in decimal numbers or float, mix make error, can't calculate
    discounted_price = ExpressionWrapper(F('unit_price') * 0.8, output_field=DecimalField())
    query_set = Product.objects.annotate(discounted_price = discounted_price)

    # Next lecture Quering Generic Relationship
    ## ! It means how to retrive data from the decouples models 
    # ! get_for_model method is available for ContentType manager

    # content_type =  ContentType.objects.get_for_model(Product)  
    # query_set =  TaggedItem\
    #     .objects.select_related('tag')\
    #     .filter(
    #     content_type  = content_type,
    #     object_id = 1
    #     )


    #Custom managers
    # ! More code could be seen in models file. 
    # query_set = TaggedItem.objects.get_tags_for(Product, 1)
    

    #! Catche system in the QuerySet
    query_set = Product.objects.all()
    query_set = list(query_set)
    query_set = list(query_set) #It means that second list read results from the mquery_set catches  

    #!Creating objects

    # collection   = Collection(title = "a")
    # collection.title = "Video Games"
    # collection.featured_product = Product(id = 1)
    # collection.save()

    # !Another way
    # collection.objects.create(title = "", featured_product = "")

    # # ! Updating the collections
    # collection = Collection.objects.get(pk=11)
    # collection.featured_product = None
    # collection.save()

    # Another way of updating the items in the objects
    # ! Using the filter because I want to update the specific collection 11 not all collections 
    # Collection.objects.filter(pk=11).update(featured_product = None)

    # ! Deleting objects

    # collection = Collection(pk = 11)
    # collection.delete()
    # Collection.objects.filter(id__gt=11).delete()

    # ! Transactions
    # ! All changes should be set together if any changes got error
    # ! Then all changes should be rolled back
    # ! I want both these transactions to in one go and no one should be failed 
    # with transaction.atomic():
    #     #By this method, with bloack we have more control over the code 
    #     # instead of using decorator on function we can make specific code for transactions

    #     order = Order()
    #     order.customer_id = 1
    #     order.save()

    #     item = OrderItem()
    #     item.order = order
    #     item.product_id = 1
    #     item.quantity = 1
    #     item.unit_price = 10
    #     item.save()

    # ! executing Raw SQL Queries 
    # ! Sometimes ORM make operations very complicated 
    # ! So instead of that sometimes we use direct RAW SQL queries

    #Every manager have raw method for executing raw sql queries
    #Using this appraoach if we really daeling with complex queries
    queryset = Product.objects.raw('Select * FROM store_product')
    #Here we dont have filter and annotae method 
    
    # ! dIFFERENT APPRoach for using sql queries
    # Here we have no limitation and can use any method
    # cursor = connection.cursor()
    # cursor.execute('')  
    # cursor.close()

    # ! Now instead of using the this we can use With statement better approac
    # with connection.cursor as cursor:
    #     cursor.execute()

    # ! We can also executing store procedures
    # with connection.cursor as cursor:
        # ! So here get_customers is store_procedure and inm array parameters to that
        # ! Store procedure is actuall used to reuse the code again and again just
        # ! byu calling that
        # cursor.callproc('get_customers', [1,2,'a '])

    
    return render( request, 'hello.html',{"name": "Hussain", "results":list(query_set)
         }

        )
