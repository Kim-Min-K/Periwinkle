from django.shortcuts import redirect
from django.urls import reverse

class ApprovalRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_approved:
            # Define exempt paths
            exempt_paths = [
                reverse('accounts:approval_pending'),
                reverse('accounts:logout'),
                '/admin/'
            ]
            
            # Check if current path is exempt
            if not any(request.path.startswith(path) for path in exempt_paths):
                return redirect('accounts:approval_pending')
                
        return self.get_response(request)