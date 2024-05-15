from django.http import HttpRequest
from users.forms import ChoiceLanguageForm


def context_processor(request: HttpRequest): # pylint: disable=W0613
    return {'locale_form': ChoiceLanguageForm()}
