from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class MStockAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # List of URLs that don't require authentication
        public_urls = [
            reverse('mstock_trade:login'),
            reverse('mstock_trade:verify_otp'),
        ]

        # Check if the current path is a public URL
        if request.path in public_urls:
            return self.get_response(request)

        # Check if user has access token
        if not request.session.get('access_token'):
            messages.error(request, 'Please login to continue')
            return redirect('mstock_trade:login')

        return self.get_response(request) 