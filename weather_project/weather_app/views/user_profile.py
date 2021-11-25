from weather_app.models import Location
from django.contrib.auth import login, authenticate
from weather_app.views.utils import get_location_params, get_location_history, get_favorite_locations, redirect_to_login
from django.shortcuts import redirect
from django.urls import reverse
from django.template.response import TemplateResponse


def render_user_profile(request, error_message=None, success_message=None):
    return TemplateResponse(
        request,
        'weather_app/user_profile.html', {
            'success_message': success_message,
            'error_message': error_message,
            'location_params': get_location_params(request),
            'location_history': get_location_history(request.user),
            'favorite_locations': get_favorite_locations(request.user)})


# TODO Implement "login required" decorator
def user_profile(request):
    if not request.user.is_authenticated:
        return redirect_to_login(get_location_params(request))
    if request.method == 'GET':
        # TODO Test show user profile page logged in
        # TODO Test show user profile page logged out
        return render_user_profile(request)
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
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
        if new_password1 or new_password2:
            if password != new_password1 == new_password2:
                # Change password successfully
                # TODO Test change password with correct credentials
                # TODO Test change password with bad credentials
                user.set_password(new_password1)
                user.save()
                login(request, user)
                return render_user_profile(
                    request,
                    success_message='New password has been set successfully.')
            elif password == new_password1 == new_password2:
                # New password is same as oldpassword
                # TODO Test new password is same like old password
                return render_user_profile(
                    request,
                    error_message='New password must be different from the old one.')
            elif new_password1 != new_password2:
                # New passwords do not match
                # TODO Test new passwords do not match
                return render_user_profile(
                    request,
                    error_message='New passwords do not match.')
        elif clear_history:
            # Delete location history
            # TODO Test delete location history with correct credentials
            # TODO Test delete location history with bad credentials
            if preserve_favorites:
                # TODO Test delete location history except favorites
                Location.objects.filter(
                    user=user,
                    is_favorite=False).delete()
                return render_user_profile(
                    request,
                    success_message='Your location history except favorites has been deleted.')
            else:
                # TODO Test delete location history completely
                Location.objects.filter(user=user).delete()
                return render_user_profile(
                    request,
                    success_message='Your location history has been deleted completely.')
        elif delete_account and i_am_sure:
            # Delete user account
            # TODO Test delete user account with correct credentials
            # TODO Test delete user account with bad credentials
            user.delete()
            return render_user_profile(
                request,
                success_message='Your user account has been deleted completely.')
        else:
            # Invalid options
            # TODO Test invalid user profile options
            return render_user_profile(
                request,
                error_message='Invalid options.')
