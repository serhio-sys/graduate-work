from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.generic import View, ListView
from django.utils import translation
from django.http import HttpRequest, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from .forms import ChoiceLanguageForm, UserUpdateForm


class SetLocale(View):
    def post(self, request: HttpRequest, route):
        form = ChoiceLanguageForm(request.POST)
        route_name = route
        if form.is_valid():
            translation.activate(form.cleaned_data['locale'])
            request.session['lang'] = form.cleaned_data['locale']
        else:
            return JsonResponse({"errors": form.errors})
        return redirect(route_name)


class ProfileEdit(LoginRequiredMixin, View):
    template_name = "users/profile.html"

    def get(self, request: HttpRequest):
        email_verified = request.user.email_verified()
        form = UserUpdateForm(email_verified=email_verified, instance=request.user)
        return render(request=request, template_name=self.template_name,
                      context={'form': form, 'email_verified': email_verified})

    def post(self, request: HttpRequest):
        form = UserUpdateForm(data=request.POST, 
                              email_verified=request.user.email_verified(), 
                              instance=request.user)
        if form.is_valid():
            upd = form.save(request=request, commit=False)
            upd.user = request.user
            upd.save()
        else:
            return render(request=request, template_name=self.template_name,
                          context={'form': form, 'errors': form.errors})
        return redirect('profile_edit')


class ForbesView(ListView):
    paginate_by = 3
    model = get_user_model()
    queryset = get_user_model().objects.filter(role__isnull=False)\
        .select_related('weapon2_equiped').select_related(
        'weapon_equiped').order_by('-balance', '-lvl')
    template_name = "users/forbes.html"


@login_required
def delete_account(request: HttpRequest):
    request.user.delete()
    logout(request=request)
    return redirect("home")


def home(request: HttpRequest):
    translation.activate(request.session.get('lang'))
    return render(request=request, template_name="home.html")


@login_required
def custom_logout(request):
    logout(request)
    return redirect("home")
