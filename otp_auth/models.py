# File: otp_auth/models.py
from django.db import models
from django.utils import timezone
import secrets

class EmailOTP(models.Model):
    email = models.EmailField(db_index=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)
    class Meta:
        db_table = 'email_otps'; ordering = ['-created_at']
        indexes = [models.Index(fields=['email', 'is_used', 'expires_at'])]
    def __str__(self): return f"{self.email} — {self.code}"
    @classmethod
    def issue(cls, email, ttl_minutes=10):
        code = f"{secrets.randbelow(1_000_000):06d}"
        return cls.objects.create(email=email.lower(), code=code,
            expires_at=timezone.now() + timezone.timedelta(minutes=ttl_minutes))
    def is_valid(self):
        return (not self.is_used and timezone.now() < self.expires_at and self.attempts < 5)
