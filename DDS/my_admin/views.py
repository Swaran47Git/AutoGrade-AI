import re, json
import requests
# FIXED CODE
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from .models import UserProfile, VehicleValue, DamageAnalysis, ClaimImage, DamageDetection, UserComplaint


def is_agent(user):
    try:
        return user.userprofile.role == 'Agent' or user.is_superuser
    except UserProfile.DoesNotExist:
        return False


def main_home(request):
    return render(request, 'main_home.html')


def my_register(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        email_pattern = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
        if not re.match(email_pattern, email.lower()):
            messages.error(request, "Invalid email format!")
            return render(request, "my_register.html")
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return render(request, "my_register.html")
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken!")
            return render(request, "my_register.html")
        user = User.objects.create_user(username=username, email=email, password=password, first_name=first_name)
        UserProfile.objects.create(user=user, role='User')
        messages.success(request, "Account created!")
        return redirect("my_login")
    return render(request, 'my_register.html')


def my_login(request):
    if request.method == "POST":
        u_name = request.POST.get("username", "").strip()
        p_word = request.POST.get("password", "")
        user = authenticate(request, username=u_name, password=p_word)
        if user is not None:
            login(request, user)
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': 'Admin' if user.is_superuser else 'User'}
            )
            if profile.role == 'Admin':
                return redirect('admin_panel')
            elif profile.role == 'Agent':
                return redirect('agent_dashboard')
            else:
                return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid credentials.")
    return render(request, 'my_login.html')


def my_logout(request):
    storage = messages.get_messages(request)
    for _ in storage:
        pass  # Just iterating through them clears the queue
    logout(request)
    return redirect('main_home')


@login_required
def admin_dashboard(request):
    if request.user.userprofile.role == 'Agent': return redirect('agent_dashboard')
    makes = VehicleValue.objects.values_list('make', flat=True).distinct()
    return render(request, "Dashboard.html", {'makes': makes})


@login_required
def upload_images(request):
    if request.method == "POST":
        make = request.POST.get('make')
        model = request.POST.get('model')
        year = request.POST.get('year')
        manual = request.POST.get('manual_details')
        vehicle_desc = manual if manual else f"{year} {make} {model}"

        # NOTE: When the model is active, you might call api_req here
        new_claim = DamageAnalysis.objects.create(
            user=request.user,
            car_details=vehicle_desc,
            status='Pending',
            damage_level='TBD',
            estimated_claim=0
        )
        files = request.FILES.getlist('car_images')
        for f in files:
            ClaimImage.objects.create(
                analysis=new_claim,  # Use 'analysis' here!
                image=f
            )
        messages.success(request, "Claim Submitted Successfully!")
        return redirect('claim_history')
    return redirect('admin_dashboard')


@login_required
def claim_history(request):
    my_claims = DamageAnalysis.objects.filter(user=request.user).order_by('-updated_at')
    return render(request, "ClaimHistory.html", {'claims': my_claims})


@login_required
def claim_details(request, claim_id):
    claim = get_object_or_404(DamageAnalysis, id=claim_id, user=request.user)
    return render(request, "ClaimDetails.html", {'claim': claim})


@login_required
def submit_appeal(request, claim_id):
    claim = get_object_or_404(DamageAnalysis, id=claim_id, user=request.user)
    if request.method == "POST" and claim.appeal_count < 2:
        claim.user_appeal_reason = request.POST.get('appeal_reason')
        claim.appeal_count += 1
        claim.status = 'Pending'
        claim.save()
        messages.success(request, "Appeal sent to the Insurance Agent.")
    else:
        messages.error(request, "Max appeals reached. Please escalate to Admin.")
    return redirect('claim_history')


@login_required
def admin_complaint(request, claim_id):
    claim = get_object_or_404(DamageAnalysis, id=claim_id, user=request.user)
    if request.method == "POST":
        UserComplaint.objects.create(
            user=request.user,
            claim=claim,
            subject=f"Final Dispute: {claim.car_details}",
            description=request.POST.get('description'),
            priority='High'
        )
        messages.warning(request, "Claim escalated to System Administrator.")
    return redirect('claim_history')


