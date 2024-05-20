import json
import random
import datetime
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.template.response import TemplateResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.templatetags.static import static
from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.forms import model_to_dict
from users.models import NewUser
from .models import Weapon, Armor, Effect, Enemy, DungeonLvl
from .logs import get_text_effect, INSTRUCTION_LOGS
from .forms import AttackForm


def get_instructions_page(request: HttpRequest):
    step = int(request.GET.get("step", 0))
    texts = INSTRUCTION_LOGS.get(step, None)
    if texts is None:
        texts = INSTRUCTION_LOGS.get(0)
    prev_page = reverse("instruction") + "?step=" + str((step - 1) if step != 0 else 0)
    next_page = reverse("instruction") + "?step=" + str((step + 1)) \
        if INSTRUCTION_LOGS.get(step + 1, None) is not None \
        else reverse("finished-instruction")
    return render(request=request, template_name="game/instruction.html",
                  context={"prev": prev_page, "text": texts, "next": next_page})


def get_with_user_context(request: HttpRequest, template_name: str) -> TemplateResponse:
    user = request.user
    return TemplateResponse(request=request, template=template_name, context={'user': user})


def post_church(request: HttpRequest) -> HttpResponse:
    if request.user.balance < 10:
        return render(request=request, template_name="game/church_success.html",
                      context={"head": _("Недостатньо коштів на вашому рахунку")})
    if Effect.objects.filter(user=request.user, is_church_ef=True).exists():
        return redirect(reverse("church_loc") + "?msg=Ви вже робили пожертвування.")
    effects = Effect.objects.filter(user__isnull=True, is_church_ef=True)
    effect = effects[random.randint(0, len(effects) - 1)]
    kwargs = model_to_dict(effect, exclude=['id'])
    user_effect = Effect(**kwargs)
    user_effect.user = request.user
    user_effect.deleted_time = datetime.datetime.now() + datetime.timedelta(minutes=1)
    request.user.balance -= 10
    request.user.save()
    user_effect.save()
    return render(request=request, template_name="game/church_success.html",
                  context={"head": _("Свята пожертва."),
                           "msg": _("Ви отримали ефект святої пожертви.")})


def post_equip_armor(request: HttpRequest) -> JsonResponse:
    data = json.loads(request.body)
    if data.get('dequip'):
        request.user.armor_equiped = None
        request.user.save()
        return JsonResponse("success", safe=False, status=200)
    try:
        armor = Armor.objects.get(pk=data.get('pk'))
    except Armor.DoesNotExist:
        return JsonResponse({"error": Armor.DoesNotExist})
    if request.user.weapon2_equiped:
        request.user.weapon2_equiped = None
    request.user.armor_equiped = armor
    request.user.save()
    return JsonResponse("success", safe=False, status=200)


def post_equip_weapon(request: HttpRequest) -> JsonResponse:
    data = json.loads(request.body)
    if data.get('dequip') is not None:
        if int(data.get('dequip')) == 1:
            request.user.weapon_equiped = None
            request.user.save()
            return JsonResponse("success", safe=False, status=200)
        if int(data.get('dequip')) == 2:
            request.user.weapon2_equiped = None
            request.user.save()
            return JsonResponse("success", safe=False, status=200)
    else:
        try:
            weapon = Weapon.objects.get(pk=data.get('pk'))
        except Weapon.DoesNotExist:
            return JsonResponse({"error": Weapon.DoesNotExist})
        if request.user.weapon_equiped:
            if request.user.armor_equiped:
                request.user.armor_equiped = None
            request.user.weapon2_equiped = weapon
        else:
            request.user.weapon_equiped = weapon
        request.user.save()
    return JsonResponse("success", safe=False, status=200)


