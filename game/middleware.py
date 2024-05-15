import random
from django.http import HttpRequest
from django.shortcuts import reverse as reverse_lazy
from django.contrib.auth import get_user_model


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
