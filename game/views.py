import random
from django.shortcuts import redirect
from django.urls.exceptions import NoReverseMatch
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse, HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST, require_GET
from django.templatetags.static import static
from .services import get_select_classview, get_with_user_context, \
    post_select_classview, get_inventory_classview, \
    post_church, post_equip_armor, post_equip_weapon, get_buy_armor, get_buy_weapon, \
    BasedDungeon, BasedFight, reverse, get_instructions_page, \
    ChangeDungeonView, BossFightView
from .models import Weapon, Armor
from .forms import UserIncreaseStatsForm, AttackForm
from .logs import select_log
from .mixins import DungeonMixin, InstructionMixin


@login_required
@require_GET
def instruction_page(request: HttpRequest):
    return get_instructions_page(request=request)


@login_required
@require_GET
def instruction_finished_page(request: HttpRequest):
    request.user.is_started = True
    request.user.save(update_fields={'is_started'})
    return redirect(reverse("main_loc") + "?msg=Вітаємо! Навчання успішно завершено")


@login_required
@require_GET
def back_to_starter_page(request: HttpRequest, name: str):
    if name in ["inventory", "abilities"]:
        return redirect("home")
    request.user.current_position = name
    request.user.save(update_fields=['current_position'])
    return redirect("home")


@login_required
@require_GET
def get_start_game_page(request: HttpRequest):
    if not request.user.is_started:
        return redirect("instruction")
    if request.user.enemy is not None:
        return redirect("fight")
    if request.user.current_position is None:
        return redirect("main_loc")
    try:
        return redirect(request.user.current_position)
    except NoReverseMatch:
        return redirect("main_loc")


@login_required
@require_POST
def sell_weapon(request: HttpRequest, pk: int):
    try:
        item = Weapon.objects.get(pk=pk)
    except Weapon.DoesNotExist:
        return JsonResponse("error", safe=False, status=400)
    if item.user == request.user:
        if request.user.weapon_equiped == item or request.user.weapon2_equiped == item:
            return JsonResponse("error", safe=False, status=400)
        else:
            request.user.balance += item.balance // 2
            request.user.save()
            item.delete()
        return JsonResponse("success", safe=False, status=200)
    else:
        return JsonResponse("error", safe=False, status=400)


@login_required
@require_POST
def sell_armor(request: HttpRequest, pk: int):
    try:
        item = Armor.objects.get(pk=pk)
    except Weapon.DoesNotExist:
        return JsonResponse("error", safe=False, status=400)
    if item.user == request.user:
        if request.user.armor_equiped == item:
            return JsonResponse("error", safe=False, status=400)
        else:
            request.user.balance += item.balance
            request.user.save()
            item.delete()
        return JsonResponse("success", safe=False, status=200)
    else:
        return JsonResponse("error", safe=False, status=400)


@login_required
@require_POST
def equip_armor(request: HttpRequest):
    return post_equip_armor(request=request)


@login_required
@require_POST
def equip_weapon(request: HttpRequest):
    return post_equip_weapon(request=request)


@login_required
def buy_armor(request: HttpRequest, pk: int):
    return get_buy_armor(request=request, pk=pk)


@login_required
def buy_weapon(request: HttpRequest, pk: int):
    return get_buy_weapon(request=request, pk=pk)


class InventoryView(DungeonMixin, View):
    template_name = "game/inventory.html"

    def get(self, request: HttpRequest, name: str):
        if request.resolver_match.url_name != name:
            request.user.current_position = name
            request.user.save(update_fields=['current_position'])
        return get_inventory_classview(request=request, template_name=self.template_name)


class MainLocationView(DungeonMixin, View):
    template_name = "game/main.html"

    def get(self, request: HttpRequest):
        return get_with_user_context(request=request, template_name=self.template_name).render()


class CityLocation(DungeonMixin, View):
    template_name = "game/city_center.html"

    def get(self, request: HttpRequest):
        return get_with_user_context(request=request, template_name=self.template_name).render()


class OutskirtsLocation(DungeonMixin, View):
    template_name = "game/outskirts.html"

    def get(self, request: HttpRequest):
        return get_with_user_context(request=request, template_name=self.template_name).render()


class TavernLocation(DungeonMixin, View):
    template_name = "game/tavern.html"

    def get(self, request: HttpRequest):
        return get_with_user_context(request=request, template_name=self.template_name).render()


class ChurchLocation(DungeonMixin, View):
    template_name = "game/church.html"

    def get(self, request: HttpRequest):
        response = get_with_user_context(request=request, template_name=self.template_name)
        response.context_data.update({"error": request.GET.get("error", None)})
        return response.render()

    def post(self, request: HttpRequest):
        return post_church(request=request)


class ShopLocation(DungeonMixin, View):
    template_name = "game/shop.html"

    def get(self, request: HttpRequest):
        weapons = Weapon.objects.filter(user__isnull=True)
        armors = Armor.objects.filter(user__isnull=True)
        response = get_with_user_context(request=request, template_name=self.template_name)
        response.context_data.update({"weapons": weapons, "armors": armors})
        return response.render()


class SelectClassView(InstructionMixin, DungeonMixin, View):
    template_name = "game/select_class.html"

    def get(self, request: HttpRequest):
        return get_select_classview(request=request, template_name=self.template_name)

    def post(self, request: HttpRequest):
        return post_select_classview(request=request)


