from typing import Any
from django.contrib import admin, messages
# Register your models here
from django.contrib import admin
from django.db.models.query import QuerySet
from . import models
from django.db.models import Count
from django.utils.html import format_html, urlencode
from django.urls import reverse


# ! so here we are making a custom filter on products in admin panel
# ! the lookups and queryset are components of SimpleListFilter which
# ! Is the part of django admin framework
class InventoryFilter(admin.SimpleListFilter):
    title = "inventory"
    parameter_name = "inventory"
    # ! lookups defines the available filter options.
    def lookups(self, request, model_admin):
        return [
            ("<10", "Low") ]
    # ! queryset filters the data based on the selected option.
    def queryset(self, request: Any, queryset: QuerySet[Any]) -> QuerySet[Any] | None:
        if self.value() == '<10':
            return queryset.filter(inventory__lt = 10)


class CollectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'products_count']
    search_fields = ['title']
    def products_count(self, collection):
        # ! Going from one page to another page using href in django admin
        # reverse('admin:app_model_page')
        # ! That list of products in the admin page is called changelist
        # url = reverse('admin:store_product_changelist')
        # ! Now lets applying the filters, to show only selected collection products
        url = ( reverse('admin:store_product_changelist')
               + '?'
               + urlencode({
                   'collection__id':str(collection.id),
               }))
        return format_html('<a href="{}">{}</a>',url ,collection.products_count)
    
    def get_queryset(self, request):
        #This is the base implementation where we are going
        # To the base class and calling get_queryset method
        return super().get_queryset(request).annotate(
            products_count = Count('products')
        )
    
admin.site.register(models.Collection, CollectionAdmin)



#Another wat of registeringh the models in class
@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    
    # ! the only fields we want to show in admin form
    # fields = ['']
    # ! The fields we want to exclude from form
    # exclude = ['']
    # ! To read only not editable fields
    # readonly_fields = ['']
    # ! prepopulated fields, creating slugs
    prepopulated_fields = {
        "slug": ["title"]
    }
    # ! Auto complete fields 
    autocomplete_fields = ['collection']
    search_fields = ['title']
    # ! So here I passed the method as string which I made in this class
    actions = ["clear_inventory"]
    list_display = ['title', 'unit_price', 'inventory_status', 'collection_title']
    list_editable = ['unit_price']
    list_per_page = 10
    list_filter = ["collection", "last_update", InventoryFilter]

    # By this method we are fetching the fields of other models 
    # By Preloading which reduce the queries to db for better performance
    list_select_related = ["collection"]

    #! This is how to make computed columns to database 
    @admin.display(ordering='inventory') 
    def inventory_status(self, product):
        if product.inventory < 10:
            return "Low"
        else:
            return "Ok"
    
    # ! Creating custom actions
    @admin.action(description='clear inventory')
    def clear_inventory(self, request, queryset):
        updates_count = queryset.update(inventory = 0)
        self.message_user(request,
                          f"{updates_count} Products were successfully updated",
        # ! If I uncomment this below it will dispaly error red meesage
                        #   messages.ERROR
        )
    
    #I used this to display the specific field of collection model which is title
    # And this could be used to display 
    def collection_title(self, product):
        return product.collection.title

@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user__first_name', 'last_name', 'membership']
    list_editable = ['membership']
    list_per_page = 10
    list_select_related = ['user']
    ordering = ['user__first_name','user__last_name']

    # ! This is how we can make search by search engine in admin
    # search_fields = ["first_name", "last_name"]
    # ! Here is another way
    # ! This will throw names starts with any letter in search
    # search_fields = ["first_name__startswith", "last_name__startswith"]
    # ! Here is another way that means search will not be case sensitive istartwith
    search_fields = ["first_name__istartswith", "last_name__istartswith"]


class OrderItemInline(admin.TabularInline):
    autocomplete_fields = ["product"]
    min_num = 1
    max_num = 10
    model = models.OrderItem
    # ! It means not editable and no pre- rows there in table
    extra = 0

@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):

    # Here we are calling model name directly instead of
    # calling its field, and model is returning str of firt name last name 
    # combine

    list_display = ["id", 'placed_at', "customer"]
    list_per_page = 10
    autocomplete_fields = ["customer"]
    # ! This means that in "Order" model admin panel; we are displaying table of Orders placed
    # ! Which belongs to another model OrderItem
    # ! We can also manage them; populate them. (children inlines)
    inlines = [OrderItemInline]

    def customer_first_name(self, order):
        return order.customer.first_name

