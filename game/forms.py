from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .models import Room

class UserIncreaseStatsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['agility'] = forms.IntegerField(
            required=True,
            label=_("Спритність"),
            widget=forms.NumberInput(
            attrs={"min": self.instance.agility, 
                    "class": "ag",
                    "readonly": "readonly",
                    "value": self.instance.agility,
                    "placeholder": _("Спритність")})
            )
        self.fields['strength'] = forms.IntegerField(required=True,
                    label=_("Сила"),
                    widget=forms.NumberInput(
                    attrs={"min": self.instance.strength, "class": "str", 
                        "readonly": "readonly",
                        "value": self.instance.strength, "placeholder": _("Сила")}))
        self.fields['upgrade_points'] = forms.IntegerField(
                    required=True,
                    widget=forms.HiddenInput(
                        attrs={"value": self.instance.upgrade_points}))

    class Meta:
        model = get_user_model()
        fields = ['agility', 'strength', 'upgrade_points']
        

class AttackForm(forms.Form):
    choise = [("head",_("Голова")),
            ("body",_("Тіло")),
            ("legs",_("Ноги"))]
    
    attack = forms.CharField(label=_("Атака"),widget=forms.RadioSelect(choices=choise))
    defence = forms.CharField(label=_("Захист"),widget=forms.RadioSelect(choices=choise))


class RoomCreateForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = _("Ім'я кімнати")
        self.fields['rate'].label = _("Початковий взнесок")
        self.fields['password'].label = _("Пароль кімнати (Не обов'язково)")

    class Meta:
        model = Room
        fields = ['name', 'rate', 'password']