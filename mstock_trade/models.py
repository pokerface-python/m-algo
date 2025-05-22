from django.db import models
from django.contrib.auth.models import User

class Strategy(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Trade(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=20)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    side = models.CharField(max_length=4, choices=[('BUY', 'Buy'), ('SELL', 'Sell')], default='BUY')
    executed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('EXECUTED', 'Executed'),
        ('CANCELLED', 'Cancelled'),
        ('FAILED', 'Failed')
    ])

    def __str__(self):
        return f"{self.side} {self.quantity} {self.symbol} @ {self.price}"

# class Position(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     symbol = models.CharField(max_length=20)
#     quantity = models.IntegerField()
#     average_price = models.DecimalField(max_digits=10, decimal_places=2)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.quantity} {self.symbol} @ {self.average_price}"

# models.py
class Position(models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_id = models.IntegerField()
    trading_symbol = models.CharField(max_length=100)
    exchange = models.CharField(max_length=20)  # <-- ADD THIS
    average_price = models.FloatField()
    quantity = models.IntegerField()
    product = models.CharField(max_length=10, blank=True, null=True)  # <-- ADD THIS
    pnl = models.FloatField(default=0)
    m2m = models.FloatField(default=0)
    unrealized_pnl = models.FloatField(default=0)
    realized_pnl = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Order(models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_id = models.IntegerField()

    symbol = models.CharField(max_length=20)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    side = models.CharField(max_length=4, choices=[('BUY', 'Buy'), ('SELL', 'Sell')])
    order_type = models.CharField(max_length=10, choices=[
        ('MARKET', 'Market'),
        ('LIMIT', 'Limit'),
        ('STOP', 'Stop'),
        ('STOP_LIMIT', 'Stop Limit')
    ])
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('EXECUTED', 'Executed'),
        ('CANCELLED', 'Cancelled'),
        ('FAILED', 'Failed')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order_type} {self.side} {self.quantity} {self.symbol} @ {self.price}"

class APIKeys(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    api_key = models.CharField(max_length=100)
    api_secret = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"

    def __str__(self):
        return f"API Keys for {self.user.username}"

class Instrument(models.Model):
    instrument_token = models.CharField(max_length=50, unique=True)
    exchange_token = models.CharField(max_length=50)
    trading_symbol = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    last_price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    expiry = models.DateField(null=True, blank=True)
    strike = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    tick_size = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    lot_size = models.IntegerField(null=True, blank=True)
    instrument_type = models.CharField(max_length=50)
    segment = models.CharField(max_length=50)
    exchange = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['trading_symbol']
        indexes = [
            models.Index(fields=['trading_symbol']),
            models.Index(fields=['instrument_token']),
            models.Index(fields=['exchange']),
        ]

    def __str__(self):
        return f"{self.trading_symbol} ({self.exchange})" 