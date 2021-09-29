from django.shortcuts import render
from django.contrib import messages
import pprint

def home(request):
    try:
        return render(request, 'weather_app/home.html')
    except Exception as err:
        messages.error(request, {
            'headline': 'Internal error',
            'description': 'Homepage loading failed.',
            'icon': 'fas fa-times-circle',
            'admin_details': [
                'Method: home(request)',
                f'Exception: {pprint.pformat(err)}']})
        return render(request, 'weather_app/message.html')
