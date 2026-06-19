from rest_framework import generics, permissions
from django.shortcuts import render

from .models import Listing
from .serializers import ListingSerializer
from vip.permissions import IsOwnerOrReadOnly


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

    def get_queryset(self):
        # Filter listings to only include those owned by the authenticated user
       obj = super(). get_object()
       obj.close_if_expired()
       return obj

# Create your views here.
