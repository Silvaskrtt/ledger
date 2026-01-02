from django.shortcuts import redirect

class RedirectToLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Lista de URLs que podem ser acessadas sem login
        public_urls = [
            '/accounts/login/',
            '/accounts/signup/',
            '/accounts/logout/',
            '/admin/',
            '/static/',
            '/media/',
        ]
        
        # Se não está autenticado e não está em uma URL pública
        if not request.user.is_authenticated and request.path == '/':
            return redirect('account_login')
        
        response = self.get_response(request)
        return response