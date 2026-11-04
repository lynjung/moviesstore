from django.contrib.auth.forms import UserCreationForm
from django.forms.utils import ErrorList
from django.utils.html import format_html_join
class CustomErrorList(ErrorList):
    def __str__(self):
        if not self:
            return ''
        return format_html_join('', '<div class="alert alert-danger" role="alert">{}</div>',
                                ((error,) for error in self))
class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        self.error_class = CustomErrorList
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None
            self.fields[fieldname].widget.attrs.update(
                {'class': 'form-control'}
            )
