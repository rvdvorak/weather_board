from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout
import pprint


def logout_user(request):
    try:
        if request.user.is_authenticated:
            logout(request)
        return redirect('home')
    except Exception as err:
        messages.error(
            request, {
                'headline': 'Internal error',
                'description': 'Log-out failed.',
                'icon': 'fas fa-times-circle',
                'admin_details': [
                    'Method: logout_user(request)',
                    f'Exception: {pprint.pformat(err)}']})
        return render(request, 'weather_app/message.html')
        