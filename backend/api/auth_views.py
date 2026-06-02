from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, 'Р’С‹ СѓСЃРїРµС€РЅРѕ РІРѕС€Р»Рё')
            return redirect('home')
        else:
            messages.error(request, 'РќРµРІРµСЂРЅС‹Р№ Р»РѕРіРёРЅ РёР»Рё РїР°СЂРѕР»СЊ')
    return render(request, 'api/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Р’С‹ РІС‹С€Р»Рё РёР· СЃРёСЃС‚РµРјС‹')
    return redirect('login')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            messages.error(request, 'РџР°СЂРѕР»Рё РЅРµ СЃРѕРІРїР°РґР°СЋС‚')
        elif len(password) < 6:
            messages.error(request, 'РџР°СЂРѕР»СЊ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ РЅРµ РјРµРЅРµРµ 6 СЃРёРјРІРѕР»РѕРІ')
        else:
            from django.contrib.auth.models import User
            try:
                User.objects.create_user(username=username, password=password)
                messages.success(request, 'Р РµРіРёСЃС‚СЂР°С†РёСЏ СѓСЃРїРµС€РЅР°! РўРµРїРµСЂСЊ РІРѕР№РґРёС‚Рµ')
                return redirect('login')
            except:
                messages.error(request, 'РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ СЃ С‚Р°РєРёРј РёРјРµРЅРµРј СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓРµС‚')

    return render(request, 'api/register.html')
