from django.urls import path, include
from . import views
from rest_framework_nested import routers

# ! This how we use nested routers

router = routers.DefaultRouter()
router.register("products", views.ProductViewSet, basename="products")
router.register("collections", views.CollectionViewSet)
router.register('carts',views.CartViewSet)
router.register('customers',views.CustomerViewSet)
router.register('orders',views.OrderViewSet,basename="orders")
# router.register('items',views.CartItemsSet)

products_router = routers.NestedDefaultRouter(router, "products", lookup="product")
products_router.register("reviews", views.ReviewViewSet, basename='product-reviews')

carts_router = routers.NestedDefaultRouter(router,"carts", lookup="cart")
carts_router.register("items",views.CartItemsViewSet, basename="cart-items")

urlpatterns = router.urls + products_router.urls + carts_router.urls

# ! This is how we use souters
# router = SimpleRouter()
# router.register("products", views.ProductViewSet)
# router.register("collections", views.CollestionViewSet)
# urlpatterns = router.urls

# ! This is how we can set router if urlpatterns have some other patterns available otherwise above
# urlpatterns = [
    # path("", include(router.urls))
    # path("products/",views.ProductList.as_view()),
    # path("products/<int:pk>",views.ProductDetail.as_view()),
    # path("collections/<int:pk>",views.CollectionDetail.as_view(), name = "collection-detail"),
    # path("collections",views.CollectionList.as_view(), name = "collections")

# ]

# ! # URL Configuration for simple method based views
# urlpatterns = [
#     path("products/",views.product_list),
#     path("products/<int:id>",views.product_detail),
#     path("collections/<int:id>",views.collection_detail, name = "collection-detail"),
#     path("collections",views.collection_list, name = "collections")

# ]
# DefaultRouter This Router have two other feeatures