@login_required
def user_edit_claim(request, claim_id):
    claim = get_object_or_404(DamageAnalysis, id=claim_id, user=request.user)
    if claim.status != 'Pending':
        messages.error(request, "Processed claims cannot be edited.")
        return redirect('claim_history')
    if request.method == "POST":
        claim.car_details = request.POST.get('car_details')
        claim.save()
        messages.success(request, "Details updated.")
        return redirect('claim_history')
    return render(request, "UserEditClaim.html", {'claim': claim})


@login_required
@user_passes_test(is_agent, login_url='admin_dashboard')
def agent_dashboard(request):
    assigned_claims = DamageAnalysis.objects.filter(status='Pending').order_by('-updated_at')
    return render(request, "AgentDashboard.html", {'claims': assigned_claims})


@login_required
def review_claim(request, claim_id):
    if not is_agent(request.user): return redirect('admin_dashboard')
    claim = get_object_or_404(DamageAnalysis, id=claim_id)

    default_market_value = 0
    try:
        model_name = claim.car_details.split()[-1]
        vehicle = VehicleValue.objects.filter(model__icontains=model_name).first()
        if vehicle: default_market_value = vehicle.price
    except:
        pass

    if request.method == "POST":
        # Get form inputs
        m_val = float(request.POST.get('market_value') or 0)
        mi_c = float(request.POST.get('minor_coeff') or 0.025)
        mo_c = float(request.POST.get('moderate_coeff') or 0.05)
        ma_c = float(request.POST.get('major_coeff') or 0.1)

        # Update base fields
        claim.market_value = m_val
        claim.minor_coeff = mi_c
        claim.moderate_coeff = mo_c
        claim.major_coeff = ma_c
        claim.agent_comment = request.POST.get('agent_comment')

        if "run_model" in request.POST:
            # 1. Gather all images associated with this claim
            evidence_photos = claim.images.all()

            if not evidence_photos.exists():
                messages.error(request, "No images found to analyze! Please ask user for evidence.")
                return redirect('review_claim', claim_id=claim.id)

            files_to_send = []
            opened_files = []

            try:
                # 2. Prepare files for the YOLO API
                for photo_record in evidence_photos:
                    f = open(photo_record.image.path, 'rb')
                    opened_files.append(f)
                    files_to_send.append(('image', (photo_record.image.name, f, 'image/jpeg')))

                # 3. Call the YOLO Server
                ai_url = "http://26.185.160.119:5000/home"
                response = requests.post(ai_url, files=files_to_send, timeout=60)

                if response.status_code == 200:
                    ai_results = response.json()
                    detections_data = ai_results.get('detections', [])
                    # --- CLEAN 5 RELATIONAL LOGIC ---
                    # 4. Clear any old AI detections before saving new ones (Prevent Duplicates)
                    claim.detections.all().delete()

                    total_coeff = 0.0
                    counts = {'Major': 0, 'Moderate': 0, 'Minor': 0}
                    highest_sev = 'Minor'

                    # 5. Create a REAL database row for every single detection
                    for det in detections_data:
                        sev = det.get('severity', 'minor').lower()
                        ai_filename = det.get('filename', '')
                        clean_name = ai_filename.split('/')[-1]

                        # Finding the correct photo
                        correct_photo = claim.images.filter(image__icontains=clean_name).first()
                        if not correct_photo:
                            correct_photo = claim.images.first()

                        # 2. CREATE THE DATABASE ROW (Must happen inside the loop)
                        DamageDetection.objects.create(
                            analysis=claim,
                            severity=sev,
                            box_coords=str(det.get('box')),
                            source_image=correct_photo,
                            # part_name=f"Damage on {clean_name}"
                        )

                        # 3. Additive Math (Must happen inside the loop)
                        if sev == 'major':
                            total_coeff += float(ma_c); counts['Major'] += 1; highest_sev = 'Major'
                        elif sev == 'moderate':
                            total_coeff += float(mo_c); counts['Moderate'] += 1
                            if highest_sev != 'Major': highest_sev = 'Moderate'
                        else:
                            total_coeff += float(mi_c); counts['Minor'] += 1
                    # 7. Update the Master Claim (DamageAnalysis table)
                    summary = [f"{k}({v})" for k, v in counts.items() if v > 0]
                    claim.detected_parts = ", ".join(summary)
                    claim.total_damage_factor = total_coeff
                    claim.damage_level = highest_sev

                    # Calculate Final Payout: Market Value * Sum of Coefficients
                    claim.estimated_claim = float(m_val) * total_coeff

                    claim.save()
                    messages.success(request, f"AI Ledger Updated: {len(detections_data)} items identified.")
                else:
                    messages.error(request, "AI Server returned an error. Check Flask terminal.")

            except Exception as e:
                messages.error(request, f"System Error: {str(e)}")
            finally:
                # Cleanup: Close all image files
                for f in opened_files:
                    f.close()

            return redirect('review_claim', claim_id=claim.id)

        # Handle Finalize
        if "finalize_valuation" in request.POST:
            if claim.appeal_count >= 2:
                claim.status = 'Escalated'
            else:
                claim.status = 'Approved'

            claim.save()
            messages.success(request, "Valuation finalized.")
            return redirect('agent_dashboard')

        # Handle Generic Save
        claim.save()
        return redirect('review_claim', claim_id=claim.id)

    # PAGE LOAD (GET REQUEST)
    context = {
        'claim': claim,
        'detections': claim.detections.all(),  # This now finds the rows created above
        'default_market_value': default_market_value,
        'def_minor': 0.025, 'def_moderate': 0.05, 'def_major': 0.1
    }
    return render(request, "ReviewClaim.html", context)


