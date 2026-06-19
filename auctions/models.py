from django.conf import settings
from django.db import models
from django.utils import timezone

class Listing(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPELETED = "completed", "Completed"
        CANCELED = "canceled", "Canceled"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listings",
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    end_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="won_listings",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        return timezone.now() >= self.end_time
    
    def close_if_expired(self):
        if self.status == self.Status.ACTIVE and self.is_expired:
            highest_bid = self.bids.order_by('-amount').first()
            if highest_bid:
                self.winner = highest_bid.bidder
                self.current_price = highest_bid.amount
            self.status = self.Status.COMPLETED
            self.save(update_fields=['status', 'winner', 'current_price'])
        return self
            

# Create your models here.
