from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Strategy, Trade, Position, Order
from .serializers import (
    StrategySerializer, TradeSerializer, PositionSerializer, OrderSerializer,
    MarketQuoteSerializer, OptionChainSerializer, IntradayDataSerializer,
    FundSummarySerializer
)
from .services import MStockAPIService

class StrategyViewSet(viewsets.ModelViewSet):
    queryset = Strategy.objects.all()
    serializer_class = StrategySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        strategy = self.get_object()
        try:
            api_service = MStockAPIService()
            result = api_service.execute_strategy(strategy)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class TradeViewSet(viewsets.ModelViewSet):
    queryset = Trade.objects.all()
    serializer_class = TradeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Trade.objects.filter(strategy__user=self.request.user)

class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Position.objects.filter(user=self.request.user)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

class MarketDataView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        symbols = request.query_params.getlist('symbols', [])
        if not symbols:
            return Response({'error': 'No symbols provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            api_service = MStockAPIService()
            quotes = api_service.get_market_quote_batch(symbols)
            serializer = MarketQuoteSerializer(quotes.get('data', {}).values(), many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class OptionChainView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        exchange = request.query_params.get('exchange')
        expiry = request.query_params.get('expiry')
        token = request.query_params.get('token')

        if not all([exchange, expiry, token]):
            return Response({'error': 'Missing required parameters'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            api_service = MStockAPIService()
            option_chain = api_service.get_option_chain_formatted(exchange, expiry, token)
            serializer = OptionChainSerializer(option_chain.get('data', {}))
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class IntradayDataView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        exchange = request.query_params.get('exchange')
        script_name = request.query_params.get('script_name')
        interval = request.query_params.get('interval', 'minute')

        if not all([exchange, script_name]):
            return Response({'error': 'Missing required parameters'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            api_service = MStockAPIService()
            intraday_data = api_service.get_intraday_data_formatted(exchange, script_name, interval)
            serializer = IntradayDataSerializer(intraday_data.get('data', {}).get('candles', []), many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class FundSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            api_service = MStockAPIService()
            fund_summary = api_service.get_fund_summary()
            serializer = FundSummarySerializer(fund_summary.get('data', {}))
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST) 