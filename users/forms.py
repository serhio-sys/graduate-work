from typing import Any
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.urls import reverse, NoReverseMatch
from allauth.socialaccount.forms import SignupForm
from allauth.socialaccount.models import SocialAccount, EmailAddress
from allauth.utils import set_form_field_order, get_username_max_length
from allauth.account.forms import PasswordField, SignupForm as SF, LoginForm,\
    ResetPasswordForm, ChangePasswordForm, \
    ResetPasswordKeyForm, SetPasswordField
from game.models import DungeonLvl
from allauth.socialaccount.adapter import get_adapter

CHOICE = [
    ("en", "EN"),
    ("uk", "UK")
]


class CustomLoginForm(LoginForm):

    error_messages = {
        "account_inactive": _("Неактивований акаунт."),
        "email_password_mismatch": _(
            "Електронна пошта й/або пароль введені некоректно. Будь ласка перевірте вхідні дані."
        ),
        "username_password_mismatch": _(
            "Не знайдено жодного користувача за вхідними даними.  Будь ласка перевірте вхідні дані."
        ),
    }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super(LoginForm, self).__init__(*args, **kwargs)
        login_field = forms.CharField(
            label=_("Ім'я користувача"),
            widget=forms.TextInput(
                attrs={"placeholder": _("Ім'я користувача"), "autocomplete": "username"}
            ),
            max_length=get_username_max_length(),
        )
        self.fields["login"] = login_field
        set_form_field_order(self, ["login", "password", "remember"])
        self.fields["password"] = PasswordField(label=_("Пароль"), autocomplete="new-password")
        try:
            reset_url = reverse("account_reset_password")
        except NoReverseMatch:
            pass
        else:
            forgot_txt = _("Забули пароль?")
            self.fields["password"].help_text = mark_safe(
                f'<a href="{reset_url}">{forgot_txt}</a>'
            )


class CustomUserCreationFormAccount(SF):
    def __init__(self, *args, **kwargs):
        super(SF, self).__init__(*args, **kwargs)
        self.fields['username'] = forms.CharField(required=True,
                            widget=forms.TextInput(attrs={"placeholder": _("Ім'я користувача")}),
                            label=_("Ім'я користувача"))
        self.fields["email"] = forms.EmailField(required=True,
                            widget=forms.EmailInput(attrs={"placeholder": _("Електронна пошта")}),
                            label=_("Електронна пошта"))
        self.fields["password1"] = PasswordField(label=_("Пароль"), 
                                                 autocomplete="new-password")
        self.fields["password2"] = PasswordField(label=_("Пароль (знову)"), 
                                                 autocomplete="new-password")
        self.fields["img"] = forms.ImageField(required=False, label=_("Аватар (Не обов'язковий)"))

        if hasattr(self, "field_order"):
            set_form_field_order(self, self.field_order)

    def save(self, request):
        user = super(CustomUserCreationFormAccount, self).save(request) # pylint: disable=R1725
        user.dungeon = DungeonLvl.objects.get(pk=1)
        if request.FILES:
            user.img = request.FILES['img']
        user.save()
        return user


class CustomUserCreationForm(SignupForm):
    email = forms.CharField(required=True, widget=forms.HiddenInput())
    username = forms.CharField(required=True, label=_("Ім'я користувача"))
    account_img = forms.ImageField(required=False, label=_("Аватар (Не обов'язковий)"))
    password1 = PasswordField(label=_("Пароль"), autocomplete="new-password")

    def __init__(self, *args, **kwargs):  # pylint: disable=W0246
        super().__init__(*args, **kwargs)
        data = get_adapter().get_signup_form_initial_data(self.sociallogin)
        self.fields["username"].widget=forms.TextInput(attrs={"placeholder": _("Ім'я користувача"), "value": data['first_name']})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        data = get_adapter().get_signup_form_initial_data(self.sociallogin)
        kwargs['initial'] = {'username': data['first_name']}
        return kwargs

    def save(self, request):
        password = self.cleaned_data["password1"]
        user = super(CustomUserCreationForm, self).save(request) # pylint: disable=R1725
        user.activated = True
        user.set_password(password)
        user.dungeon = DungeonLvl.objects.get(pk=1)
        if request.FILES:
            user.img = request.FILES['account_img']
        user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    def __init__(self, email_verified, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if email_verified:
            self.fields['email'] = forms.EmailField(label=_("Електронна пошта"), 
                widget=forms.EmailInput(attrs={'value': self.instance.email, 
                                               "placeholder": _("Електронна пошта")}))
        else:
            self.fields['email'] = forms.EmailField(label=_("Електронна пошта"), 
                widget=forms.EmailInput(attrs={'readonly': 'readonly', 
                                               'value': self.instance.email}))
        self.fields['username'] = forms.CharField(required=True, label="Ім'я користувача",
                widget=forms.TextInput(attrs={"placeholder": _("Ім'я користувача")}))
        self.fields['img'] = forms.ImageField(required=False, label=_("Аватар (Не обов'язковий)."))

    def is_valid(self) -> bool:
        if self.data['email'] != self.instance.email:
            self.instance.activated = False
            try:
                SocialAccount.objects.get(user=self.instance.id).delete()
                EmailAddress.objects.get(user=self.instance.id).delete()
            except SocialAccount.DoesNotExist or EmailAddress.DoesNotExist: #pylint: disable=W0711
                pass
        return super().is_valid()

    def save(self, request, commit: bool = ...) -> Any: # pylint: disable=W0237
        if request.FILES:
            self.instance.img = request.FILES['img']
        return super().save(commit)

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'img']


class CustomResetPassword(ResetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'] = forms.EmailField(label=_("Електронна пошта"),
                widget=forms.EmailInput(attrs={"placeholder": _("Електронна пошта")}))


class CustomResetPasswordKeyForm(ResetPasswordKeyForm):
    password1 = SetPasswordField(label=_("Новий пароль"))
    password2 = PasswordField(label=_("Повторіть пароль"))


class CustomChangePasswordForm(ChangePasswordForm):
    oldpassword = PasswordField(
        label=_("Поточний пароль"), autocomplete="current-password"
    )
    password1 = SetPasswordField(
        label=_("Новий пароль")
    )
    password2 = PasswordField(label=_("Повторіть новий пароль"))


class ChoiceLanguageForm(forms.Form):
    locale = forms.ChoiceField(label=False, choices=CHOICE, 
            widget=forms.Select(attrs={'class': 'form-control locale'}))
