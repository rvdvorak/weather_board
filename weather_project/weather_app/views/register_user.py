from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib.auth import login, logout, authenticate
import pprint



def register_user(request):
    try:
        if request.method == 'GET':
            return render(request, 'weather_app/register_user.html', {'form': UserCreationForm()})
        else:
            if request.POST['password1'] == request.POST['password2']:
                try:
                    user = User.objects.create_user(request.POST['username'], password=request.POST['password1'])
                    user.save()
                    login(request, user)
                    return redirect('dashboard')
                except IntegrityError:
                    return render(request, 'weather_app/register_user.html',
                        {'form': UserCreationForm(), 'error': 'User already exists. Please choose different username.'})
            else:
                return render(request, 'weather_app/register_user.html',
                    {'form': UserCreationForm(), 'error': 'Passwords do not match.'})
    except Exception as err:
        messages.error(
            request, {
                'header': 'Internal error',
                'description': 'User registration failed.',
                'icon': 'fas fa-times-circle',
                'admin_details': [
                    'Method: register_user(request)',
                    f'Exception: {pprint.pformat(err)}']})
        return render(request, 'weather_app/message.html')