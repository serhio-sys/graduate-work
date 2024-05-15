from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from allauth.account.models import EmailAddress
from game.models import Enemy, BaseEntity


class NewUser(AbstractUser, BaseEntity):
    upgrade_points = models.PositiveIntegerField("UPGRADE POINTS", default=0)
    img = models.ImageField("IMG", upload_to="img/", default=None, null=True, blank=True)
    balance = models.DecimalField("MONEY", default=0, decimal_places=0, max_digits=10)
    lvl = models.IntegerField("LEVEL", default=1)
    exp = models.IntegerField("EXP", default=0)
    is_started = models.BooleanField("IS FINISHED INSTRUCTION", default=False)
    killed_units = models.PositiveIntegerField("Killed units for all time", default=0)
    current_position = models.CharField("POSITION IN THE GAME",
                                        max_length=200,
                                        blank=True,
                                        null=True,
                                        default=None)
    current_dungeon = models.PositiveIntegerField(
        default=1,
        blank=True
    )
    is_fight = models.BooleanField("IS FIGHT", default=False)
    enemy = models.ForeignKey("game.Enemy",
                              verbose_name="ENEMY",
                              default=None,
                              null=True,
                              blank=True,
                              on_delete=models.SET_NULL)
    weapon_equiped = models.ForeignKey('game.Weapon',
                                       verbose_name="WEAPON",
                                       default=None,
                                       null=True,
                                       blank=True,
                                       on_delete=models.SET_NULL,
                                       related_name='equipped_weapon_user')
    armor_equiped = models.ForeignKey('game.Armor',
                                      verbose_name="ARMOR",
                                      default=None,
                                      null=True,
                                      blank=True,
                                      on_delete=models.SET_NULL,
                                      related_name='equipped_armor_user')
    weapon2_equiped = models.ForeignKey('game.Weapon',
                                        verbose_name="SEC WEAPON",
                                        default=None,
                                        null=True,
                                        blank=True,
                                        on_delete=models.SET_NULL,
                                        related_name='equipped_weapon2_user')

    def get_name(self):
        return self.username

    def email_verified(self):
        return EmailAddress.objects.filter(user=self, verified=True).exists()

    def get_class_img(self):
        url = f"{settings.PROTOCOL}://127.0.0.1:8000"
        return url + "/static/img/classes/" + settings.ROLES[self.role]['img']

    def check_exp(self):
        if self.lvl >= 99 and self.exp > 99:
            self.lvl = 99
            self.exp = 99
            self.save(update_fields=['lvl', 'exp'])
        else:
            if self.exp >= 100:
                self.lvl += 1
                self.upgrade_points = self.upgrade_points + 3
                self.exp = 0
                self.save(update_fields=['lvl', 'exp', 'upgrade_points'])
        return self.lvl