class AbilitiesView(DungeonMixin, View):
    template_name = "game/abilities.html"

    def get(self, request: HttpRequest):
        name = request.GET.get("name", "main_loc")
        if name != 'inventory':
            request.user.current_position = name
            request.user.save(update_fields=['current_position'])
        response = get_with_user_context(request=request, template_name=self.template_name)
        response.context_data.update({"form": UserIncreaseStatsForm(instance=request.user)})
        return response.render()

    def post(self, request: HttpRequest):
        form = UserIncreaseStatsForm(request.POST)
        response = get_with_user_context(request=request, template_name=self.template_name)
        if form.is_valid():
            difference_ag = form.cleaned_data['agility'] - request.user.agility
            difference_str = form.cleaned_data['strength'] - request.user.strength
            if (difference_ag + difference_str) <= request.user.upgrade_points:
                request.user.agility = form.cleaned_data['agility']
                request.user.strength = form.cleaned_data['strength']
                request.user.upgrade_points = form.cleaned_data['upgrade_points']
                request.user.save(update_fields=['upgrade_points', 'strength', 'agility'])
            response = get_with_user_context(request=request, template_name=self.template_name)
            response.context_data.update({"form": UserIncreaseStatsForm(instance=request.user)})
            return response.render()
        response.context_data.update({"form": form})
        return response.render()


class DungeonEnterenceView(LoginRequiredMixin, View):
    template_name = "game/dungeon/dungeon.html"

    def get(self, request: HttpRequest):
        return get_with_user_context(request=request, template_name=self.template_name).render()


class DungeonView(BasedDungeon, LoginRequiredMixin, View):
    template_name = "game/dungeon/dungeon_inside.html"

    def get(self, request: HttpRequest):
        if random.randint(1, 100) < request.session.get('fight_posibility', -1):
            request.session['enemy_first'] = True
            return redirect('fight')
        request.session['fight_posibility'] = -1
        response = self.get_based_response(request=request)
        if isinstance(response, HttpResponseRedirect):
            return response
        return response.render()


class DungeonEnemyView(DungeonView):
    template_name = "game/dungeon/dungeon_enemy.html"

    def get(self, request: HttpRequest):
        response = self.get_based_response(request=request)
        if isinstance(response, HttpResponseRedirect):
            return response
        response.template_name = self.template_name
        request.session['fight_posibility'] = 40
        request.session["x"], request.session["y"] = self.x, self.y
        response.context_data['img'] = static(self.map_data[self.x][self.y]["img"])
        return response.render()

    def post(self, request: HttpRequest):
        request.session['enemy_first'] = False
        return redirect("fight")


class FightResultsView(LoginRequiredMixin, View):
    template_name = "game/fight/fight_results.html"

    def get(self, request: HttpRequest):
        response = get_with_user_context(request=request, template_name=self.template_name)
        return response.render()


class FightView(BasedFight, LoginRequiredMixin, View):
    template_name = "game/fight/fight.html"

    def get(self, request: HttpRequest):
        response = get_with_user_context(request=request, template_name=self.template_name)
        self.initial_enemy(response.context_data['user'])
        request.session['fight_posibility'] = -1
        if request.session.get('enemy_first', False):
            self.attack(request, response.context_data['user'].enemy, response.context_data['user'])
            request.session['enemy_first'] = False
        response.context_data.update(
            {
                "form": AttackForm(),
                "enemy": response.context_data['user'].enemy,
                "effects": response.context_data['user'].get_summary_stats(),
                "enemy_effects": response.context_data['user'].enemy.get_summary_stats()
            }
        )
        return response.render()

    def post(self, request: HttpRequest):
        user = get_user_model().objects.select_related('weapon2_equiped', 'weapon_equiped', 'enemy') \
            .get(pk=request.user.pk)
        if user.enemy.role == "agility":
            if random.randint(0, 100) < 5:
                dmg = self.attack(request, user.enemy, user)
                self.logs.append(select_log(who=user.enemy.name,
                                            whom=user.username,
                                            attack_type="agility", dmg=dmg))
                response = self.finish_attack(request, user, self.logs)
                return response
        if self.request.user.role == "agility":
            if random.randint(0, 100) < 5:
                dmg = self.attack(request, user, user.enemy)
                self.logs.append(select_log(who=user.username,
                                            whom=user.enemy.name,
                                            attack_type="agility", dmg=dmg))
                response = self.finish_attack(request, user, self.logs)
                return response
        dmg = self.attack(request, user, user.enemy)
        self.logs.append(select_log(who=user.username,
                                    whom=user.enemy.name,
                                    dmg=dmg))
        dmg = self.attack(request, user.enemy, user)
        self.logs.append(select_log(who=user.enemy.name,
                                    whom=user.username,
                                    dmg=dmg))
        response = self.finish_attack(request, user, self.logs)
        return response


class DungeonBossView(DungeonView):
    template_name = "game/dungeon/dungeon_boss.html"
    defeted_template_name = "game/dungeon/dungeon_change.html"

    def get(self, request: HttpRequest):
        response = self.get_based_response(request=request)
        if isinstance(response, HttpResponseRedirect):
            return response
        if self.request.user.dungeon.lvl > self.request.user.current_dungeon:
            response.template_name = self.defeted_template_name
            return response.render()
        response.template_name = self.template_name
        request.session["x"], request.session["y"] = self.x, self.y
        response.context_data['img'] = static(f"img/locations/dungeon/dun{request.user.current_dungeon}/dun_boss.jpg")
        return response.render()

    def post(self, request: HttpRequest):
        return redirect("fight_boss")


class DungeonChangeView(ChangeDungeonView):
    def get(self, request: HttpRequest, page: str):
        url = self.initial_points(request, page)
        return redirect(url)


class BossFightView(FightView, BossFightView):
    pass

class FinalView(LoginRequiredMixin, View):

    template_name = "game/dungeon/final.html"

    def get(self, request: HttpRequest):
        response = get_with_user_context(request=request, template_name=self.template_name)
        return response