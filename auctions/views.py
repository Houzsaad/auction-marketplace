from rest_framework import generics, permissions
from django.shortcuts import render

from .models import Listing
from .serializers import ListingSerializer
from vip.permissions import IsOwnerOrReadOnly

from .models import Listing, Bid
from .serializers import ListingSerializer, BidSerializer

class ListingCreateView(generics.CreateAPIView):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter listings to only include those owned by the authenticated user
        listings = Listing.objects.all()
        for listing in listings:
            listing.close_if_expired()
        return listings
    
class ListingDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self):
        # Filter listings to only include those owned by the authenticated user
       obj = super().get_object()
       obj.close_if_expired()
       return obj




class BidCreateView(generics.CreateAPIView):
    serializer_class = BidSerializer
    permission_classes = [permissions.IsAuthenticated]

class ListingBidListView(generics.ListAPIView):
    serializer_class = BidSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        listing_id = self.kwargs['listing_id']
        return Bid.objects.filter(listing_id=listing_id).order_by('-amount')

# Create your views here.



