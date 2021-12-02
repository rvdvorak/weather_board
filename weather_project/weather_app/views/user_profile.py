from weather_app.models import Location
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from weather_app.views.utils import get_query, get_location_history, get_favorite_locations
from django.shortcuts import redirect
from django.urls import reverse
from django.template.response import TemplateResponse


def render_user_profile(request, error_message='', success_message=''):
    query = get_query(request)
    return TemplateResponse(
        request,
        'weather_app/user_profile.html', {
            'display_mode': query['display_mode'],
            'location': {
                'label': query['label'],
                'latitude': query['latitude'],
                'longitude': query['longitude'] },
            'location_history': get_location_history(request.user),
            'favorite_locations': get_favorite_locations(request.user),
            'error_message': error_message,
            'success_message': success_message})


@login_required(redirect_field_name='next_url')
def user_profile(request):
    if request.method == 'GET':
        # Show user profile page
        return render_user_profile(request)
    if request.method == 'POST':
        # Try to apply changes
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Verify user identity
        user = authenticate(username=username, password=password)
        if not user:
            return render_user_profile(
                request,
                error_message='Username and password do not match.')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        clear_history = request.POST.get('clear_history')
        preserve_favorites = request.POST.get('preserve_favorites')
        delete_account = request.POST.get('delete_account')
        i_am_sure = request.POST.get('i_am_sure')
        if new_password1 and new_password2:
            # Change password
            if password != new_password1 == new_password2:
                user.set_password(new_password1)
                user.save()
                login(request, user)
                return render_user_profile(
                    request,
                    success_message='New password has been set successfully.')
            elif password == new_password1 == new_password2:
                return render_user_profile(
                    request,
                    error_message='New password must be different from the old one.')
            elif new_password1 != new_password2:
                return render_user_profile(
                    request,
                    error_message='New passwords do not match.')
        elif clear_history:
            # Delete location history
            if preserve_favorites:
                Location.objects.filter(
                    user=user,
                    is_favorite=False).delete()
                return render_user_profile(
                    request,
                    success_message='Your location history except favorites has been deleted.')
            else:
                Location.objects.filter(user=user).delete()
                return render_user_profile(
                    request,
                    success_message='Your location history has been deleted completely.')
        elif delete_account and i_am_sure:
            # Delete user account
            user.delete()
            return render_user_profile(
                request,
                success_message='Your user account has been deleted completely.')
        else:
            # Invalid options
            return render_user_profile(
                request,
                error_message='Invalid options.')
