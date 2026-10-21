from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import RegistroForm


def registro(request):
    if request.user.is_authenticated:
        return redirect("boletas:dashboard")
    form = RegistroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "¡Bienvenido/a! Completa tus datos de emisor para emitir tu primera boleta.")
        return redirect("boletas:perfil")
    return render(request, "cuentas/registro.html", {"form": form})