def get_buy_armor(request: HttpRequest, pk: int) -> HttpResponse:
    user = request.user
    item = Armor.objects.get(pk=pk, user__isnull=True)
    kwargs = model_to_dict(item, exclude=['id'])
    if user.balance < item.balance:
        return render(request, 'game/shop_err.html',
                      context={"msg": _("Не вистачає коштів")})
    if (user.agility < item.req_agility
            or user.strength < item.req_strength
            or item.lvl > request.user.lvl):
        return render(request, 'game/shop_err.html',
                      context={"msg": _("Недостатньо атрибутів для цього предмету")})
    user_armors = list(user.armor_set.values_list('name', flat=True).distinct())
    if item.name in user_armors:
        return render(request,
                      'game/shop_err.html',
                      context={"msg": _("Цей предмет вже є у вас в інвентарі.")})
    user.balance -= item.balance
    new_armor = Armor(**kwargs)
    new_armor.user = user
    new_armor.save()
    user.save()
    return render(request, template_name="game/shop_success.html")


def get_buy_weapon(request: HttpRequest, pk: int) -> HttpResponse:
    user = request.user
    item = Weapon.objects.get(pk=pk, user__isnull=True)
    if user.balance < item.balance:
        return render(request, 'game/shop_err.html',
                      context={"msg": _("Не вистачає коштів")})
    if (user.agility < item.req_agility
            or user.strength < item.req_strength
            or item.lvl > request.user.lvl):
        return render(request, 'game/shop_err.html',
                      context={"msg": _("Недостатньо атрибутів для цього предмету")})
    kwargs = model_to_dict(item, exclude=['id'])
    user_weapons = list(user.weapon_set.values_list('name', flat=True).distinct())
    if item.name in user_weapons:
        return render(request, 'game/shop_err.html',
                      context={"msg": _("Цей предмет вже є у вас в інвентарі.")})
    user.balance -= item.balance
    new_weapon = Weapon(**kwargs)
    new_weapon.user = user
    new_weapon.save()
    user.save()
    return render(request, template_name="game/shop_success.html")


def get_inventory_classview(request: HttpRequest, template_name: str):
    user = request.user
    weapons = user.weapon_set.exclude(
        id__in=[user.weapon_equiped_id, user.weapon2_equiped_id]
    )
    armors = user.armor_set.exclude(id=user.armor_equiped_id)
    context = {'user': user, 'armors': armors, 'weapons': weapons}
    return render(request=request, template_name=template_name, context=context)


def get_select_classview(request: HttpRequest, template_name: str) -> HttpResponse:
    if request.user.role is not None:
        return redirect('main_loc')
    classes = [
        {
            "name": "agility",
            "img": request.build_absolute_uri('/static/img/classes/agility.png'),
            "visual_name": _("Ловкач"),
            "desc": _(
                "Головний атрибут: Спритність.\n Якщо супротивник дуже повільний і "
                "буде ловити гав, то є можливість зробити подвійну атаку.\n Особливість:"
                "можливість ухилитися від атаки та контр атакувати.")
        },
        {
            "name": "strength",
            "img": request.build_absolute_uri('/static/img/classes/strength.png'),
            "visual_name": _("Силач"),
            "desc": _(
                "Головний атрибут: Сила.\n Чим більша сила, тим більше"
                " болю може зазнати супротивник.\n Особливість: наносити тяжкі поранення.")
        }
    ]
    return render(request=request, template_name=template_name, context={"classes": classes})


def post_select_classview(request: HttpRequest):
    if request.POST['role'] is not None:
        request.user.role = request.POST['role']
        request.user.save()
    else:
        return redirect('select_class')

    return redirect("instruction")


