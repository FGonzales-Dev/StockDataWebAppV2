from email.headerregistry import Group
from unicodedata import name
from django.shortcuts import render, redirect
from .forms import RegisterForm, ProfileForm,LoginForm
from django.contrib.auth.models import User
from .models import Profile
from django.utils.crypto import get_random_string
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as views_auth
from . import forms
from django.contrib.auth import login, authenticate 
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm 

# Create your views here.
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        profile_form = ProfileForm(request.POST)
        if form.is_valid() and profile_form.is_valid():
            user = form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.user_key = get_random_string(10, 'abcdef0123456789')
            profile.save()
            new_user = authenticate(username=form.cleaned_data['username'],
                                    password=form.cleaned_data['password1'],
                                    )
            login(request, new_user)
        return redirect("/profile")
    else:
        form = RegisterForm()
        profile_form = ProfileForm()
        print("not success")
    return render(request, "register/register.html", {"form":form, "profile_form":profile_form })

def profile(request):
    
    return render(request,"register/profile.html")

def login_request(request):
	if request.method == "POST":
		form = AuthenticationForm(request, data=request.POST)
		if form.is_valid():
			username = form.cleaned_data.get('username')
			password = form.cleaned_data.get('password')
			user = authenticate(username=username, password=password)
			if user is not None:
				login(request, user)
				messages.info(request, f"You are now logged in as {username}.")
				return redirect("/profile")
			else:
				messages.error(request,"Invalid username or password.")
		else:
			messages.error(request,"Invalid username or password.")
	form = AuthenticationForm()
	return render(request=request, template_name="register/login.html", context={"login_form":form})


