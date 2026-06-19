from rest_framework import serializers
from .models import Listing, Bid

class ListingSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id',
            'owner',
            'title',
            'description',
            'starting_price',
            'current_price',
            'end_time',
            'status',
            'winner',
            'created_at',
            'updated_at',
            'is_expired',
        ]
        read_only_fields = ['current_price', 'status', 'winner']

    def create(self, validated_data):
        # Set the current_price to starting_price when creating a new listing
        validated_data['owner'] = self.context['request'].user
        validated_data['current_price'] = validated_data['starting_price']
        return super().create(validated_data)



class BidSerializer(serializers.ModelSerializer):
    bidder = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Bid
        fields = [
            'id',
            'listing',
            'bidder',
            'amount',
            'created_at',
        ]
        read_only_fields = ['bidder', 'created_at']

    def validate(self, data):
        request = self.context['request']
        listing = data['listing']

        listing.close_if_expired() #lazy close check happen here tooo

        if listing.status != listing.Status.ACTIVE:
            raise serializers.ValidationError("This auction is no longer active.")

        if listing.owner == request.user:
            raise serializers.ValidationError("You cannot bid on your own Auction.")

        if data['amount'] <= listing.current_price:
            raise serializers.ValidationError(
                f"Bid must be higher than the current price ({listing.current_price})"
            )

        return data

    def create(self, validated_data):
        validated_data["bidder"] = self.context["request"].user
        bid = super().create(validated_data)

        #update the current price of the listing if the bid is valid
        listing = bid.listing
        listing.current_price = bid.amount
        listing.save(update_fields=["current_price"])

        return bid