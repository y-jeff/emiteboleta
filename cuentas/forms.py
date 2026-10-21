from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, UserCreationForm

from boletas.forms import INPUT


class RegistroForm(UserCreationForm):
    """Registro con email: el email se usa como nombre de usuario."""

    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"autocomplete": "email"}))

    class Meta:
        model = get_user_model()
        fields = ("email",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT
        self.fields["password1"].help_text = "Mínimo 8 caracteres, que no sea solo números ni muy común."
        self.fields["password2"].help_text = ""

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if get_user_model().objects.filter(username__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este email.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Email"
        self.fields["username"].widget = forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True})
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()


class EstiloMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT


class RecuperarForm(EstiloMixin, PasswordResetForm):
    pass


class NuevaClaveForm(EstiloMixin, SetPasswordForm):
    pass
