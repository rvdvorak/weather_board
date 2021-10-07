from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login
import pprint


def login_user(request):
    try:
        if request.method == 'GET':
            return render(
                request,
                'weather_app/login_user.html', {
                    'form': AuthenticationForm()})
        elif request.method == 'POST':
            user = authenticate(
                request,
                username=request.POST['username'],
                password=request.POST['password'])
            if not user:
                return render(
                    request,
                    'weather_app/login_user.html', {
                        'form': AuthenticationForm(),
                        'error': 'Username and/or password do not match.'})
            else:
                login(request, user)
                return redirect('dashboard')
    except Exception as err:
        messages.error(
            request, {
                'headline': 'Internal error',
                'description': 'Log-in failed.',
                'icon': 'fas fa-times-circle',
                'admin_details': [
                    'Method: login_user(request)',
                    f'Exception: {pprint.pformat(err)}']})
        return render(request, 'weather_app/message.html')
