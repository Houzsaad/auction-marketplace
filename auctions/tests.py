from urllib import response

from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Bid, Listing

from django.test import TestCase

User = get_user_model()

class BaseAuctionTestCse(APITestCase):
    """set_up began here, two users (Owner & Bidder) and One ACTIVE LISTING"""

    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@gmail.com", full_name="Dopalo Temidayo", password="Test2026"
        )

        self.bidder = User.objects.create_user(
            email="bidder@gmail.com", full_name="Bidder Buyer", password="Test2026"
        )

        self.admin = User.objects.create_user(
            email="admin@admin.com", full_name="Jhon Doi", password="Test2026"
        )

        self.listing = Listing.objects.create(
            owner=self.owner,
            title="Testing Item",
            description="It's just for testing",
            starting_price=100,
            current_price=100,
            end_time=timezone.now() + timedelta(days=1)
        )

    def auth(self, user):
        """login as a given user and attach the token to the self.client"""
        response = self.client.post(
            reverse("login"),
            {"email": user.email, "password": "Test2026"},
        )
        token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

class AuthTest(APITestCase):
    def test_register_new_user(self):
        response = self.client.post(reverse("register"), {
            "email": "newuser@gmail.com", "full_name": "Friday Sunday", "password": "Test2026"
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="newuser@gmail.com").exists())

    def test_login_returns_token(self):
        User.objects.create_user(
            email="x@gmail.com", full_name="X User", password="Test2026"
        )
        self.assertEqual(response.status.code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)


    def test_logout_block_token(self):
        User.objects.create(email="logout@gmail.com", full_name="Logot User", password="Test2026")
        login = self.client.post(reverse("login"), {
            "email": "logot@gmail.com",
            "password": "Test2026"
        })
        access = login.data["access"]
        refresh = login.data["refresh"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout = self.client.post(reverse("logout"), {"refresh": refresh})
        self.assertSetEqual(logout.status_code, status.HTTP_205_RESET_CONTENT)
        

        retry = self.client.post(reverse("login_refresh"), {"refresh": refresh})
        self.assertEqual(logout.status_code, status.HTTP_401_UNAUTHORIZED)


class ListingPermissionsTest(BaseAuctionTestCse):
    def test_non_owner_cannot_update_listing(self):
        self.auth(self.bidder)
        response = self.client.put(
            reverse("listing-detail", args=[self.listing.id]),
            {"title": "Updated Title", "description": "Updated Description", "starting_price": 150, "current_price": 150, "end_time": timezone.now() + timedelta(days=2)}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_update_listing(self):
        self.auth(self.owner)
        response = self.client.patch(
            reverse("listing-detail", args=[self.listing.id]),
            {"title": "Update title"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ADMIN_can_update_listing(self):
        self.auth(self.admin)
        response = self.client.patch(
            reverse("listing-detail", args=[self.listing.id]),
            {"title": "Admin has Update tille"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_any_authenticated_can_view_listing(self):
        self.auth(self.bidder)
        response = self.client.patch(
            reverse("listing-detail", args=[self.listing.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class BiddingTests(BaseAuctionTestCse):
    def test_valid_bid_updates_current_price(self):
        self.auth(self.bidder)
        response = self.client.post(reverse("bid-create"), {
            "listing": self.listing.id, "amount": 200.00
        })
        self.asserEqual(response.status_code, status.HTTP_201_CREATED)

        self.listing.refresh_from_db()
        self.assertEqual(str(self.listing.current_price), 250.00)
        
    def test_bid_beloow_current_price(self):
        self.auth(self.bidder)
        response = self.client.post(reverse("bid-create"), {
            "listing": self.listing.id, "amount": 220.00
        })
        self.asserEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_owner_can_bid(self):
        self.auth(self.owner)
        response = self.client.post(reverse("bid-create"), {
            "listing": self.listing.id, "amount": 222.00
        })
        self.asserEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expired_listing_reject_bids(self):
        expired = Listing.objects.create(
            owner=self.owner,
            title="EXPIRED Item",
            description="It WA EXPIRED just for testing",
            starting_price=10,
            current_price=10,
            end_time=timezone.now() + timedelta(days=1)
        )
        self.auth(self.bidder)
        response = self.client.post(reverse("bid-create"), {
            "listing": expired.id, "amount": 11.00
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        expired.refresh_from_db()
        self.assertEqual(expired.status, Listing.Status.COMPLETED)

    def bid_history_ordered_by_nums(self):
        Bid.objects.create(listing=self.listing, bidder=self.bidder, amount=120)
        Bid.objects.create(listing=self.listing, bidder=self.bidder, amount=20)

        self.auth(self.bidder)
        response = self.client.get(
            reverse("listing-bid-history", args=[self.listing.id])
        )
        amounts = [bid["bids"] for bid in response.data]
        self.asserEqual(amounts, [200.00, 120.00])

class AuctionCompletionTests(BaseAuctionTestCse):
    def test_highest_bidder_wins_on_expirr(self):
        listing = Listing.objects.create(
            owner=self.owner,
            title="EXPIRED Item",
            description="It WA EXPIRED just for testing",
            starting_price=10,
            current_price=10,
            end_time=timezone.now() + timedelta(days=1)
        )
        Bid.objects.create(listing=self.listing, bidder=self.bidder, amount=120)
        Bid.objects.create(listing=self.listing, bidder=self.bidder, amount=20)

        listing.close_if_expired()
        listing.refresh_from_db()

        self.assertEqual(listing.status, Listing.Status.COMPLETED)
        self.assertEqual(listing.winner, self.admin)
        self.assertEqual(str(listing.current_price), 250)







# Create your tests here.