class BasedDungeon:
    def __init__(self) -> None:
        self.dungeon = None
        self.map_data = []
        self.x, self.y = 0, 0
        self.points = self.get_start_points()

    def get_end_points(self) -> list[int]:
        for i in enumerate(self.map_data):
            for j in range(len(i[1])):
                if self.map_data[i[0]][j]["pos"] == 5:
                    return [i[0], j]
        return [0, 2]

    def get_start_points(self) -> list[int]:
        for i in enumerate(self.map_data):
            for j in range(len(i[1])):
                if self.map_data[i[0]][j]["pos"] == 2:
                    return [i[0], j]
        return [0, 2]

    def get_point_reverse(self, x: int, y: int) -> str:
        if x < 0 or y < 0:
            return None
        try:
            if self.map_data[x][y]["pos"] == 1 or self.map_data[x][y]["pos"] == 2:
                return reverse("dungeon") + f"?x={x}&y={y}"
            if self.map_data[x][y]["pos"] == 3:
                return reverse("dungeon_tresure") + f"?x={x}&y={y}"
            if self.map_data[x][y]["pos"] == 4:
                return reverse("dungeon_enemy") + f"?x={x}&y={y}"
            if self.map_data[x][y]["pos"] == 5:
                return reverse("dungeon_boss") + f"?x={x}&y={y}"
        except IndexError:
            pass
        return None

    def initial_points(self, request: HttpRequest, user: NewUser) -> bool:
        leave = False
        self.x, self.y = int(request.GET.get("x", request.session.get("x", 0))), \
            int(request.GET.get("y", request.session.get("y", 0)))
        self.dungeon = DungeonLvl.objects.get(lvl=user.current_dungeon)
        with open(settings.BASE_DIR + self.dungeon.map.url, 'r', encoding='utf-8') as f:
            self.map_data = json.load(f)
        if self.map_data[self.x][self.y]["pos"] == 0:
            self.x, self.y = self.points[0], self.points[1]
        if self.map_data[self.x][self.y]["pos"] == 2:
            leave = True
        self.map_data[self.x][self.y]["pos"] = 6
        return leave

    def get_based_response(self, request: HttpRequest) -> TemplateResponse | HttpResponseRedirect:
        response = get_with_user_context(request=request,
                                         template_name=self.template_name)
        can_leave = self.initial_points(request=request, user=response.context_data['user'])
        try:
            if (self.x > request.session["x"] + 1 or
                    self.x < request.session["x"] - 1 or
                    self.y > request.session["y"] + 1 or
                    self.y < request.session["y"] - 1):
                return redirect(self.get_point_reverse(request.session["x"], request.session["y"]))
        except KeyError:
            pass
        moves = {"a": self.get_point_reverse(self.x + 1, self.y),
                 "l": self.get_point_reverse(self.x, self.y + 1),
                 "r": self.get_point_reverse(self.x, self.y - 1),
                 "b": self.get_point_reverse(self.x - 1, self.y)}
        response.context_data.update(moves)
        response.context_data['map'] = self.map_data
        response.context_data['can_leave'] = can_leave
        if self.points[0] == self.x and self.points[1] == self.y:
            response.context_data['img'] = static(self.map_data[self.x][self.y]["img"])
        else:
            response.context_data['img'] = static(self.map_data[self.x][self.y]["img"])
        request.session["x"], request.session["y"] = self.x, self.y
        return response


