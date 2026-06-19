from rest_framework import serializers
from .models import Listing

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