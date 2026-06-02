from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, "Вы успешно вошли в систему")
            return redirect("home")
        messages.error(request, "Неверное имя пользователя или пароль")
    return render(request, "api/login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "Вы вышли из системы")
    return redirect("login")


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")

        if not username:
            messages.error(request, "Имя пользователя обязательно")
        elif password != password2:
            messages.error(request, "Пароли не совпадают")
        elif len(password) < 6:
            messages.error(request, "Пароль должен содержать не менее 6 символов")
        else:
            try:
                User.objects.create_user(username=username, password=password)
            except Exception:
                messages.error(request, "Пользователь с таким именем уже существует")
            else:
                messages.success(request, "Регистрация завершена. Теперь войдите в систему")
                return redirect("login")

    return render(request, "api/register.html")
