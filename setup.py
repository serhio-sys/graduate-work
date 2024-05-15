"""import os"""
import os


if __name__ == "__main__":
    os.system("python manage.py loaddata data/armor_data.json")
    os.system("python manage.py loaddata data/dungeon_data.json")
    os.system("python manage.py loaddata data/weapons_data.json")
    os.system("python manage.py loaddata data/enemy_data.json")
    os.system("python manage.py loaddata data/effects_data.json")
