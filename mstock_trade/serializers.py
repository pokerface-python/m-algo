from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Strategy, Trade, Position, Order

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = ('id',)

class StrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = Strategy
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class TradeSerializer(serializers.ModelSerializer):
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)

    class Meta:
        model = Trade
        fields = '__all__'
        read_only_fields = ('executed_at',)

class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

# Market Data Serializers
class MarketQuoteSerializer(serializers.Serializer):
    symbol = serializers.CharField()
    last_price = serializers.FloatField()
    change = serializers.FloatField()
    percent_change = serializers.FloatField()
    open = serializers.FloatField()
    high = serializers.FloatField()
    low = serializers.FloatField()
    volume = serializers.IntegerField()
    exchange = serializers.CharField()
    instrument_token = serializers.IntegerField()

class OptionChainSerializer(serializers.Serializer):
    calls = serializers.ListField(child=serializers.DictField())
    puts = serializers.ListField(child=serializers.DictField())
    future = serializers.DictField(required=False)
    spot = serializers.DictField(required=False)

class IntradayDataSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField()
    open = serializers.FloatField()
    high = serializers.FloatField()
    low = serializers.FloatField()
    close = serializers.FloatField()
    volume = serializers.IntegerField()

class FundSummarySerializer(serializers.Serializer):
    cash_balance = serializers.DictField()
    margin = serializers.DictField()
    bank_holding = serializers.FloatField()
    collaterals = serializers.FloatField()
    mtf_available_balance = serializers.FloatField()
    mtf_collateral = serializers.FloatField()
    mtf_utilize = serializers.FloatField()
    peak_margin = serializers.FloatField() 