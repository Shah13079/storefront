from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer 
from rest_framework import serializers
from store.models import Customer 

class UserCreateSerializer(BaseUserCreateSerializer):
    
    # def save(self, **kwargs):
    #     user = super().save(**kwargs)
    #     Customer.objects.create(user = user)

    class Meta(BaseUserCreateSerializer.Meta):
        fields = ["id","username","password","email","first_name","last_name"]
        
class TheUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = ["id","first_name","last_name","username","email"]
        
