from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from django.conf import settings
import logging
logger = logging.getLogger(__name__)


def auth_login(request):
    next_page = request.GET.get('next', '/anno/')
    if request.user.is_authenticated:
        return redirect(next_page)

    if request.method == 'POST':
        user_form = AuthenticationForm(data=request.POST)
        if user_form.is_valid():
            user = authenticate(
                username=user_form.cleaned_data['username'],
                password=user_form.cleaned_data['password'])
            # user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            logger.info('%s login' % user)
            return redirect(next_page)
        else:
            return render(request, 'auth/auth.html', {'form': user_form})
    return render(request, 'auth/auth.html', {'form': AuthenticationForm()})


def auth_logout(request):
    logout(request)
    return redirect('/anno')


def auth_register(request):
    next_page = request.GET.get('next', '/anno/')
    user_form = UserCreationForm()
    if request.method == 'POST':
        user_form = UserCreationForm(data=request.POST)
        if user_form.is_valid():
            user_form.save()
            username = user_form.cleaned_data.get('username')
            raw_password = user_form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect(next_page)
        else:
            return render(request, 'auth/register.html', {'form': user_form})
    return render(request, 'auth/register.html', {'form': user_form})