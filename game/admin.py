from django.contrib import admin
from .models import (
    Armor,
    Weapon,
    Enemy,
    Effect,
    DungeonLvl,
    Room
)

admin.site.register(Armor)
admin.site.register(Weapon)
admin.site.register(Enemy)
admin.site.register(Effect)
admin.site.register(DungeonLvl)
admin.site.register(Room)
