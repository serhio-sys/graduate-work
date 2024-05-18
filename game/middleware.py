import random
from django.http import HttpRequest, HttpResponseForbidden
from django.shortcuts import reverse as reverse_lazy
from django.contrib.auth import get_user_model
from django.conf import settings


class EffectMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def process_view(self, request, view_func, view_args, view_kwargs): # pylint: disable=W0613
        paths_to_disable_middlewares = [reverse_lazy("fight"), reverse_lazy("dungeon_enemy")]

        if request.path in paths_to_disable_middlewares:
            return None

        if request.user.is_authenticated and request.user.enemy is None:
            if request.user.health >= 100:
                return None

            rand = random.randint(0, 10)
            if rand + request.user.health > 100:
                request.user.health = 100
            else:
                request.user.health += rand
            request.user.save(update_fields=['health'])

        return None

    def __call__(self, request: HttpRequest):
        response = self.get_response(request)
        return response


class CustomUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Fetch the user with related fields
        if request.user.is_authenticated:
            user = get_user_model().objects.select_related('weapon2_equiped','armor_equiped',
                                                           'weapon_equiped','dungeon', 'enemy')
            request.user = user.get(pk=request.user.pk)

        response = self.get_response(request)
        return response
    
class AdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            ip = AdminMiddleware.__get_client_ip__(request)  
            if request.GET.get("token") == settings.SECRET_ADMIN_TOKEN and ip not in settings.ALLOWED_ADMIN_IPS:
                settings.ALLOWED_ADMIN_IPS.append(ip)
            if ip not in settings.ALLOWED_ADMIN_IPS:
                return HttpResponseForbidden("<h1><center>Access to the admin panel is restricted to authenticated users.</center></h1><h2><center>Forbidden 403</center></h2>")
        response = self.get_response(request)
        return response

    @staticmethod
    def __get_client_ip__(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip