# import from rest_framework library
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import Http404
from .serializers import *
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView
from .forms import AccessKeyForm, MailForm, SchoolForm
from datetime import datetime
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.conf import settings
from .models import *
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from .key_generator import generate_access_key
from account.models import CustomUser
from django.utils import timezone


# Create your views here.
def index(request):
    return render(request, 'management/index.html')


@method_decorator(login_required, name='dispatch')
class ListView(ListView):
    model = Key
    template_name = 'management/key_detail.html'
    ordering = ['date_of_procurement']
    context_object_name = 'list'
    paginate_by = 5


@login_required
def revoke_key(request, pk):
    access_key_by_id = get_object_or_404(Key, id=pk)
    access_key_by_id.status = 'revoked'
    access_key_by_id.save()
    messages.success(request,'Access-key has been revoked successfully')
    return redirect('management:key_list')
    # return render(request, 'management/key_list.html')


@login_required
def generate_key(request, pk):
    form = AccessKeyForm()
    user = request.user
    user_by_id = School.objects.get(id=pk)
    if request.method == 'POST':
        form = AccessKeyForm(request.POST)
        if form.is_valid():
            access_key =form.save(commit=False)
            access_key.key = generate_access_key
            access_key.school = user_by_id
            access_key.user =user
            if access_key.expiry_date and access_key.expiry_date < timezone.now():
                messages.warning(request, 'Expiry date cannot be in the past')
                return redirect('management:generate_key', user_by_id.id)
            else:
                access_key.expiry_date = form.cleaned_data['expiry_date']
                access_key.save()

            email_body = render_to_string('school/purchase_key_mail.html', {
                    'user': user,
                    'schools': user_by_id,
                    'domain': get_current_site(request).domain,
                    'access_key': Key.objects.filter(school= user_by_id).first()
                })
            email_body = strip_tags(email_body)
            email_subject = 'Access Key Granted'
            email = send_mail(email_subject, email_body,from_email=user.email, recipient_list=[settings.EMAIL_HOST_USER])
            # email.send()
            return redirect('management:school_key_view', user_by_id.id)
        else:
            form = AccessKeyForm()
    return render(request, 'management/generate_access_key.html',{'form':form, 'schools': user_by_id})


@login_required
def update_key(request, pk):
    access_key = get_object_or_404(Key, id=pk)
    if request.method == 'POST':
        form = AccessKeyForm(request.POST, instance= access_key)
        if form.is_valid():
            if access_key.expiry_date and access_key.expiry_date < timezone.now():
                messages.warning(request, 'Expiry date cannot be in the past')
                return redirect('management:update_key', access_key.pk)
            else:
                access_key.expiry_date = form.cleaned_data['expiry_date']
            access_key.save()
            messages.success(request,'Access-key has been Updated')
            return redirect('management:key_list')
    else:
        form = AccessKeyForm(instance= access_key)
    return render(request, 'management/api_update_form.html', {'form':form, 'access_key': access_key})


@method_decorator(login_required, name='dispatch')
class AccessKeyViewAPI(APIView):
    def get(self, request):
        form = MailForm(request.GET or None)
        if form.is_valid():
            email = form.cleaned_data['email']
            print(email)
            try:
                user = CustomUser.objects.get(email=email)
                school = School.objects.get(user=user)
                # key = get_object_or_404(Key, school=school)
                key = Key.objects.filter(school=school)
                serializers = ProjectSerializer(key, many=True)
                return Response(serializers.data)
            except ( Key.DoesNotExist, CustomUser.DoesNotExist):
                if user.is_superuser:
                    return HttpResponse('<h2>Access denied for Mircro-Focus Administrator...</h2>')
                else:
                    return Http404
        return render(request, 'management/api_form.html', {'form': form})


#School Dashboard
@login_required
def School_key_view(request, pk):
    user = request.user
    school = get_object_or_404(School, id=pk)
    key = Key.objects.filter(school=school).order_by('date_of_procurement')
    paginator = Paginator(key, 5)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    time = timezone.now()
    return render(request, 'school/dashboard.html', {'school':school, 'user':user, 'page_obj': page_object, 'time':time})


@login_required
def school_dashboard(request):
    form = SchoolForm()
    if request.method == 'POST':
        form = SchoolForm(request.POST)
        if form.is_valid():
            user = request.user
            name = form.cleaned_data['name']
            school = School.objects.create(name=name, user=user)
            school.save()
            return redirect('management:school_key_view', pk=school.pk)
        else:
            form = SchoolForm()
    return render(request,'school/school_view.html', {'form':form})


def key_request(request, school_id):
    # school = School.objects.get(id=school_id)
    school = get_object_or_404(School, id=school_id)
    key = Key.objects.filter(school=school, status=Key.ACTIVE).first()
    if key:
        if key.expiry_date > timezone.now():
            return HttpResponse('You have an active key already.')
        else:
            return redirect('management:generate_key', pk=str(school.id))
    else:
        return redirect('management:generate_key', pk=str(school.id))


