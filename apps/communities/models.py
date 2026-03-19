from django.db import models
from django.conf import settings
from core.models import CoreModel
import random
import string

class Community(CoreModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    join_code = models.CharField(max_length=12, unique=True, editable=False)
    
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_communities')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='communities')
    
    class Meta:
        verbose_name_plural = "Communities"

    def save(self, *args, **kwargs):
        if not self.join_code:
            self.join_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12)).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
