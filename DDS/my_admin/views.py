from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import VehicleValue  # Our Car Database
import re, requests


# 1. LANDING PAGE
def main_home(request):
    return render(request, 'main_home.html')


# 2. REGISTRATION WITH SERVER-SIDE REGEX BACKUP
def my_register(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        # Server-side Email Validation (The Backup)
        email_pattern = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'

        if not re.match(email_pattern, email.lower()):
            messages.error(request, "Invalid email format! Please use name@domain.com")
            return render(request, "my_register.html")

        # Basic Validation
        if not all([first_name, username, email, password, confirm_password]):
            messages.error(request, "All fields are required!")
            return render(request, "my_register.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return render(request, "my_register.html")

        # Duplicate Checks
        if User.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered!")
            return render(request, "my_register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken!")
            return render(request, "my_register.html")

        # User Creation
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
        )
        user.save()

        messages.success(request, "Account created with AutoGrade AI! Please sign in.")
        return redirect("my_login")

    return render(request, 'my_register.html')


# 3. LOGIN LOGIC
def my_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, "Please enter both username and password!")
            return render(request, "my_login.html")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back to AutoGrade AI, {user.first_name}!")
            return redirect("admin_dashboard")
        else:
            messages.error(request, "Invalid credentials. Please try again.")
            return render(request, "my_login.html")

    return render(request, 'my_login.html')


# 4. LOGOUT LOGIC
def my_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('main_home')


# 5. CAR ANALYTICS DASHBOARD
@login_required(login_url='my_login')
def admin_dashboard(request):
    # Fetch all unique Car Makes from the SQLite DB
    makes = VehicleValue.objects.values_list('make', flat=True).distinct()

    context = {
        'user': request.user,
        'makes': makes,
    }
    return render(request, "Dashboard.html", context)


# 6. AJAX ENDPOINT FOR DYNAMIC CAR DROPDOWNS
def get_vehicle_details(request):
    """Fetches specific car models and years based on the selected Make"""
    make = request.GET.get('make')
    # Fetch models and years associated with the selected make
    car_data = VehicleValue.objects.filter(make=make).values('model', 'year')
    return JsonResponse(list(car_data), safe=False)


# 7. API Request for Yolo model
def api_req(request):
    if request.method == 'POST':
        image = request.FILES.getlist('images')
        print(image, "image? whare")
        files_to_send = []
        for img in image:
            print(img.name)
            # Most YOLO/Flask setups expect 'images' or 'file'
            files_to_send.append(('image', (img.name, img.read(), img.content_type)))

        #response = requests.post("http://192.168.1.15:5000/home", files=files_to_send)
        # files_to_send = [('file', (img.name, img.read(), img.content_type)) for img in images]

        try:
            ai_url = "http://127.0.0.1:5000/home"
            response = requests.post(ai_url, files=files_to_send, timeout=60)

            # --- DEBUGGING LINES ---
            print(f"AI Server Status Code: {response.status_code}")
            print(f"AI Server Raw Response: {response.text}")
            # -----------------------

            # Check if the response is actually JSON before parsing
            if response.status_code == 200:
                try:
                    ai_results = response.json()
                    print(ai_results)
                    return JsonResponse({'status': 'done', 'ai_data': ai_results})
                except Exception:
                    return JsonResponse({'status': 'error', 'message': 'AI server did not return JSON. Check AI terminal.'})
            else:
                return JsonResponse({'status': 'error', 'message': f'AI Server Error {response.status_code}'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid Request'}, status=400)
