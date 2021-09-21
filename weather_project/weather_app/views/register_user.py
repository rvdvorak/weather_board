from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib.auth import login, logout, authenticate

def register_user(request):
    if request.method == 'GET':
        return render(request, 'weather_app/register_user.html', {'form': UserCreationForm()})
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(request.POST['username'], password=request.POST['password1'])
                user.save()
                login(request, user)
                return redirect('home')
            except IntegrityError:
                return render(request, 'weather_app/register_user.html',
                    {'form': UserCreationForm(), 'error': 'User already exists. Please choose different username.'})
        else:
            return render(request, 'weather_app/register_user.html',
                {'form': UserCreationForm(), 'error': 'Passwords do not match.'})