class BasedFight:

    def __init__(self) -> None:
        self.dungeon = None
        self.is_winner = None
        self.logs = []
        self.patterns = ['head', 'leg', 'body']

    def initial_enemy(self, user: NewUser):
        if user.enemy is None:
            enemies = Enemy.objects.filter(dungeon__lvl=user.current_dungeon, is_boss=False)
            enemy = enemies[random.randint(0, len(enemies) - 1)]
            user.enemy = Enemy.objects.create(
                **model_to_dict(enemy, exclude=['id', 'dungeon',
                                                'weapon_equiped',
                                                'weapon2_equiped',
                                                'armor_equiped'])
            )
            if enemy.weapon_equiped is not None:
                user.enemy.weapon_equiped = Weapon.objects.get(pk=enemy.weapon_equiped.pk)
            if enemy.weapon2_equiped is not None:
                user.enemy.weapon2_equiped = Weapon.objects.get(pk=enemy.weapon2_equiped.pk)
            if enemy.armor_equiped is not None:
                user.enemy.armor_equiped = Armor.objects.get(pk=enemy.armor_equiped.pk)

            user.save(update_fields=['enemy'])

    @staticmethod
    def apply_effect(effect_name: str, whom: NewUser | Enemy, duration_min: int) -> None:
        try:
            effect = Effect.objects.filter(name=effect_name, user__isnull=True, enemy__isnull=True).first()
        except Effect.DoesNotExist:
            return
        en_effect = Effect(**model_to_dict(effect, exclude=['id']))
        en_effect.deleted_time = datetime.datetime.now() + datetime.timedelta(minutes=duration_min)
        setattr(en_effect, 'user' if isinstance(whom, NewUser) else 'enemy', whom)
        if en_effect.user is not None or en_effect.enemy is not None:
            en_effect.save()

    def get_entity_effect(self, who: NewUser | Enemy, whom: NewUser | Enemy) -> None:
        is_whom_user = isinstance(whom, NewUser)

        if is_whom_user and whom.effect_set.all().count() > 3:  # pylint: disable=R1705
            return
        elif not is_whom_user and whom.effect_enemy.all().count() > 3:
            return

        if who.role in ["agility", "shooter"] and random.randint(0, 100) < 5:
            self.apply_effect("Кровотеча", whom, 2)
            self.logs.append(get_text_effect(who.get_name(), whom.get_name(), "bliding"))
        elif who.role == "strength" and random.randint(0, 100) < 8:
            self.apply_effect("Перелом кістки", whom, 2)
            self.logs.append(get_text_effect(who.get_name(), whom.get_name(), "bones"))

    def attack(self, request: HttpRequest, who: NewUser | Enemy, whom: NewUser | Enemy) -> int:
        form = AttackForm(request.POST)
        if form.is_valid():
            rnd = random.randint(0, len(self.patterns) - 1)
            total_dmg = who.return_all_damage_taken()
            total_defence = whom.return_all_defence()
            attack = round(total_dmg - total_defence if total_defence < total_dmg else 1)
            if isinstance(who, NewUser):
                if form.cleaned_data['attack'] != self.patterns[rnd]:
                    if whom.health - attack > 0:
                        whom.health -= attack
                    else:
                        whom.health = 0
                        self.is_winner = True
                else:
                    attack = 0
            else:
                if self.patterns[rnd] != form.cleaned_data['defence']:
                    if whom.health - attack > 0:
                        whom.health -= attack
                    else:
                        whom.health = 0
                        self.is_winner = False
                else:
                    attack = 0
            self.get_entity_effect(who, whom)
            whom.save(update_fields=['health'])
        else:
            attack = who.return_all_damage_taken()
            if whom.health - attack > 0:
                whom.health -= attack
            else:
                whom.health = 0
                self.is_winner = False
            whom.save(update_fields=['health'])
        return attack

    def generate_response(self, user: NewUser, log: list[str]):
        if self.is_winner is None:
            response = JsonResponse({
                "enemy_hp": user.enemy.health,
                "user_hp": user.health,
                "user_stats": user.get_summary_stats(),
                "enemy_stats": user.enemy.get_summary_stats(),
                "winner": self.is_winner,
                "log": log
            }, status=200)
        else:
            response = JsonResponse({
                "winner": self.is_winner,
                "redirect_url": reverse("fight_results"),
            }, status=200)
        return response

    def finish_attack(self, request: HttpRequest, user: NewUser, logs: list[str]):
        if self.is_winner is True:
            request.session['winner'] = True
            user.exp += random.randint(10, 60)
            dungeon = DungeonLvl.objects.get(lvl=user.current_dungeon)
            user.balance += random.randint(dungeon.min_treasure,
                                           dungeon.max_treasure)
            user.save(update_fields=['exp', 'balance'])
            user.enemy.delete()
        elif self.is_winner is False:
            request.session['winner'] = False
            user.enemy.delete()
        response = self.generate_response(user, logs)
        return response


