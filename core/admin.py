from django.contrib import admin
from store.admin import ProductAdmin
from tags.models import TaggedItem
from store.models import Product
from django.contrib.contenttypes.admin import GenericTabularInline 
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "usable_password", "password1", "password2", "email", "first_name", "last_name"),
            },
        ),
    )


#EXTTEMDING PLUGGABLEW APPS; 
#Decoupling apps in django
# ! Creating inline class for prpduct class
# ! to display the tags in products form
class TagInline(GenericTabularInline):
    model = TaggedItem
    autocomplete_fields = ["tag"]



class CustomProductAdmin(ProductAdmin):\
    # ! here we are displayiyng to select tags for product using inlines
    inlines = [TagInline]

# In custom we un-registering the Product and then directly registering CustomProductAdmin
# To get the effect of new app use for intyer-communicating two apps.
admin.site.unregister(Product)
admin.site.register(Product, CustomProductAdmin)
