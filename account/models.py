from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

# Create your models here.
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, *args, **kwargs):
        if not email:
            raise ValueError('Please, provide an email address')
        if not password:
            raise ValueError('Please, provide a password')
        
        try:
            user = self.model(
                email=self.normalize_email(email),
                *args,
                **kwargs
            )
            user.set_password(password)
            user.save()
            return user
        except:
            raise ValueError('Please, try again.')
        
    def create_superuser(self, email, password = None, *args, **kwargs):
        try:
            user = self.create_user(
                email,
                password = password,
                is_admin=True,
                is_superuser=True,
                is_staff=True,
                *args,
                **kwargs
            )
            return user
        except:
            raise ValueError('An error occurred. Please,try again.')

            
        
class CustomUser(AbstractUser):
    username = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    
    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'email'
    
    objects = CustomUserManager()