class ChangeDungeonView(BasedDungeon, LoginRequiredMixin, View):

    def initial_points(self, request: HttpRequest, page: str) -> str:
        request.session['is_boss'] = False
        self.x, self.y = int(request.GET.get("x", request.session.get("x", 0))), \
            int(request.GET.get("y", request.session.get("y", 0)))     
        current_dungeon = DungeonLvl.objects.get(lvl=request.user.current_dungeon)
        if self.get_end_points() == [self.x, self.y] and request.user.dungeon.lvl == 6:
            return reverse("dungeon") + f"?x={self.x}&y={self.y}"
        with open(settings.BASE_DIR + current_dungeon.map.url, 'r', encoding='utf-8') as f:
            current_map = json.load(f)   
        if current_map[self.x][self.y]["pos"] == 5:
            self.dungeon = DungeonLvl.objects.get(lvl=request.user.current_dungeon + 1)
            request.user.current_dungeon += 1
            with open(settings.BASE_DIR + self.dungeon.map.url, 'r', encoding='utf-8') as f:
                self.map_data = json.load(f)
            points = self.get_start_points()
        elif current_map[self.x][self.y]["pos"] == 2:
            self.dungeon = DungeonLvl.objects.get(lvl=request.user.current_dungeon - 1)
            with open(settings.BASE_DIR + self.dungeon.map.url, 'r', encoding='utf-8') as f:
                self.map_data = json.load(f)
            request.user.current_dungeon -= 1
            points = self.get_end_points()
        else:
            return reverse(page) + f"?x={self.x}&y={self.y}"
        request.user.save(update_fields=['current_dungeon'])
        request.session["x"], request.session["y"] = points[0], points[1]
        request.session['fight_posibility'] = 0
        if points == self.get_end_points():
            return reverse("dungeon_boss") + f"?x={points[0]}&y={points[1]}"
        return reverse("dungeon") + f"?x={points[0]}&y={points[1]}"


class BossFightView(BasedFight):

    def initial_enemy(self, user: NewUser):
        if user.enemy is None:
            enemies = Enemy.objects.filter(dungeon__lvl=user.dungeon.lvl, is_boss=True)
            enemy = enemies[random.randint(0, len(enemies) - 1)]
            user.enemy = Enemy.objects.create(
                **model_to_dict(enemies[random.randint(0, len(enemies) - 1)], exclude=['id', 'dungeon',
                                                                                       'weapon_equiped',
                                                                                       'weapon2_equiped',
                                                                                       'armor_equiped']))
            if enemy.weapon_equiped is not None:
                user.enemy.weapon_equiped = Weapon.objects.get(pk=enemy.weapon_equiped.pk)
            if enemy.weapon2_equiped is not None:
                user.enemy.weapon2_equiped = Weapon.objects.get(pk=enemy.weapon2_equiped.pk)
            if enemy.armor_equiped is not None:
                user.enemy.armor_equiped = Armor.objects.get(pk=enemy.armor_equiped.pk)
            user.save(update_fields=['enemy'])

    def finish_attack(self, request: HttpRequest, user: NewUser, logs: list[str]):
        if self.is_winner is True:
            request.session['winner'] = True
            user.exp += 50
            user.balance += user.dungeon.lvl * 500
            try:
                user.dungeon = DungeonLvl.objects.get(lvl=user.dungeon.lvl + 1) 
            except (DungeonLvl.DoesNotExist):
                user.dungeon = None            
            user.save(update_fields=['exp', 'balance', 'dungeon'])            
            user.enemy.delete()
            request.session['is_boss'] = True
        elif self.is_winner is False:
            request.session['winner'] = False
            user.enemy.delete()
        response = self.generate_response(user, logs)
        return response
    
    def generate_response(self, user: NewUser, log: list[str]):
        if self.is_winner is None:
            response = JsonResponse({
                "enemy_hp": user.enemy.health,
                "user_hp": user.health,
                "user_stats": user.get_summary_stats(),
                "enemy_stats": user.enemy.get_summary_stats(),
                "winner": self.is_winner,
                "log": log
            }, status=200)
        else:
            response = JsonResponse({
                "winner": self.is_winner,
                "redirect_url": reverse("final" if user.dungeon == 6 else "fight_results"),
            }, status=200)
        return response