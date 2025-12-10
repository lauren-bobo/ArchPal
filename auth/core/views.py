from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm


@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

def signup(request):
    error = None
    form = CustomUserCreationForm()
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email', '').strip()
            if not email.endswith('@uga.edu'):
                error = "Please use your UGA email address."
            elif User.objects.filter(email=email).exists():
                error = "That email is already registered."
            else:
                user = form.save(commit=False)
                user.email = email  # Actually save the email!
                user.save()
                return redirect('login')
        else:
            error = "Please correct the errors below."
    return render(request, 'registration/signup.html', {'form': form, 'error': error})