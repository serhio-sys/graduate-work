import random
from django.utils import timezone
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.templatetags.static import static
from channels.db import database_sync_to_async


class BaseShopEntity(models.Model):
    name = models.CharField("NAME",
                            max_length=30)
    img = models.CharField("IMG", max_length=100)
    balance = models.IntegerField("SUM")
    lvl = models.IntegerField("LVL")
    req_agility = models.IntegerField("REQUIRED AGILITY")
    req_strength = models.IntegerField("REQUIRED STRENGTH")
    user = models.ForeignKey("users.NewUser",
                             verbose_name="Owner",
                             default=None,
                             null=True,
                             blank=True,
                             on_delete=models.CASCADE)

    def get_img(self):
        return static('img/' + self.img)

    def get_sell_sum(self):
        return self.balance // 2

    def __str__(self) -> str:
        return str(self.name)

    class Meta:
        abstract = True


class DungeonLvl(models.Model):
    lvl = models.PositiveIntegerField("DUNGEON LVL", unique=True, primary_key=True)
    is_boss_killed = models.BooleanField(default=False)
    min_treasure = models.IntegerField("MIN")
    max_treasure = models.IntegerField("MAX")
    map = models.FileField(upload_to="maps/", default="maps/map1.json")
    unlock_lvl = models.PositiveIntegerField("LVL FOR UNLOCK BOSS")


class Weapon(BaseShopEntity):
    damage = models.IntegerField("DAMAGE+")

    def get_absolute_url(self):
        return reverse("buy_w", kwargs={"pk": self.pk})


class Armor(BaseShopEntity):
    armor_value = models.IntegerField("AROMOR+")

    def get_absolute_url(self):
        return reverse("buy_a",
                       kwargs={"pk": self.pk})


class Effect(models.Model):
    name = models.CharField("NAME", max_length=50, default="")
    desc = models.TextField("Desc")
    is_positive = models.BooleanField("IS_POSITIVE", default=True)
    is_church_ef = models.BooleanField("IS CHURCH EFFECT", default=False)
    agility = models.IntegerField("AGILITY", default=1)
    strength = models.IntegerField("STRENGTH", default=1)
    user = models.ForeignKey("users.NewUser",
                             default=None,
                             null=True,
                             blank=True,
                             on_delete=models.CASCADE)
    enemy = models.ForeignKey("Enemy",
                              default=None,
                              null=True,
                              blank=True,
                              on_delete=models.CASCADE,
                              related_name='effect_enemy')
    deleted_time = models.DateTimeField("DELETED TIME",
                                        default=None,
                                        null=True,
                                        blank=True)


