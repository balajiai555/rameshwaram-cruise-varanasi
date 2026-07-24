# File: accounts/managers.py
from django.contrib.auth.models import BaseUserManager
class UserManager(BaseUserManager):
    def create_user(self, email, full_name, password=None, phone=None):
        if not email: raise ValueError('Email required')
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, phone=phone)
        user.set_password(password); user.save(using=self._db); return user
    def create_superuser(self, email, full_name, password=None, phone=None):
        user = self.create_user(email, full_name, password, phone)
        user.is_staff = True; user.is_superuser = True
        user.save(using=self._db); return user

