from django.shortcuts import redirect
from django.contrib.auth import logout


def logout_user(request):
    #TODO Exceptions
    if request.method == 'POST':
        logout(request)
        return redirect('home')