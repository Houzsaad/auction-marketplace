from django.urls import path
from .views import ListingCreateView, ListingDetailView

urlspatterns = [
    path('listings/', ListingCreateView.as_view(), name='listing-create'),
    path('listings/<int:pk>/', ListingDetailView.as_view(), name='listing-detail'),
]