@login_required
@user_passes_test(is_agent, login_url='admin_dashboard')
def manage_part_weights(request):
    return render(request, "ManageWeights.html")


@login_required
def admin_panel(request):
    if request.user.userprofile.role != 'Admin': return redirect('admin_dashboard')
    search_query = request.GET.get('search', '').strip()
    profiles = UserProfile.objects.all()
    if search_query:
        profiles = profiles.filter(user__username__icontains=search_query) | profiles.filter(
            user__first_name__icontains=search_query)
    return render(request, "AdminPanel.html", {'profiles': profiles, 'search_query': search_query})


@login_required
def admin_complaints_view(request):
    if request.user.userprofile.role != 'Admin': return redirect('admin_dashboard')
    complaints = UserComplaint.objects.all().order_by('-created_at')
    return render(request, "AdminComplaints.html", {'complaints': complaints})


@login_required
def user_detail_view(request, profile_id):
    if request.user.userprofile.role != 'Admin': return redirect('admin_dashboard')
    profile = get_object_or_404(UserProfile, id=profile_id)
    history = DamageAnalysis.objects.filter(
        agent=profile.user) if profile.role == 'Agent' else DamageAnalysis.objects.filter(user=profile.user)
    return render(request, "UserDetail.html", {'profile': profile, 'history': history.order_by('-updated_at')})


@login_required
def grant_agent_status(request, user_id):
    if request.user.userprofile.role != 'Admin': return redirect('admin_dashboard')
    profile = get_object_or_404(UserProfile, id=user_id)
    profile.role = 'Agent'
    profile.save()
    messages.success(request, f"{profile.user.username} is now an Insurance Agent.")
    return redirect('admin_panel')


def get_vehicle_details(request):
    make = request.GET.get('make')
    car_data = VehicleValue.objects.filter(make=make).values('model', 'year')
    return JsonResponse(list(car_data), safe=False)


def api_req(request,images):
    if request.method == 'POST':
        #images = request.FILES.getlist('images')
        files_to_send = [('image', (img.name, img.read(), img.content_type)) for img in images]
        try:
            ai_url = "http://127.0.0.1:5000/home"
            response = requests.post(ai_url, files=files_to_send, timeout=60)
            if response.status_code == 200:
                return JsonResponse({'status': 'done', 'ai_data': response.json()})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid Request'}, status=400)