class BaseEntity(models.Model):
    health = models.IntegerField("HP", default=100)
    attack = models.IntegerField("ATTACK", default=11)
    defence = models.IntegerField("ARMOR", default=0)
    agility = models.IntegerField("AGILITY", default=1)
    strength = models.IntegerField("STRENGTH", default=1)
    role = models.CharField("ROLE", default=None, max_length=40, blank=True, null=True)
    weapon_equiped = models.ForeignKey('game.Weapon',
                                       verbose_name="WEAPON",
                                       default=None,
                                       null=True,
                                       blank=True,
                                       on_delete=models.SET_NULL)
    armor_equiped = models.ForeignKey('game.Armor',
                                      verbose_name="ARMOR",
                                      default=None,
                                      null=True,
                                      blank=True,
                                      on_delete=models.SET_NULL)
    weapon2_equiped = models.ForeignKey('game.Weapon',
                                        verbose_name="SEC WEAPON",
                                        default=None,
                                        null=True,
                                        blank=True,
                                        on_delete=models.SET_NULL)
    dungeon = models.ForeignKey("game.DungeonLvl",
                                default=None,
                                null=True,
                                blank=True,
                                on_delete=models.SET_NULL)

    def return_all_armor(self) -> int:
        bonus = settings.ROLES[self.role]['dmg']
        defence = self.defence + round(self.agility * bonus)
        if self.armor_equiped is None:
            return defence
        return defence + self.armor_equiped.armor_value

    def return_all_damage(self):
        bonus = settings.ROLES[self.role]['dmg']
        attack = self.attack + (self.agility * bonus)
        if self.weapon_equiped is None and self.weapon2_equiped is None:
            return attack
        if self.weapon_equiped:
            bonus += self.weapon_equiped.damage
        if self.weapon2_equiped:
            bonus += self.weapon2_equiped.damage
        return attack + bonus

    def get_summary_damage(self) -> dict:
        bonus = round(self.agility * settings.ROLES[self.role]['dmg'], 1)
        if self.weapon_equiped is None and self.weapon2_equiped is None:
            return {"hero": self.attack, "bonus": bonus, "total": self.attack + bonus}
        if self.weapon_equiped:
            bonus += self.weapon_equiped.damage
        if self.weapon2_equiped:
            bonus += self.weapon2_equiped.damage
        return {"hero": self.attack, "bonus": bonus, "total": self.attack + bonus}

    def get_summary_stats(self) -> dict:
        total_str = self.strength
        total_ag = self.agility

        current_time = timezone.now()
        if isinstance(self, Enemy):
            self.effect_enemy.filter(models.Q(deleted_time__lte=current_time)).delete()
            active_effects = self.effect_enemy.filter(deleted_time__gt=current_time).values()
        else:
            self.effect_set.filter(models.Q(deleted_time__lte=current_time)).delete()
            active_effects = self.effect_set.filter(deleted_time__gt=current_time).values()

        sum_str = sum(effect['strength'] for effect in active_effects)
        sum_ag = sum(effect['agility'] for effect in active_effects)

        return {
            "str": {"hero": total_str,
                    "sum": sum_str,
                    "total": max(total_str + sum_str, 0)},
            "ag": {"hero": total_ag,
                   "sum": sum_ag,
                   "total": max(total_ag + sum_ag, 0)},
            "effects": list(active_effects)
        }
    
    @database_sync_to_async
    def async_get_summary_stats(self) -> dict:
        total_str = self.strength
        total_ag = self.agility

        current_time = timezone.now()
        if isinstance(self, Enemy):
            self.effect_enemy.filter(models.Q(deleted_time__lte=current_time)).delete()
            active_effects = self.effect_enemy.filter(deleted_time__gt=current_time).values()
        else:
            self.effect_set.filter(models.Q(deleted_time__lte=current_time)).delete()
            active_effects = self.effect_set.filter(deleted_time__gt=current_time).values()

        sum_str = sum(effect['strength'] for effect in active_effects)
        sum_ag = sum(effect['agility'] for effect in active_effects)

        return {
            "str": {"hero": total_str,
                    "sum": sum_str,
                    "total": max(total_str + sum_str, 0)},
            "ag": {"hero": total_ag,
                   "sum": sum_ag,
                   "total": max(total_ag + sum_ag, 0)},
            "effects": list(active_effects)
        }

    def return_all_damage_taken(self) -> int:
        bonus = round(settings.ROLES[self.role]['dmg'] * self.agility)
        if self.weapon_equiped is not None:
            bonus += self.weapon_equiped.damage
        if self.weapon2_equiped is not None:
            bonus += self.weapon2_equiped.damage
        attack = self.attack + bonus
        if self.role == 'strength':
            return attack * 1.2
        if settings.ROLES[self.role]['double_dmg']:
            chance = random.randint(0, 100)
            if chance <= 10:
                return attack * 1.8
        return attack
    
    @database_sync_to_async
    def async_return_all_damage_taken(self) -> int:
        bonus = round(settings.ROLES[self.role]['dmg'] * self.agility)
        if self.weapon_equiped is not None:
            bonus += self.weapon_equiped.damage
        if self.weapon2_equiped is not None:
            bonus += self.weapon2_equiped.damage
        attack = self.attack + bonus
        if self.role == 'strength':
            return attack * 1.2
        if settings.ROLES[self.role]['double_dmg']:
            chance = random.randint(0, 100)
            if chance <= 10:
                return attack * 1.8
        return attack

    def return_all_defence(self) -> int:
        bonus = round(settings.ROLES[self.role]['dmg'] * self.agility)
        if self.armor_equiped is not None:
            bonus += self.armor_equiped.armor_value
        attack = self.defence + bonus
        return attack
    
    @database_sync_to_async
    def async_return_all_defence(self) -> int:
        bonus = round(settings.ROLES[self.role]['dmg'] * self.agility)
        if self.armor_equiped is not None:
            bonus += self.armor_equiped.armor_value
        attack = self.defence + bonus
        return attack

    def get_max_hp(self):
        return 100

    def get_current_hp(self):
        return self.health

    class Meta:
        abstract = True


class Enemy(BaseEntity):
    name = models.CharField("NAME", max_length=40)
    lvl = models.IntegerField("LEVEL", default=1)
    role = models.CharField("ROLE", max_length=40, default="strength")
    img = models.CharField("IMG", max_length=50)
    is_boss = models.BooleanField("IS_BOSS", default=False)
    weapon_equiped = models.ForeignKey('game.Weapon',
                                       verbose_name="WEAPON",
                                       default=None,
                                       null=True,
                                       blank=True,
                                       on_delete=models.SET_NULL,
                                       related_name='equipped_weapon_enemy')
    armor_equiped = models.ForeignKey('game.Armor',
                                      verbose_name="ARMOR",
                                      default=None,
                                      null=True,
                                      blank=True,
                                      on_delete=models.SET_NULL,
                                      related_name='equipped_armor_enemy')
    weapon2_equiped = models.ForeignKey('game.Weapon',
                                        verbose_name="SEC WEAPON",
                                        default=None,
                                        null=True, blank=True,
                                        on_delete=models.SET_NULL,
                                        related_name='equipped_weapon2_enemy')

    def get_name(self):
        return self.name

    def get_img_url(self):
        return static(f'img/enemy/lvl{self.lvl}/' + self.img)


class Task(models.Model):
    task_queue = models.PositiveSmallIntegerField("TASK QUEUE")
    name = models.CharField("TASK NAME", max_length=50)
    desc = models.TextField("TASK DESK")
    reward_exp = models.PositiveSmallIntegerField("TASK EXP")
    reward_money = models.PositiveSmallIntegerField("TASK MONEY_REWARD")
    is_current = models.BooleanField("IS CURRENT")
    enemy_type = models.CharField("TYPE", max_length=50)
    killed_enemies = models.PositiveIntegerField("KILLED")
    needed_enemies = models.PositiveIntegerField("NEEDED")
    user = models.ForeignKey("users.NewUser",
                             default=None,
                             null=True,
                             blank=True,
                             on_delete=models.CASCADE)
    

class Room(models.Model):
    first_player = models.ForeignKey("users.NewUser", default=None, null=True, blank=True, on_delete=models.SET_NULL, related_name="first")
    second_player = models.ForeignKey("users.NewUser", default=None, null=True, blank=True, on_delete=models.SET_NULL, related_name="second")
    name = models.CharField("NAME", max_length=50)
    rate = models.PositiveIntegerField("RATE")
    password = models.CharField("PASSWORD", max_length=255, default=None, null=True, blank=True)