from django.shortcuts import render
import pprint

def home(request):
    try:
        return render(request, 'weather_app/home.html')
    except Exception as err:
        return render(request, 'weather_app/message.html', {
            'message': {
                'style': 'danger',
                'headline': 'Internal error',
                'description': 'Data processing failed.',
                'admin_details': [
                    'Method: home(request)',
                    f'Exception: {pprint.pformat(err)}']}})
