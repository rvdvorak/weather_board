from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login


def login_user(request):
    if request.method == 'GET':
        return render(request, 'weather_app/login_user.html', {'form': AuthenticationForm()})
    else:
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user == None:
            return render(request, 'weather_app/login_user.html',
                {'form': AuthenticationForm(), 'error': 'Username and/or password do not match.'})
        else:    
            login(request, user)
            return redirect('home')