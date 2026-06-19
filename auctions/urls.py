from django.urls import path
from .views import ListingCreateView, ListingDetailView, BidCreateView, ListingBidHistoryView

urlpatterns = [
    path('listings/', ListingCreateView.as_view(), name='listing-create'),
    path('listings/<int:pk>/', ListingDetailView.as_view(), name='listing-detail'),
    path('bids/', BidCreateView.as_view(), name='bid-create'),
    path('listings/<int:listing_id>/bids/', ListingBidHistoryView.as_view(), name='listing-bids'),
]