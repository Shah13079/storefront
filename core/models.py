from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

# Note
# We should always create Abstract User in beganing of our projects
# we can just pass the class, but then it will not create problems
# later incase we want to use it.

class User(AbstractUser):
    
    email = models.EmailField(unique=True)
