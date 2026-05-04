from django.shortcuts import render,redirect,get_object_or_404
from .models import *
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
import os
import google.generativeai as genai
from utils.ai_engine import detect_intent
from utils.ai_llm import get_ai_goal
import os
from openai import OpenAI
from datetime import timedelta,datetime
from datetime import date   
from django.utils import timezone
import random
import razorpay
from django.conf import settings
import string
from django.http import JsonResponse
from django.db.models import Q, Sum, Count,Avg
import json
import random
import string
from django.core.mail import send_mail
from decimal import Decimal 
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import io
from django.template.loader import get_template
from django.core.mail import EmailMessage
from io import BytesIO
from xhtml2pdf import pisa
from .utils.pdf_utils import send_invoice_email
from django.contrib.auth.hashers import make_password, check_password
# Create your views here.

AIclient = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


razorpay_client = razorpay.Client(auth=(
    settings.RAZORPAY_KEY_ID,
    settings.RAZORPAY_KEY_SECRET
))

def index(request):
    # Fetch all products from database
    all_products = products.objects.all()
    
    # Categorize products
    vegetables = products.objects.filter(category__icontains='vegetable')
    fruits = products.objects.filter(category__icontains='fruit')
    proteins = products.objects.filter(category__icontains='protein')
   
    
    # Get recent feedbacks
    recent_feedbacks = Feedbacks.objects.select_related('user', 'product').order_by('-submitted_at')[:6]
    
    
    context = {
        'products': all_products,
        'vegetables': vegetables,
        'fruits': fruits,
        'proteins': proteins,
        'feedbacks': recent_feedbacks,
    }
    return render(request, 'home.html', context)

def openlogin(request):
    return render(request,'login.html')

def openreg(request):
    return render(request,'seller-reg.html')

import re
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

def userreg(request):
    if request.method == 'POST':
        # Get form data
        name = request.POST['fullname']
        email_id = request.POST['email']
        phone_number = request.POST['phone']
        address = request.POST['address']
        password = request.POST['password']
        confirmpassword = request.POST.get('confirmpassword')
        
        # ========== VALIDATIONS ==========
        
        # 1. Name validation
        if not name or len(name.strip()) < 2:
            messages.error(request, "Name must be at least 2 characters long!")
            return render(request, 'login.html')
        
        if any(char.isdigit() for char in name):
            messages.error(request, "Name cannot contain numbers!")
            return render(request, 'login.html')
        
        # 2. Email validation
        if not email_id:
            messages.error(request, "Email is required!")
            return render(request, 'login.html')
        
        try:
            validate_email(email_id)
        except ValidationError:
            messages.error(request, "Please enter a valid email address!")
            return render(request, 'login.html')
        
        # 3. Phone number validation (10 digits)
        if not phone_number or not phone_number.isdigit() or len(phone_number) != 10:
            messages.error(request, "Please enter a valid 10-digit phone number!")
            return render(request, 'login.html')
        
        # 4. Address validation
        if not address or len(address.strip()) < 5:
            messages.error(request, "Address must be at least 5 characters long!")
            return render(request, 'login.html')
        
        # 5. Password validation
        if not password or len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long!")
            return render(request, 'login.html')
        
        # Check for at least one uppercase, one lowercase, one number
        if not re.search(r'[A-Z]', password):
            messages.error(request, "Password must contain at least one uppercase letter!")
            return render(request, 'login.html')
        
        if not re.search(r'[a-z]', password):
            messages.error(request, "Password must contain at least one lowercase letter!")
            return render(request, 'login.html')
        
        if not re.search(r'[0-9]', password):
            messages.error(request, "Password must contain at least one number!")
            return render(request, 'login.html')
        
        # 6. Confirm password validation
        if password != confirmpassword:
            messages.error(request, "Passwords do not match!")
            return render(request, 'login.html')
        
        # 7. Check if email already exists in user table
        if user.objects.filter(email=email_id).exists():
            messages.error(request, "Email already registered as a customer!")
            return render(request, 'login.html')
        
        # 8. Check if email already exists in seller table
        if Seller.objects.filter(email=email_id).exists():
            messages.error(request, "Email already registered as a seller! Please use a different email.")
            return render(request, 'login.html')
        
        # 9. Phone number uniqueness (optional)
        if user.objects.filter(phone=phone_number).exists():
            messages.error(request, "Phone number already registered!")
            return render(request, 'login.html')
        
        # ========== CREATE USER ==========
        try:
            data = user.objects.create(
                name=name.strip(),
                email=email_id.lower().strip(),
                phone=phone_number,
                address=address.strip(),
                password=password  # Note: You should hash passwords in production!
            )
            data.save()
            messages.success(request, "Account created successfully! Please login.")
            return render(request, 'login.html')
            
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return render(request, 'login.html')
    
    return render(request, 'login.html')


def sellerreg(request):
    if request.method == 'POST':
        # Get form data
        cname = request.POST['companyname']
        owner_name = request.POST['ownername']
        email_id = request.POST['email']
        phone_number = request.POST['phone']
        address = request.POST['address']
        gst_no = request.POST['gstnumber']
        password = request.POST['password']
        confirmpassword = request.POST.get('confirmpassword')
        
        # ========== VALIDATIONS ==========
        
        # 1. Company name validation
        if not cname or len(cname.strip()) < 2:
            messages.error(request, "Company name must be at least 2 characters long!")
            return render(request, 'seller-reg.html')
        
        # 2. Owner name validation
        if not owner_name or len(owner_name.strip()) < 2:
            messages.error(request, "Owner name must be at least 2 characters long!")
            return render(request, 'seller-reg.html')
        
        if any(char.isdigit() for char in owner_name):
            messages.error(request, "Owner name cannot contain numbers!")
            return render(request, 'seller-reg.html')
        
        # 3. Email validation
        if not email_id:
            messages.error(request, "Email is required!")
            return render(request, 'seller-reg.html')
        
        try:
            validate_email(email_id)
        except ValidationError:
            messages.error(request, "Please enter a valid email address!")
            return render(request, 'seller-reg.html')
        
        # 4. Phone number validation (10 digits)
        if not phone_number or not phone_number.isdigit() or len(phone_number) != 10:
            messages.error(request, "Please enter a valid 10-digit phone number!")
            return render(request, 'seller-reg.html')
        
        # 5. Address validation
        if not address or len(address.strip()) < 5:
            messages.error(request, "Address must be at least 5 characters long!")
            return render(request, 'seller-reg.html')
        
        # 6. GST number validation
        if not gst_no or len(gst_no.strip()) < 15:
            messages.error(request, "GST number must be 15 characters long!")
            return render(request, 'seller-reg.html')
        
        # GST format: 22AAAAA0000A1Z5 (example format)
        gst_pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z]{1}[0-9A-Z]{1}$'
        if not re.match(gst_pattern, gst_no.upper()):
            messages.error(request, "Please enter a valid GST number format!")
            return render(request, 'seller-reg.html')
        
        # 7. Password validation
        if not password or len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long!")
            return render(request, 'seller-reg.html')
        
        # Check for at least one uppercase, one lowercase, one number
        if not re.search(r'[A-Z]', password):
            messages.error(request, "Password must contain at least one uppercase letter!")
            return render(request, 'seller-reg.html')
        
        if not re.search(r'[a-z]', password):
            messages.error(request, "Password must contain at least one lowercase letter!")
            return render(request, 'seller-reg.html')
        
        if not re.search(r'[0-9]', password):
            messages.error(request, "Password must contain at least one number!")
            return render(request, 'seller-reg.html')
        
        # 8. Confirm password validation
        if password != confirmpassword:
            messages.error(request, "Passwords do not match!")
            return render(request, 'seller-reg.html')
        
        # 9. Check if GST number already exists
        if Seller.objects.filter(gst_number=gst_no.upper()).exists():
            messages.error(request, "GST number already registered!")
            return render(request, 'seller-reg.html')
        
        # 10. Check if email already exists in seller table
        if Seller.objects.filter(email=email_id.lower()).exists():
            messages.error(request, "Email already registered as a seller!")
            return render(request, 'seller-reg.html')
        
        # 11. Check if email already exists in user table
        if user.objects.filter(email=email_id.lower()).exists():
            messages.error(request, "Email already registered as a customer! Please use a different email.")
            return render(request, 'seller-reg.html')
        
        # 12. Phone number uniqueness (optional)
        if Seller.objects.filter(phone=phone_number).exists():
            messages.error(request, "Phone number already registered!")
            return render(request, 'seller-reg.html')
        
        # ========== CREATE SELLER ==========
        try:
            data = Seller.objects.create(
                company_name=cname.strip(),
                owner_name=owner_name.strip(),
                email=email_id.lower().strip(),
                phone=phone_number,
                address=address.strip(),
                gst_number=gst_no.upper().strip(),
                password=password,  # Note: You should hash passwords in production!
                status = 'pending'  # New sellers start with pending status
            )
            data.save()
            messages.success(request, "Seller account created successfully! Please login.")
            return render(request, 'login.html')
            
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return render(request, 'seller-reg.html')
    
    return render(request, 'seller-reg.html')
def userlogin(request):
    if request.method == 'POST':
        Email = request.POST.get('email')
        Password = request.POST.get('password')

        # Admin login
        if Email == "admin@gmail.com" and Password == "admin":
            request.session['admin'] = Email
            messages.success(request, 'Welcome Admin!')
            return redirect('admin_dashboard')

        # User login
        try:
            u = user.objects.get(email=Email, password=Password)
            request.session['uid'] = u.email
            
            # Get cart count
            cart_count = Cart.objects.filter(user_email=u.email).count()
            
            all_products = products.objects.all()
            categories = products.objects.values_list('category', flat=True).distinct()
            feedbacks = Feedbacks.objects.select_related('user').order_by('-submitted_at')[:6]
            
            context = {
                'products': all_products,
                'categories': categories,
                'feedbacks': feedbacks,
                'user': u,
                'user_email': u.email,
                'cart_count': cart_count,
                'logged_in': True
            }
            return render(request, 'index.html', context)
            
        except user.DoesNotExist:
            pass

        # Dietitian login
        try:
            dietitian = Dietitian.objects.get(email=Email)
            if Password == dietitian.password:
                if dietitian.is_active:
                    request.session['dietitian_id'] = dietitian.id
                    request.session['dietitian_email'] = dietitian.email
                    request.session['dietitian_name'] = dietitian.name
                    messages.success(request, f'Welcome back, Dietitian {dietitian.name}!')
                    return redirect('dietitian_dashboard')
                else:
                    messages.error(request, 'Your account is inactive. Please contact admin.')
                    return render(request, 'login.html')
            else:
                messages.error(request, 'Invalid password')
                return render(request, 'login.html')
        except Dietitian.DoesNotExist:
            pass

        # Seller login with status check
        try:
            seller = Seller.objects.get(email=Email, password=Password)
            
            # Check seller status
            if seller.status == 'pending':
                messages.warning(request, 'Your account is pending verification. Please wait for admin approval.')
                return render(request, 'login.html')
            elif seller.status == 'rejected':
                messages.error(request, f'Your account has been rejected. Reason: {seller.rejection_reason or "Not specified"}')
                return render(request, 'login.html')
            elif seller.status == 'suspended':
                messages.error(request, 'Your account has been suspended. Please contact support.')
                return render(request, 'login.html')
            elif seller.status == 'approved':
                # Store seller info in session
                request.session['seller_id'] = seller.id
                request.session['sid'] = seller.email
                request.session['seller_email'] = seller.email
                request.session['seller_name'] = seller.company_name
                
                messages.success(request, f'Welcome back, {seller.company_name}!')
                return redirect('seller_dashboard')
            
        except Seller.DoesNotExist:
            pass

        # Invalid credentials
        messages.error(request, "Invalid Email or Password")
        return render(request, 'login.html', {'error': 'Invalid email or password'})
    
    return render(request, 'login.html')
def userdashboard(request):
    if 'uid' in request.session:
        user_email = request.session['uid']
        u = user.objects.get(email=user_email)
        all_products = products.objects.all()
        
    
    # Get recent feedbacks
        recent_feedbacks = Feedbacks.objects.select_related('user', 'product').order_by('-submitted_at')[:6]
    
        context = {
                'products': all_products,
                'user': u,
                'logged_in': True,
                'feedbacks': recent_feedbacks,
            }
        return render(request, 'index.html', context)
    return redirect('log')

def admin_dashboard(request):
    """Admin dashboard with real data from models"""
    # Check if admin is logged in
    if 'admin' not in request.session:
        messages.warning(request, 'Please login as admin')
        return redirect('log')
    
    # Get current date using Django's timezone
    today_date = timezone.now().date()  # Renamed from 'today' to 'today_date'
    first_day_month = today_date.replace(day=1)
    
    # Statistics from models
    total_users = user.objects.count()
    total_sellers = Seller.objects.count()
    total_products = products.objects.count()
    total_orders = Orders.objects.count()
    total_pending_verification = Seller.objects.filter(status='pending').count()
    print('tf',total_pending_verification)
    # Orders by status
    pending_orders = Orders.objects.filter(order_status='pending').count()
    confirmed_orders = Orders.objects.filter(order_status='confirmed').count()
    prepared_orders = Orders.objects.filter(order_status='prepared').count()
    dispatched_orders = Orders.objects.filter(order_status='dispatched').count()
    delivered_orders = Orders.objects.filter(order_status='delivered').count()
    cancelled_orders = Orders.objects.filter(order_status='cancelled').count()
    
    # Payment statistics
    paid_orders = Orders.objects.filter(payment_status='paid').count()
    pending_payments = Orders.objects.filter(payment_status='pending').count()
    failed_payments = Orders.objects.filter(payment_status='failed').count()
    
    # Revenue calculations
    total_revenue = Orders.objects.filter(
        payment_status='paid'
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    monthly_revenue = Orders.objects.filter(
        payment_status='paid',
        order_date__date__gte=first_day_month
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Average order value
    avg_order_value = Orders.objects.filter(
        payment_status='paid'
    ).aggregate(Avg('total_amount'))['total_amount__avg'] or 0
    
    # Meal type distribution
    meal_types = {
        'breakfast': products.objects.filter(category__icontains='breakfast').count(),
        'lunch': products.objects.filter(category__icontains='lunch').count(),
        'dinner': products.objects.filter(category__icontains='dinner').count(),
        'snacks': products.objects.filter(
            Q(category__icontains='snack') | 
            Q(category__icontains='snacks')
        ).count(),
    }
    
    # Popular products
    popular_products = OrderItem.objects.values(
        'product__product_name', 'product__calories', 'product__image'
    ).annotate(
        total_orders=Count('order', distinct=True),
        total_quantity=Sum('quantity')
    ).order_by('-total_orders')[:5]
    
    # Recent orders
    recent_orders = Orders.objects.select_related('customer').order_by('-order_date')[:10]
    
    # Orders for charts (last 7 days) - FIXED: renamed loop variable
    dates = []
    order_counts = []
    
    for i in range(6, -1, -1):
        current_date = today_date - timedelta(days=i)  # Renamed from 'date' to 'current_date'
        count = Orders.objects.filter(order_date__date=current_date).count()
        dates.append(current_date.strftime('%a'))
        order_counts.append(count)
    
    # Monthly trends (last 6 months)
    monthly_orders = []
    monthly_labels = []
    
    for i in range(5, -1, -1):
        month_date = today_date - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        
        # Calculate month end
        if month_date.month == 12:
            month_end = month_date.replace(day=31)
        else:
            month_end = (month_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        count = Orders.objects.filter(
            order_date__date__gte=month_start,
            order_date__date__lte=month_end
        ).count()
        
        monthly_orders.append(count)
        monthly_labels.append(month_date.strftime('%b %Y'))
    
    # Recent feedbacks
    recent_feedbacks = Feedbacks.objects.select_related('user').order_by('-submitted_at')[:5]
    
    # Order status distribution
    order_status_data = {
        'labels': ['Pending', 'Confirmed', 'Prepared', 'Dispatched', 'Delivered', 'Cancelled'],
        'data': [
            pending_orders,
            confirmed_orders,
            prepared_orders,
            dispatched_orders,
            delivered_orders,
            cancelled_orders
        ]
    }
    
    # Top sellers
    top_sellers = Seller.objects.annotate(
        total_revenue=Sum('orders__total_amount', 
                         filter=Q(orders__payment_status='paid')),
        total_orders=Count('orders')
    ).order_by('-total_revenue')[:5]
    
    context = {
        'admin_email': request.session['admin'],
        # User stats
        'total_users': total_users,
        'total_sellers': total_sellers,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_pending_verification': total_pending_verification,
        
        # Order stats
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'prepared_orders': prepared_orders,
        'dispatched_orders': dispatched_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'paid_orders': paid_orders,
        'pending_payments': pending_payments,
        'failed_payments': failed_payments,
        
        # Revenue stats
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'avg_order_value': round(avg_order_value, 2),
        
        # Distribution
        'meal_types': meal_types,
        'popular_products': popular_products,
        'recent_orders': recent_orders,
        'recent_feedbacks': recent_feedbacks,
        'top_sellers': top_sellers,
        
        # Chart data
        'chart_dates': json.dumps(dates),
        'chart_order_counts': json.dumps(order_counts),
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_orders': json.dumps(monthly_orders),
        'order_status_labels': json.dumps(order_status_data['labels']),
        'order_status_data': json.dumps(order_status_data['data']),
    }
    
    return render(request, 'fitness-dashboard.html', context)
def admin_users(request):
    """View all users"""
    if 'admin' not in request.session:
        return redirect('log')
    
    users_list = user.objects.all().order_by('-created_at')
    return render(request, 'admin_users.html', {'users': users_list})

def admin_sellers(request):
    """View all sellers"""
    if 'admin' not in request.session:
        return redirect('log')
    
    sellers_list = Seller.objects.all()
    return render(request, 'admin_sellers.html', {'sellers': sellers_list})

def admin_products(request):
    """View all products"""
    if 'admin' not in request.session:
        return redirect('log')
    
    products_list = products.objects.select_related('seller').all()
    return render(request, 'admin_products.html', {'products': products_list})

def admin_orders(request):
    """View all orders"""
    if 'admin' not in request.session:
        return redirect('log')
    
    orders_list = Orders.objects.select_related('customer', 'seller').all().order_by('-order_date')
    return render(request, 'admin_orders.html', {'orders': orders_list})

def admin_order_detail(request, order_id):
    """View single order details"""
    if 'admin' not in request.session:
        return redirect('log')
    
    order = Orders.objects.select_related('customer', 'seller').get(id=order_id)
    order_items = OrderItem.objects.filter(order=order).select_related('product')
    
    return render(request, 'admin_order_detail.html', {
        'order': order,
        'order_items': order_items
    })

def admin_logout(request):
    """Admin logout"""
    if 'admin' in request.session:
        del request.session['admin']
        messages.success(request, 'Logged out successfully')
    return redirect('admin_dashboard')

def seller_dashboard(request):
    """Seller dashboard view"""
    # Check if seller is logged in
    if 'seller_id' not in request.session:
        messages.warning(request, 'Please login to access dashboard')
        return redirect('seller_login')
    
    try:
        seller = Seller.objects.get(id=request.session['seller_id'])
        
        # Get statistics
        total_products = products.objects.filter(seller=seller).count()
        
        # Get orders for this seller's products
        # This depends on how you link orders to products
        # You might need to adjust based on your OrderItem model
        seller_orders = Orders.objects.filter(seller=seller)
        total_orders = seller_orders.count()
        pending_orders = seller_orders.filter(order_status='pending').count()
        
        # Calculate total revenue from paid orders
        from django.db.models import Sum
        total_revenue = seller_orders.filter(
            payment_status='paid'
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        # Get recent 5 orders
        recent_orders = seller_orders.order_by('-order_date')[:5]
        
        context = {
            'seller': seller,
            'total_products': total_products,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'total_revenue': total_revenue,
            'recent_orders': recent_orders,
        }
        
        return render(request, 'seller-home.html', context)
        
    except Seller.DoesNotExist:
        messages.error(request, 'Seller not found')
        return redirect('seller_login')

def seller_logout(request):
    """Seller logout"""
    request.session.flush()  # Clear all session data
    messages.success(request, 'Logged out successfully')
    return redirect('login')


def showuser(request):
    data = user.objects.all()
    paginator = Paginator(data,10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request,'user.html',{'user':page_obj})

def showseller(request):
    data = Seller.objects.all()
    paginator = Paginator(data,10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request,'seller.html',{'seller':page_obj})

def addproducts(request):
    if request.method == 'POST':
        # Check both possible session keys
        seller_id = None
        if 'seller_id' in request.session:
            seller_id = request.session['seller_id']
        elif 'sid' in request.session:
            seller_id = request.session['sid']
        else:
            return HttpResponse("<script>alert('Please login as seller!'); window.location='/login/';</script>")
        
        try:
            # Get seller by ID or email
            try:
                sellerdata = Seller.objects.get(id=seller_id)
            except Seller.DoesNotExist:
                # Try by email if ID doesn't work
                sellerdata = Seller.objects.get(email=seller_id)
            
            # Get form data with .get() to avoid KeyError
            name = request.POST.get('product_name', '').strip()
            description = request.POST.get('description', '').strip()
            category = request.POST.get('category', '').strip()
            
            # Get numeric values and validate
            calories_str = request.POST.get('calories', '0').strip()
            protein_str = request.POST.get('protein', '0').strip()
            carbs_str = request.POST.get('carbs', '0').strip()
            fat_str = request.POST.get('fat', '0').strip()
            fiber_str = request.POST.get('fiber', '0').strip()
            price_str = request.POST.get('price', '0').strip()
            stock_str = request.POST.get('stock', '0').strip()
            weight_str = request.POST.get('weight', '0').strip()
            
            # Handle image upload
            images = request.FILES.get('images')
            
            # ========== VALIDATION ==========
            
            # 1. Validate required fields
            if not name:
                return HttpResponse("<script>alert('❌ Product name is required!'); window.history.back();</script>")
            
            if len(name) < 2:
                return HttpResponse("<script>alert('❌ Product name must be at least 2 characters long!'); window.history.back();</script>")
            
            if any(char.isdigit() for char in name):
                return HttpResponse("<script>alert('❌ Product name cannot contain numbers!'); window.history.back();</script>")
            
            # 2. Validate description
            if not description:
                return HttpResponse("<script>alert('❌ Product description is required!'); window.history.back();</script>")
            
            if len(description) < 10:
                return HttpResponse("<script>alert('❌ Description must be at least 10 characters long!'); window.history.back();</script>")
            
            # 3. Validate category
            if not category:
                return HttpResponse("<script>alert('❌ Please select a category!'); window.history.back();</script>")
            
            # 4. Validate image
            if not images:
                return HttpResponse("<script>alert('❌ Please upload a product image!'); window.history.back();</script>")
            
            # Validate image type
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
            file_extension = os.path.splitext(images.name)[1].lower()
            
            if file_extension not in allowed_extensions:
                return HttpResponse("<script>alert('❌ Invalid image format! Please upload JPG, JPEG, PNG, WEBP, or GIF.'); window.history.back();</script>")
            
            # Validate image size (max 5MB)
            if images.size > 5 * 1024 * 1024:
                return HttpResponse("<script>alert('❌ Image size too large! Maximum size is 5MB.'); window.history.back();</script>")
            
            # 5. Validate numeric fields
            # Helper function to validate numbers
            def validate_number(value_str, field_name, allow_decimal=True):
                if not value_str or value_str == '':
                    return 0, True  # Empty is treated as 0
                
                # Remove any whitespace
                value_str = value_str.strip()
                
                # Check if it contains only numbers and optional decimal
                if allow_decimal:
                    import re
                    if not re.match(r'^\d*\.?\d+$', value_str):
                        return None, False
                else:
                    if not value_str.isdigit():
                        return None, False
                
                try:
                    if allow_decimal:
                        value = float(value_str)
                    else:
                        value = int(value_str)
                    return value, True
                except ValueError:
                    return None, False
            
            # Validate calories
            calories, valid = validate_number(calories_str, 'calories', True)
            if not valid:
                return HttpResponse("<script>alert('❌ Calories must be a valid number (e.g., 100, 250.5)!'); window.history.back();</script>")
            if calories < 0:
                return HttpResponse("<script>alert('❌ Calories cannot be negative!'); window.history.back();</script>")
            
            # Validate protein
            protein, valid = validate_number(protein_str, 'protein', True)
            if not valid:
                return HttpResponse("<script>alert('❌ Protein must be a valid number (e.g., 10, 15.5)!'); window.history.back();</script>")
            if protein < 0:
                return HttpResponse("<script>alert('❌ Protein cannot be negative!'); window.history.back();</script>")
            
            # Validate carbs
            carbs, valid = validate_number(carbs_str, 'carbs', True)
            if not valid:
                return HttpResponse("<script>alert('❌ Carbs must be a valid number (e.g., 20, 30.5)!'); window.history.back();</script>")
            if carbs < 0:
                return HttpResponse("<script>alert('❌ Carbs cannot be negative!'); window.history.back();</script>")
            
            # Validate fat
            fat, valid = validate_number(fat_str, 'fat', True)
            if not valid:
                return HttpResponse("<script>alert('❌ Fat must be a valid number (e.g., 5, 10.5)!'); window.history.back();</script>")
            if fat < 0:
                return HttpResponse("<script>alert('❌ Fat cannot be negative!'); window.history.back();</script>")
            
            # Validate fiber
            fiber, valid = validate_number(fiber_str, 'fiber', True)
            if not valid:
                return HttpResponse("<script>alert('❌ Fiber must be a valid number (e.g., 2, 5.5)!'); window.history.back();</script>")
            if fiber < 0:
                return HttpResponse("<script>alert('❌ Fiber cannot be negative!'); window.history.back();</script>")
            
            # Validate price
            price, valid = validate_number(price_str, 'price', True)
            if not valid:
                return HttpResponse("<script>alert('❌ Price must be a valid number (e.g., 99, 199.99)!'); window.history.back();</script>")
            if price <= 0:
                return HttpResponse("<script>alert('❌ Price must be greater than 0!'); window.history.back();</script>")
            
            # Validate stock
            stock_quantity, valid = validate_number(stock_str, 'stock', False)
            if not valid:
                return HttpResponse("<script>alert('❌ Stock quantity must be a valid whole number (e.g., 10, 25, 100)!'); window.history.back();</script>")
            if stock_quantity < 0:
                return HttpResponse("<script>alert('❌ Stock quantity cannot be negative!'); window.history.back();</script>")
            
            # Validate weight (optional)
            weight, valid = validate_number(weight_str, 'weight', False)
            if not valid:
                return HttpResponse("<script>alert('❌ Weight must be a valid whole number (e.g., 250, 500)!'); window.history.back();</script>")
            if weight < 0:
                return HttpResponse("<script>alert('❌ Weight cannot be negative!'); window.history.back();</script>")
            
            # ========== CREATE PRODUCT ==========
            
            # Create product
            data = products.objects.create(
                seller=sellerdata,
                product_name=name,
                description=description,
                image=images,
                category=category,
                calories=calories,
                protein=protein,
                carbs=carbs,
                fat=fat,
                fiber=fiber,
                price=price,
                stock_quantity=stock_quantity,
                weight=weight
            )
            
            return HttpResponse("<script>alert('✅ Product added successfully!'); window.location='/seller-products/';</script>")
            
        except Seller.DoesNotExist:
            return HttpResponse("<script>alert('❌ Seller not found! Please login again.'); window.location='/login/';</script>")
        except Exception as e:
            import traceback
            traceback.print_exc()
            return HttpResponse(f"<script>alert('❌ Error: {str(e)}'); window.history.back();</script>")
            
    return render(request, 'seller-products.html')
def seller_products(request):
    # Check if seller is logged in - check both possible session keys
    if 'seller_id' not in request.session and 'sid' not in request.session:
        messages.warning(request, 'Please login to view products')
        return redirect('seller_login')
    
    try:
        # Get seller from session
        seller_id = None
        if 'seller_id' in request.session:
            seller_id = request.session['seller_id']
        elif 'sid' in request.session:
            seller_id = request.session['sid']
        
        # Get seller object (by ID or email)
        try:
            seller = Seller.objects.get(id=seller_id)
        except (Seller.DoesNotExist, ValueError):
            seller = Seller.objects.get(email=seller_id)
        
        # Filter products by this seller only
        product_qs = products.objects.filter(seller=seller).order_by('-id')
        
        # Pagination
        paginator = Paginator(product_qs, 5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'products': page_obj,
            'seller': seller,
        }
        return render(request, 'view-seller-products.html', context)
        
    except Seller.DoesNotExist:
        messages.error(request, 'Seller not found. Please login again.')
        return redirect('seller_login')
    except Exception as e:
        messages.error(request, f'Error loading products: {str(e)}')
        return redirect('seller_dashboard')

def update_product(request):
    """Update product with all fields"""
    if request.method == "POST":
        # Check seller authentication
        seller_id = None
        if 'seller_id' in request.session:
            seller_id = request.session['seller_id']
        elif 'sid' in request.session:
            seller_id = request.session['sid']
        else:
            messages.error(request, 'Please login as seller')
            return redirect('seller_login')
        
        try:
            # Get product and verify ownership
            p_id = request.POST.get('product_id')
            product = get_object_or_404(products, id=p_id)
            
            # Verify that this product belongs to the logged-in seller
            try:
                seller = Seller.objects.get(id=seller_id)
            except (Seller.DoesNotExist, ValueError):
                seller = Seller.objects.get(email=seller_id)
            
            if product.seller.id != seller.id:
                messages.error(request, 'You do not have permission to edit this product')
                return redirect('seller_inventory')
            
            # Get all form data
            product_name = request.POST.get('product_name', '').strip()
            description = request.POST.get('description', '').strip()
            category = request.POST.get('category', '').strip()
            
            # Get numeric values with proper conversion
            calories = request.POST.get('calories', 0)
            protein = request.POST.get('protein', 0)
            carbs = request.POST.get('carbs', 0)
            fat = request.POST.get('fat', 0)
            fiber = request.POST.get('fiber', 0)
            price = request.POST.get('price', 0)
            stock = request.POST.get('stock', 0)
            weight = request.POST.get('weight', 0)
            
            # Validate required fields
            if not product_name or not description or not category:
                messages.error(request, 'Please fill all required fields')
                return redirect('seller_inventory')
            
            # Update product fields
            product.product_name = product_name
            product.description = description
            product.category = category
            
            # Update nutrition fields (convert to appropriate types)
            product.calories = int(float(calories)) if calories else 0
            product.protein = float(protein) if protein else 0.0
            product.carbs = float(carbs) if carbs else 0.0
            product.fat = float(fat) if fat else 0.0
            product.fiber = float(fiber) if fiber else 0.0
            
            # Update price and stock
            product.price = float(price) if price else 0.0
            product.stock_quantity = int(stock) if stock else 0
            product.weight = int(weight) if weight else 0
            
            product.save()
            
            messages.success(request, f'Product "{product_name}" updated successfully!')
            
        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')
        
        return redirect('seller_inventory')
    
    return redirect('seller_inventory')
def delete_product(request, pk):
    product = get_object_or_404(products, id=pk)
    product.delete()
    return redirect(seller_products)
        
def logout(request):
    if 'uid' in request.session:
        request.session.flush()
        return render(request,'login.html')
    elif 'sid' in request.session:
        request.session.flush()
        return render(request,'login.html')
    elif 'admin' in request.session:
        return render(request,'login.html')
    return render(request,'login.html')

def openserch(request):
    # Get all products from database
    all_products = products.objects.all()
    
    # Get unique categories for filter
    categories = products.objects.values_list('category', flat=True).distinct()
    
    # Get cart count for logged in user
    cart_count = 0
    user_email = None
    if 'uid' in request.session:
        user_email = request.session['uid']
        cart_count = Cart.objects.filter(user_email=user_email).count()
    
    context = {
        'products': all_products,
        'categories': categories,
        'total_products': all_products.count(),
        'cart_count': cart_count,
        'user_email': user_email
    }
    return render(request, 'user-search.html', context)

def searchproduct(request):
    if request.method == 'POST':
        goal = request.POST.get('goal')
        weight = request.POST.get('weight')
        height = request.POST.get('height')
        prompt = request.POST.get('prompt', '').strip()
        
        # Calculate BMI and recommended calorie intake
        bmi = None
        bmi_category = None
        recommended_calories = None
        recommended_protein = None
        
        if weight and height:
            try:
                height_m = float(height) / 100
                weight_kg = float(weight)
                bmi = round(weight_kg / (height_m * height_m), 2)
                
                # Determine BMI category
                if bmi < 18.5:
                    bmi_category = 'Underweight'
                    recommended_calories = 2500  # Higher calories for weight gain
                    recommended_protein = round(weight_kg * 1.2, 1)  # 1.2g per kg
                elif bmi < 25:
                    bmi_category = 'Normal'
                    recommended_calories = 2200
                    recommended_protein = round(weight_kg * 1.0, 1)
                elif bmi < 30:
                    bmi_category = 'Overweight'
                    recommended_calories = 1800  # Lower calories for weight loss
                    recommended_protein = round(weight_kg * 1.0, 1)
                else:
                    bmi_category = 'Obese'
                    recommended_calories = 1500
                    recommended_protein = round(weight_kg * 1.0, 1)
            except (ValueError, ZeroDivisionError):
                bmi = None
        
        # Start with all products
        products_list = products.objects.all()
        
        # Apply goal-based filters with only existing fields
        if goal == 'weight_loss':
            products_list = products_list.filter(
                calories__lte=400,
                fat__lte=12
                # Removed sugar filter
            )
        elif goal == 'muscle_gain':
            products_list = products_list.filter(
                protein__gte=15,
                calories__gte=300  # Need enough calories for muscle building
            )
        elif goal == 'maintenance':
            products_list = products_list.filter(
                calories__range=(250, 550),
                protein__gte=8  # Moderate protein
            )
        elif goal == 'keto':
            products_list = products_list.filter(
                carbs__lte=10,  # Very low carbs for keto
                fat__gte=10      # Higher fat for keto
            )
        elif goal == 'low_carb':
            products_list = products_list.filter(
                carbs__lte=30,
                protein__gte=10
            )
        elif goal == 'high_protein':
            products_list = products_list.filter(
                protein__gte=20,
                fat__lte=15      # Lean protein sources
            )
        
        # Enhanced prompt-based filtering with only existing fields
        if prompt:
            prompt_lower = prompt.lower()
            
            # Define keyword categories with only available fields
            keyword_categories = {
                'protein': {
                    'keywords': ['protein', 'high protein', 'whey', 'casein', 'amino', 'muscle', 'gainer'],
                    'filter': {'protein__gte': 15},
                    'weight': 3
                },
                'low_carb': {
                    'keywords': ['low carb', 'keto', 'no carb', 'carb free', 'zero carb', 'atkins'],
                    'filter': {'carbs__lte': 15},
                    'weight': 3
                },
                'low_fat': {
                    'keywords': ['low fat', 'fat free', 'no fat', 'lean', 'light'],
                    'filter': {'fat__lte': 5},
                    'weight': 2
                },
                'high_fiber': {
                    'keywords': ['high fiber', 'fiber rich', 'digestion'],
                    'filter': {'fiber__gte': 3} if hasattr(products, 'fiber') else None,
                    'weight': 1
                },
                'low_calorie': {
                    'keywords': ['low calorie', 'diet', 'light', 'calorie conscious'],
                    'filter': {'calories__lte': 200},
                    'weight': 2
                }
            }
            
            # Apply filters based on keyword matches (only if filter exists)
            matched_categories = set()
            for category, data in keyword_categories.items():
                if data['filter'] and any(keyword in prompt_lower for keyword in data['keywords']):
                    try:
                        products_list = products_list.filter(**data['filter'])
                        matched_categories.add(category)
                    except Exception:
                        # Skip if field doesn't exist
                        pass
            
            # Check for specific food items
            food_keywords = {
                'chicken': ['chicken', 'poultry', 'broiler', 'breast'],
                'fish': ['fish', 'salmon', 'tuna', 'seafood', 'mackerel'],
                'egg': ['egg', 'eggs', 'omelette'],
                'milk': ['milk', 'dairy', 'yogurt', 'curd', 'cheese'],
                'rice': ['rice', 'brown rice', 'basmati'],
                'oats': ['oats', 'oatmeal', 'porridge'],
                'banana': ['banana', 'bananas'],
                'apple': ['apple', 'apples'],
                'broccoli': ['broccoli', 'broccolini'],
                'spinach': ['spinach', 'palak', 'leafy greens'],
                'almond': ['almond', 'almonds', 'badam'],
                'peanut': ['peanut', 'peanuts', 'groundnut']
            }
            
            for food, keywords in food_keywords.items():
                if any(keyword in prompt_lower for keyword in keywords):
                    products_list = products_list.filter(
                        Q(product_name__icontains=food) |
                        Q(description__icontains=food) |
                        Q(category__icontains=food)
                    )
            
            # General text search across multiple fields
            if not matched_categories and not any(k in prompt_lower for k in sum(food_keywords.values(), [])):
                # If no specific filters matched, do a general search
                products_list = products_list.filter(
                    Q(product_name__icontains=prompt) |
                    Q(description__icontains=prompt) |
                    Q(category__icontains=prompt)
                )
        
        # Get unique categories for filter dropdown
        categories = products.objects.values_list('category', flat=True).distinct()
        
        # Calculate relevance score for each product (using only available fields)
        scored_products = []
        for product in products_list:
            score = 0
            
            # BMI-based scoring
            if bmi and bmi_category:
                if bmi_category == 'Underweight' and product.calories > 400:
                    score += 10
                elif bmi_category == 'Overweight' and product.calories < 300:
                    score += 10
                elif bmi_category == 'Obese' and product.calories < 250:
                    score += 15
            
            # Goal-based scoring
            if goal == 'weight_loss':
                if product.calories < 200:
                    score += 15
                elif product.calories < 300:
                    score += 10
                if product.fat < 5:
                    score += 10
                if hasattr(product, 'fiber') and product.fiber and product.fiber > 3:
                    score += 5
                    
            elif goal == 'muscle_gain':
                if product.protein > 25:
                    score += 15
                elif product.protein > 20:
                    score += 10
                if product.calories > 400:
                    score += 10
                    
            elif goal == 'maintenance':
                if 300 <= product.calories <= 450:
                    score += 10
                if 10 <= product.protein <= 20:
                    score += 10
                    
            elif goal == 'keto':
                if product.carbs < 5:
                    score += 20
                elif product.carbs < 10:
                    score += 15
                if product.fat > 15:
                    score += 10
                    
            elif goal == 'high_protein':
                if product.protein > 30:
                    score += 20
                elif product.protein > 25:
                    score += 15
            
            # Price-based scoring (if price is reasonable)
            if product.price < 500:  # Lower price gets higher score
                score += 5
            elif product.price < 1000:
                score += 2
            
            # Prompt relevance scoring
            if prompt:
                prompt_lower = prompt.lower()
                product_name_lower = product.product_name.lower()
                description_lower = product.description.lower() if product.description else ''
                
                # Exact matches get highest score
                if prompt_lower in product_name_lower:
                    score += 30
                elif any(word in product_name_lower for word in prompt_lower.split() if len(word) > 2):
                    score += 20
                    
                if prompt_lower in description_lower:
                    score += 15
                    
                # Keyword matching
                prompt_words = set([w for w in prompt_lower.split() if len(w) > 2])
                name_words = set(product_name_lower.split())
                common_words = prompt_words.intersection(name_words)
                score += len(common_words) * 5
            
            # Nutritional profile scoring (using only available fields)
            if product.protein and product.protein > 10:
                score += 5
            if hasattr(product, 'fiber') and product.fiber and product.fiber > 3:
                score += 5
            if product.fat and product.fat < 5:
                score += 3
            
            scored_products.append((product, score))
        
        # Sort by score (highest first) and remove duplicates
        scored_products.sort(key=lambda x: x[1], reverse=True)
        final_products = [p for p, score in scored_products]
        
        # Get cart count for logged in user
        cart_count = 0
        user_email = None
        if 'uid' in request.session:
            user_email = request.session['uid']
            cart_count = Cart.objects.filter(user_email=user_email).count()
        
        # Prepare context with enhanced data
        context = {
            'products': final_products,
            'categories': categories,
            'bmi': bmi,
            'bmi_category': bmi_category,
            'recommended_calories': recommended_calories,
            'recommended_protein': recommended_protein,
            'goal': goal,
            'prompt': prompt,
            'total_products': len(final_products),
            'cart_count': cart_count,
            'user_email': user_email,
            'filters_applied': {
                'goal': goal,
                'has_prompt': bool(prompt),
                'has_bmi': bmi is not None
            }
        }
        return render(request, 'user-search.html', context)
    
    return redirect('openserch')

# Cart Views
def add_to_cart(request):
    if request.method == 'POST' and 'uid' in request.session:
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        user_email = request.session['uid']
        
        product = get_object_or_404(products, id=product_id)
        
        cart_item, created = Cart.objects.get_or_create(
            user_email=user_email,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
            message = f'Updated {product.product_name} quantity'
        else:
            message = f'Added {product.product_name} to cart'
        
        cart_count = Cart.objects.filter(user_email=user_email).count()
        
        # Always return JSON for AJAX requests
        return JsonResponse({
            'success': True,
            'message': message,
            'cart_count': cart_count
        })
    
    return JsonResponse({
        'success': False,
        'error': 'Please login to add items to cart'
    }, status=401)

def view_cart(request):
    if 'uid' in request.session:
        user_email = request.session['uid']
        cart_items = Cart.objects.filter(user_email=user_email).select_related('product')
        
        subtotal = sum(float(item.total_price) for item in cart_items)
        platform_fee = 50.0
        total = subtotal + platform_fee
        
        context = {
            'cart_items': cart_items,
            'subtotal': subtotal,
            'total': total,
            'cart_count': cart_items.count(),
            'user_email': user_email,
        }
        return render(request, 'cart.html', context)
    
    messages.error(request, 'Please login to view cart')
    return redirect('login')

def update_cart_quantity(request):
    if request.method == 'POST' and 'uid' in request.session:
        try:
            cart_id = request.POST.get('cart_id')
            action = request.POST.get('action')
            
            if not cart_id or not action:
                return JsonResponse({'success': False, 'error': 'Missing parameters'})
            
            cart_item = get_object_or_404(Cart, id=cart_id, user_email=request.session['uid'])
            product_price = float(cart_item.product.price)
            
            if action == 'increase':
                cart_item.quantity += 1
                cart_item.save()
                message = 'Quantity increased'
            elif action == 'decrease':
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    cart_item.save()
                    message = 'Quantity decreased'
                else:
                    cart_item.delete()
                    message = 'Item removed from cart'
            elif action == 'remove':
                cart_item.delete()
                message = 'Item removed from cart'
            else:
                return JsonResponse({'success': False, 'error': 'Invalid action'})
            
            # Get updated cart data
            cart_items = Cart.objects.filter(user_email=request.session['uid']).select_related('product')
            subtotal = sum(float(item.total_price) for item in cart_items)
            platform_fee = 50.0
            total = subtotal + platform_fee
            cart_count = cart_items.count()
            
            # Prepare response data
            response_data = {
                'success': True,
                'message': message,
                'cart_count': cart_count,
                'subtotal': subtotal,
                'total': total,
            }
            
            # If item still exists, include its data
            if action != 'remove' and cart_item.id:
                response_data['quantity'] = cart_item.quantity
                response_data['item_total'] = float(cart_item.quantity * product_price)
            
            return JsonResponse(response_data)
            
        except Cart.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Cart item not found'})
        except Exception as e:
            print(f"Error in update_cart_quantity: {e}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Please login'}, status=401)


def remove_from_cart(request, cart_id):
    if 'uid' in request.session:
        cart_item = get_object_or_404(Cart, id=cart_id, user_email=request.session['uid'])
        product_name = cart_item.product.product_name
        cart_item.delete()
        
        messages.success(request, f'{product_name} removed from cart')
        return redirect('view_cart')
    
    return redirect('login')

def get_cart_count(request):
    """API endpoint to get cart count for AJAX"""
    if 'uid' in request.session:
        count = Cart.objects.filter(user_email=request.session['uid']).count()
        return JsonResponse({'count': count})
    return JsonResponse({'count': 0})

def ai_real_search(request):
    meals = []
    note = ""

    if request.method == "POST":
        weight = float(request.POST['weight'])
        height = float(request.POST['height']) / 100
        prompt = request.POST.get('prompt', '')
        dropdown_goal = request.POST['goal']

        bmi = round(weight / (height * height), 2)

        # 🔥 REAL AI DECISION
        final_goal = get_ai_goal(prompt, dropdown_goal)

        note = f"AI understood your goal as: {final_goal.replace('_', ' ').title()}"

        meals = products.objects.filter(category__icontains=final_goal)

    return render(request, "user-search.html", {
        "meals": meals,
        "bmi": bmi,
        "note": note
    })

def detect_goal_from_prompt(prompt):
    if not prompt:
        return None

    prompt = prompt.lower()

    if any(word in prompt for word in ['lose', 'loss', 'fat', 'slim', 'reduce', 'cut']):
        return 'weight_loss'

    if any(word in prompt for word in ['gain', 'muscle', 'bulk', 'increase']):
        return 'muscle_gain'

    if any(word in prompt for word in ['keto']):
        return 'keto'

    if any(word in prompt for word in ['protein', 'high protein']):
        return 'high_protein'

    if any(word in prompt for word in ['vegan']):
        return 'vegan'

    if any(word in prompt for word in ['low carb']):
        return 'low_carb'

    return None

def search_product(request):
    meals = []

    if request.method == "POST":
        goal = request.POST.get("goal")
        prompt = request.POST.get("prompt", "").lower()
        weight = float(request.POST['weight'])
        height = float(request.POST['height']) / 100
        

        # Detect intent from prompt
        prompt_category = detect_goal_from_prompt(prompt)
        bmi = round(weight / (height * height), 2)
        print("Detected from Prompt:", prompt_category)
        # Decide final category
        if prompt_category:
            final_category = prompt_category   # Prompt wins
        else:
            final_category = goal              # Dropdown used
        print("Final Category:", final_category)
        # Fetch products
        meals = products.objects.filter(
            category__icontains=final_category
        )

    return render(request, "user-search.html", {
        "meals": meals,
        "bmi": bmi
    })

def calculate_price(product, plan):
    if plan == 'single':
        return product.price
    elif plan == 'weekly':
        return product.price * 7
    elif plan == 'monthly':
        return product.price * 30

def generate_order_id():
    """Generate unique order ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"FB{timestamp}{random_str}"

def calculate_price(product, plan):
    """Calculate total price based on plan"""
    if plan == 'single':
        return product.price
    elif plan == 'weekly':
        return product.price * 7
    elif plan == 'monthly':
        return product.price * 30
    return product.price

def place_order(request, product_id):
    # Get product
    product = get_object_or_404(products, id=product_id)

    if 'uid' not in request.session:
        return redirect('login')

    customer = user.objects.get(email=request.session['uid'])

    if request.method == "POST":
        plan = request.POST.get('plan', 'single')
        quantity = int(request.POST.get('quantity', 1))
        start_date_str = request.POST.get('start_date')
        
        # Calculate price based on plan
        if plan == 'weekly':
            total_amount = product.price * 7 * quantity
        elif plan == 'monthly':
            total_amount = product.price * 30 * quantity
        else:
            total_amount = product.price * quantity
        
        # Calculate dates
        start_date = timezone.now().date()
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except:
                start_date = timezone.now().date()
        
        if plan == 'weekly':
            end_date = start_date + timedelta(days=7)
        elif plan == 'monthly':
            end_date = start_date + timedelta(days=30)
        else:
            end_date = start_date
        
        # Check stock
        if quantity > product.stock_quantity:
            messages.error(request, f'Only {product.stock_quantity} items available')
            return redirect('place_order', product_id=product.id)
        
        # Create order
        order = Orders.objects.create(
            customer=customer,
            seller=product.seller,
            order_id=generate_order_id(),
            full_name=request.POST.get('full_name', customer.name),
            phone=request.POST.get('phone', customer.phone),
            address=request.POST.get('address', customer.address),
            city=request.POST.get('city', ''),
            state=request.POST.get('state', ''),
            pincode=request.POST.get('pincode', ''),
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            total_amount=total_amount,
            payment_status='pending',
            order_status='pending'
        )
        
        # Create order item
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity
        )
        
        # Reduce stock
        product.stock_quantity -= quantity
        product.save()
        print(product.seller,'ps')
        
        # Send email with ALL 4 parameters
        try:
            # Pass product.seller as the 4th parameter
            send_invoice_email(order, customer, product, product.seller)
            messages.success(request, '✅ Order created! Invoice sent to your email.')
        except Exception as e:
            print(f"Email error: {e}")
            messages.success(request, '✅ Order created! (Email sending failed)')
        
        return redirect('initiate_payment', order_id=order.id)

    return render(request, "place_order.html", {
        "product": product,
        "today": timezone.now().date()
    })
def initiate_payment(request, order_id):
    """Initiate Razorpay payment"""
    order = get_object_or_404(Orders, id=order_id)
    
    if 'uid' not in request.session or order.customer.email != request.session['uid']:
        messages.error(request, 'Unauthorized access')
        return redirect('login')
    
    try:
        # Create Razorpay order
        razorpay_order = razorpay_client.order.create({
            "amount": int(order.total_amount * 100),
            "currency": "INR",
            "payment_capture": 1
        })
        
        # Save Razorpay order ID
        order.razorpay_order_id = razorpay_order['id']
        order.save()
        
        context = {
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'razorpay_order_id': razorpay_order['id'],
            'amount': order.total_amount,
            'order': order
        }
        return render(request, 'payment_page.html', context)
        
    except Exception as e:
        messages.error(request, f'Payment initiation failed: {str(e)}')
        return redirect('order_detail', order_id=order.id)

def payment_success(request):
    """Handle successful payment"""
    payment_id = request.GET.get('razorpay_payment_id')
    order_id = request.GET.get('razorpay_order_id')
    signature = request.GET.get('razorpay_signature')
    
    try:
        order = Orders.objects.get(razorpay_order_id=order_id)
        
        # Verify signature
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Update order
        order.payment_status = 'paid'
        order.order_status = 'confirmed'
        order.save()
        
        messages.success(request, 'Payment successful! Your order is confirmed.')
        return redirect('order_tracking', order_id=order.id)
        
    except Exception as e:
        messages.error(request, f'Payment verification failed: {str(e)}')
        return redirect('order_detail', order_id=order.id if 'order' in locals() else 'home')

def order_history(request):
    """View order history"""
    if 'uid' not in request.session:
        return redirect('login')
    
    customer = get_object_or_404(user, email=request.session['uid'])
    orders = Orders.objects.filter(customer=customer).order_by('-order_date')
    
    return render(request, 'order_history.html', {'orders': orders})

# def order_detail(request, order_id):
#     """View single order details with items"""
#     # Get the order
#     order = get_object_or_404(Orders, id=order_id)
    
#     # Check if user is logged in and authorized
#     if 'uid' not in request.session or order.customer.email != request.session['uid']:
#         messages.error(request, 'Unauthorized access')
#         return redirect('login')
    
#     # Get order items with product details
#     order_items = OrderItem.objects.filter(order=order).select_related('product')
    
#     # Calculate days remaining if order is active
#     days_remaining = None
#     if order.end_date and order.order_status not in ['delivered', 'cancelled']:
#         from django.utils import timezone
#         today = timezone.now().date()
#         if order.end_date >= today:
#             days_remaining = (order.end_date - today).days
    
#     # Get cart count for navbar
#     from .models import Cart
#     cart_count = Cart.objects.filter(user_email=request.session['uid']).count()
#     print('order_items',order_items)
#     context = {
#         'order': order,
#         'order_items': order_items,
#         'days_remaining': days_remaining,
#         'user_email': request.session['uid'],
#         'cart_count': cart_count,
#     }
    
#     return render(request, 'order_detail.html', context)

def order_tracking(request, order_id):
    """Track order status"""
    order = get_object_or_404(Orders, id=order_id)
    
    if 'uid' not in request.session or order.customer.email != request.session['uid']:
        messages.error(request, 'Unauthorized access')
        return redirect('login')
    
    # Status progression
    status_flow = ['pending', 'confirmed', 'prepared', 'dispatched', 'delivered']
    current_index = status_flow.index(order.order_status) if order.order_status in status_flow else -1
    
    return render(request, 'order_tracking.html', {
        'order': order,
        'status_flow': status_flow,
        'current_index': current_index
    })

def cancel_order(request, order_id):
    """Cancel an order"""
    order = get_object_or_404(Orders, id=order_id)
    
    if 'uid' not in request.session or order.customer.email != request.session['uid']:
        messages.error(request, 'Unauthorized access')
        return redirect('login')
    
    if request.method == "POST":
        if order.order_status in ['pending', 'confirmed']:
            order.order_status = 'cancelled'
            if order.payment_status == 'paid':
                order.payment_status = 'refunded'
            order.save()
            messages.success(request, 'Order cancelled successfully')
        else:
            messages.error(request, 'Order cannot be cancelled at this stage')
        
        return redirect('order_detail', order_id=order.id)
    
    return render(request, 'confirm_cancel.html', {'order': order})


def order_history(request):
    """
    View to display user's order history
    URL: /my-orders/
    """
    # Check if user is logged in
    if 'uid' not in request.session:
        messages.warning(request, 'Please login to view your orders')
        return redirect('login')
    
    try:
        # Get customer from session
        customer = user.objects.get(email=request.session['uid'])
        
        # Get all orders for this customer, ordered by latest first
        orders = Orders.objects.filter(customer=customer).order_by('-order_date')
        
        # Count orders by status for statistics
        total_orders = orders.count()
        pending_orders = orders.filter(order_status='pending').count()
        delivered_orders = orders.filter(order_status='delivered').count()
        cancelled_orders = orders.filter(order_status='cancelled').count()
        
        context = {
            'orders': orders,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'delivered_orders': delivered_orders,
            'cancelled_orders': cancelled_orders,
        }
        
        return render(request, 'order_history.html', context)
        
    except user.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('login')
    except Exception as e:
        messages.error(request, f'Error loading orders: {str(e)}')
        return redirect('home')

def order_detail(request, order_id):
    """View single order details with items"""
    # Get the order
    print('order_id',order_id)
    order = get_object_or_404(Orders, id=order_id)
    print('order',order)
    # Check if user is logged in and authorized
    if 'uid' not in request.session or order.customer.email != request.session['uid']:
        messages.error(request, 'Unauthorized access')
        return redirect('login')
    
    # Get order items with product details
    order_items = OrderItem.objects.filter(order=order).select_related('product')
    print('order_items',order_items)
    # Calculate days remaining if order is active
    days_remaining = None
    if order.end_date and order.order_status not in ['delivered', 'cancelled']:
        from django.utils import timezone
        today = timezone.now().date()
        if order.end_date >= today:
            days_remaining = (order.end_date - today).days
    
    # Get cart count for navbar
    from .models import Cart
    cart_count = Cart.objects.filter(user_email=request.session['uid']).count()
    print('order_items',order_items)
    context = {
        'order': order,
        'order_items': order_items,
        'days_remaining': days_remaining,
        'user_email': request.session['uid'],
        'cart_count': cart_count,
    }
    
    return render(request, 'order_detail.html', context)

def cancel_order(request, order_id):
    """
    View to cancel an order
    URL: /order/<order_id>/cancel/
    """
    # Check if user is logged in
    if 'uid' not in request.session:
        messages.warning(request, 'Please login to cancel order')
        return redirect('login')
    
    try:
        # Get the order
        order = get_object_or_404(Orders, id=order_id)
        
        # Verify that this order belongs to the logged-in user
        if order.customer.email != request.session['uid']:
            messages.error(request, 'You are not authorized to cancel this order')
            return redirect('order_history')
        
        # Check if order can be cancelled (only pending or confirmed orders)
        if order.order_status not in ['pending', 'confirmed']:
            messages.error(request, f'This order cannot be cancelled as it is {order.get_order_status_display()}')
            return redirect('order_detail', order_id=order.id)
        
        if request.method == "POST":
            # Get cancellation reason
            cancel_reason = request.POST.get('cancel_reason', 'No reason provided')
            
            # Update order status
            order.order_status = 'cancelled'
            
            # If payment was made, mark for refund
            if order.payment_status == 'paid':
                order.payment_status = 'refunded'
                messages.success(request, 'Order cancelled successfully. Your refund will be processed within 5-7 business days.')
            else:
                messages.success(request, 'Order cancelled successfully.')
            
            # You can add a field for cancellation reason if you want
            # order.cancel_reason = cancel_reason
            order.save()
            
            return redirect('order_detail', order_id=order.id)
        
        # GET request - show confirmation page
        context = {
            'order': order,
        }
        return render(request, 'confirm_cancel.html', context)
        
    except Orders.DoesNotExist:
        messages.error(request, 'Order not found')
        return redirect('order_history')
    except Exception as e:
        messages.error(request, f'Error cancelling order: {str(e)}')
        return redirect('order_detail', order_id=order_id)

def order_tracking(request, order_id):
    """
    View to track order status
    URL: /order/<order_id>/track/
    """
    # Check if user is logged in
    if 'uid' not in request.session:
        messages.warning(request, 'Please login to track order')
        return redirect('login')
    
    try:
        # Get the order
        order = get_object_or_404(Orders, id=order_id)
        
        # Verify that this order belongs to the logged-in user
        if order.customer.email != request.session['uid']:
            messages.error(request, 'You are not authorized to track this order')
            return redirect('order_history')
        
        # Define status flow for tracking
        status_flow = ['pending', 'confirmed', 'prepared', 'dispatched', 'delivered']
        status_colors = {
            'pending': '#ffc107',
            'confirmed': '#17a2b8',
            'prepared': '#007bff',
            'dispatched': '#6f42c1',
            'delivered': '#28a745',
            'cancelled': '#dc3545'
        }
        
        # Get current status index
        current_index = -1
        if order.order_status in status_flow:
            current_index = status_flow.index(order.order_status)
        
        # Calculate progress percentage
        if order.order_status == 'cancelled':
            progress_percentage = 0
        elif current_index >= 0:
            progress_percentage = ((current_index + 1) / len(status_flow)) * 100
        else:
            progress_percentage = 0
        
        # Estimated delivery (if order is active)
        estimated_delivery = None
        if order.order_status not in ['delivered', 'cancelled'] and order.end_date:
            estimated_delivery = order.end_date
        
        context = {
            'order': order,
            'status_flow': status_flow,
            'status_colors': status_colors,
            'current_index': current_index,
            'progress_percentage': progress_percentage,
            'estimated_delivery': estimated_delivery,
        }
        
        return render(request, 'order_tracking.html', context)
        
    except Orders.DoesNotExist:
        messages.error(request, 'Order not found')
        return redirect('order_history')
    except Exception as e:
        messages.error(request, f'Error tracking order: {str(e)}')
        return redirect('order_detail', order_id=order_id)

def reorder(request, order_id):
    """
    View to reorder a previous order
    URL: /order/<order_id>/reorder/
    """
    # Check if user is logged in
    if 'uid' not in request.session:
        messages.warning(request, 'Please login to reorder')
        return redirect('login')
    
    try:
        # Get the previous order
        previous_order = get_object_or_404(Orders, id=order_id)
        
        # Verify ownership
        if previous_order.customer.email != request.session['uid']:
            messages.error(request, 'Unauthorized')
            return redirect('order_history')
        
        # Create new order with same details but new dates
        from datetime import datetime, timedelta
        from .models import products
        
        # You need to get the product - this depends on your product model
        # Assuming you have a way to get the product from the order
        # product = previous_order.product  # If you add product field to Orders
        
        messages.success(request, 'Please place your order again with current dates')
        
        # Redirect to place order page with product
        # return redirect('place_order', product_id=product.id)
        return redirect('order_history')
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('order_history')


def seller_orders(request):
    """
    View for sellers to see all orders containing their products
    URL: /seller-orders/
    """
    # Check if seller is logged in
    if 'seller_id' not in request.session:
        messages.warning(request, 'Please login to view orders')
        return redirect('seller_login')
    
    try:
        seller = Seller.objects.get(id=request.session['seller_id'])
        
        # Get filter parameters
        status_filter = request.GET.get('status', 'all')
        date_filter = request.GET.get('date', 'all')
        search_query = request.GET.get('search', '')
        
        # Base query - Get all orders that have this seller's products
        # Using OrderItem to find orders containing seller's products
        seller_product_ids = products.objects.filter(seller=seller).values_list('id', flat=True)
        order_items = OrderItem.objects.filter(product_id__in=seller_product_ids)
        order_ids = order_items.values_list('order_id', flat=True).distinct()
        
        orders = Orders.objects.filter(id__in=order_ids).order_by('-order_date')
        
        # Apply filters
        if status_filter != 'all':
            orders = orders.filter(order_status=status_filter)
        
        # Date filter
        today = datetime.now().date()
        if date_filter == 'today':
            orders = orders.filter(order_date__date=today)
        elif date_filter == 'week':
            week_ago = today - timedelta(days=7)
            orders = orders.filter(order_date__date__gte=week_ago)
        elif date_filter == 'month':
            month_ago = today - timedelta(days=30)
            orders = orders.filter(order_date__date__gte=month_ago)
        
        # Search filter
        if search_query:
            orders = orders.filter(
                Q(order_id__icontains=search_query) |
                Q(full_name__icontains=search_query) |
                Q(phone__icontains=search_query)
            )
        
        # Get statistics
        total_orders = orders.count()
        pending_count = orders.filter(order_status='pending').count()
        confirmed_count = orders.filter(order_status='confirmed').count()
        prepared_count = orders.filter(order_status='prepared').count()
        dispatched_count = orders.filter(order_status='dispatched').count()
        delivered_count = orders.filter(order_status='delivered').count()
        cancelled_count = orders.filter(order_status='cancelled').count()
        
        # Calculate total revenue (only paid orders)
        total_revenue = orders.filter(payment_status='paid').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        context = {
            'seller': seller,
            'orders': orders,
            'total_orders': total_orders,
            'pending_count': pending_count,
            'confirmed_count': confirmed_count,
            'prepared_count': prepared_count,
            'dispatched_count': dispatched_count,
            'delivered_count': delivered_count,
            'cancelled_count': cancelled_count,
            'total_revenue': total_revenue,
            'status_filter': status_filter,
            'date_filter': date_filter,
            'search_query': search_query,
        }
        
        return render(request, 'seller_orders.html', context)
        
    except Seller.DoesNotExist:
        messages.error(request, 'Seller not found')
        return redirect('seller_login')
    except Exception as e:
        messages.error(request, f'Error loading orders: {str(e)}')
        return redirect('seller_dashboard')

def seller_order_detail(request, order_id):
    """
    View for sellers to see detailed order information
    URL: /seller-order/<order_id>/
    """
    # Check if seller is logged in
    if 'seller_id' not in request.session:
        messages.warning(request, 'Please login to view order details')
        return redirect('seller_login')
    
    try:
        seller = Seller.objects.get(id=request.session['seller_id'])
        
        # Get the order
        order = get_object_or_404(Orders, id=order_id)
        
        # Verify that this order contains seller's products
        seller_product_ids = products.objects.filter(seller=seller).values_list('id', flat=True)
        order_items = OrderItem.objects.filter(order=order, product_id__in=seller_product_ids)
        
        if not order_items.exists():
            messages.error(request, 'This order does not contain your products')
            return redirect('seller_orders')
        
        # Get all items in this order (including other sellers' products)
        all_items = OrderItem.objects.filter(order=order).select_related('product', 'product__seller')
        
        # Separate seller's items from other items
        seller_items = order_items.select_related('product')
        other_items = all_items.exclude(product_id__in=seller_product_ids)
        
        # Calculate totals
        subtotal = sum(item.product.price * item.quantity for item in all_items)
        
        context = {
            'seller': seller,
            'order': order,
            'seller_items': seller_items,
            'other_items': other_items,
            'all_items': all_items,
            'subtotal': subtotal,
        }
        
        return render(request, 'seller_order_detail.html', context)
        
    except Seller.DoesNotExist:
        messages.error(request, 'Seller not found')
        return redirect('seller_login')
    except Exception as e:
        messages.error(request, f'Error loading order details: {str(e)}')
        return redirect('seller_orders')

def update_order_status(request, order_id):
    """
    View to update order status (AJAX or POST)
    URL: /update-order-status/<order_id>/
    """
    if request.method == 'POST':
        if 'seller_id' not in request.session:
            return JsonResponse({'success': False, 'error': 'Not authenticated'})
        
        try:
            seller = Seller.objects.get(id=request.session['seller_id'])
            order = get_object_or_404(Orders, id=order_id)
            
            # Verify order contains seller's products
            seller_product_ids = products.objects.filter(seller=seller).values_list('id', flat=True)
            if not OrderItem.objects.filter(order=order, product_id__in=seller_product_ids).exists():
                return JsonResponse({'success': False, 'error': 'Unauthorized'})
            
            new_status = request.POST.get('status')
            if new_status in dict(Orders.ORDER_STATUS_CHOICES):
                order.order_status = new_status
                order.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Order status updated to {order.get_order_status_display()}',
                    'new_status': order.get_order_status_display()
                })
            else:
                return JsonResponse({'success': False, 'error': 'Invalid status'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def seller_order_stats(request):
    """
    API endpoint for order statistics (for charts)
    URL: /seller-order-stats/
    """
    if 'seller_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'Not authenticated'})
    
    try:
        seller = Seller.objects.get(id=request.session['seller_id'])
        
        # Get seller's product IDs
        seller_product_ids = products.objects.filter(seller=seller).values_list('id', flat=True)
        
        # Get orders containing seller's products
        order_ids = OrderItem.objects.filter(
            product_id__in=seller_product_ids
        ).values_list('order_id', flat=True).distinct()
        
        orders = Orders.objects.filter(id__in=order_ids)
        
        # Stats by status
        status_counts = {}
        for status_code, status_label in Orders.ORDER_STATUS_CHOICES:
            count = orders.filter(order_status=status_code).count()
            if count > 0:
                status_counts[status_label] = count
        
        # Orders by date (last 7 days)
        last_7_days = []
        today = datetime.now().date()
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            count = orders.filter(order_date__date=date).count()
            last_7_days.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        
        return JsonResponse({
            'success': True,
            'status_counts': status_counts,
            'last_7_days': last_7_days,
            'total_orders': orders.count(),
            'total_revenue': float(orders.filter(payment_status='paid').aggregate(
                total=Sum('total_amount')
            )['total'] or 0)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


from django.http import JsonResponse

def cart_data(request):
    """API endpoint to get cart data for AJAX"""
    if 'uid' in request.session:
        cart_items = Cart.objects.filter(user_email=request.session['uid']).select_related('product')
        items_data = []
        subtotal = 0
        
        for item in cart_items:
            item_total = float(item.total_price)
            subtotal += item_total
            items_data.append({
                'id': item.id,
                'name': item.product.product_name,
                'price': float(item.product.price),
                'quantity': item.quantity,
                'image': item.product.image.url if item.product.image else 'https://via.placeholder.com/80x80?text=No+Image',
                'item_total': item_total
            })
        
        platform_fee = 50.0
        total = subtotal + platform_fee
        
        return JsonResponse({
            'success': True,
            'items': items_data,
            'subtotal': subtotal,
            'total': total,
            'count': len(cart_items)
        })
    return JsonResponse({'success': False, 'items': [], 'subtotal': 0, 'total': 0, 'count': 0})

def clear_cart(request):
    if request.method == 'POST' and 'uid' in request.session:
        try:
            Cart.objects.filter(user_email=request.session['uid']).delete()
            return JsonResponse({'success': True, 'message': 'Cart cleared successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})



from django.db import transaction
from datetime import datetime, timedelta
import random
import string

def checkout_from_cart(request):
    """Checkout page from cart"""
    if 'uid' not in request.session:
        messages.warning(request, 'Please login to checkout')
        return redirect('login')
    
    try:
        user_email = request.session['uid']
        customer = user.objects.get(email=user_email)
        
        # Get cart items
        cart_items = Cart.objects.filter(user_email=user_email).select_related('product')
        
        if not cart_items.exists():
            messages.error(request, 'Your cart is empty')
            return redirect('view_cart')
        
        # Calculate subtotal - ensure it's Decimal
        subtotal = sum((item.product.price * item.quantity) for item in cart_items)
        
        # Convert shipping to Decimal
        shipping = Decimal('50.00')
        
        # Calculate total (both are now Decimal)
        total = subtotal + shipping
        
        # Get unique sellers from cart items
        sellers = set(item.product.seller for item in cart_items)
        
        # Check stock availability
        out_of_stock = []
        for item in cart_items:
            if item.quantity > item.product.stock_quantity:
                out_of_stock.append(f"{item.product.product_name} (only {item.product.stock_quantity} available)")
        
        if out_of_stock:
            messages.error(request, f"Out of stock: {', '.join(out_of_stock)}")
            return redirect('view_cart')
        
        # Get cart count
        cart_count = cart_items.count()
        
        context = {
            'customer': customer,
            'cart_items': cart_items,
            'subtotal': subtotal,
            'shipping': shipping,
            'total': total,
            'cart_count': cart_count,
            'sellers': sellers,
            'today': timezone.now().date(),
        }
        return render(request, 'checkout.html', context)
        
    except user.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('login')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('view_cart')
        
    except user.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('login')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('view_cart')
        
    except user.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('login')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('view_cart')

def generate_order_id():
    """Generate unique order ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"FB{timestamp}{random_str}"


@transaction.atomic
def place_order_from_cart(request):
    """Place order from cart items with stock reduction"""
    if request.method == 'POST' and 'uid' in request.session:
        try:
            user_email = request.session['uid']
            customer = user.objects.get(email=user_email)
            
            # Get cart items
            cart_items = Cart.objects.filter(user_email=user_email).select_related('product')
            
            if not cart_items.exists():
                messages.error(request, 'Your cart is empty')
                return redirect('view_cart')
            
            # Get form data
            full_name = request.POST.get('full_name')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            city = request.POST.get('city')
            state = request.POST.get('state')
            pincode = request.POST.get('pincode')
            plan = request.POST.get('plan', 'single')
            start_date_str = request.POST.get('start_date')
            
            # Validate required fields
            if not all([full_name, phone, address, city, state, pincode, plan]):
                messages.error(request, 'All fields are required')
                return redirect('checkout_from_cart')
            
            # Group items by seller
            from collections import defaultdict
            seller_items = defaultdict(list)
            for item in cart_items:
                seller_items[item.product.seller].append(item)
            
            orders_created = []
            
            # Calculate dates
            start_date = timezone.now().date()
            if start_date_str:
                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                except:
                    start_date = timezone.now().date()
            
            if plan == 'weekly':
                end_date = start_date + timedelta(days=7)
            elif plan == 'monthly':
                end_date = start_date + timedelta(days=30)
            else:
                end_date = start_date
            
            # Plan multipliers
            plan_multipliers = {
                'single': 1,
                'weekly': 7,
                'monthly': 30
            }
            multiplier = plan_multipliers.get(plan, 1)
            
            # Verify stock availability
            for item in cart_items:
                if item.quantity > item.product.stock_quantity:
                    messages.error(request, f"{item.product.product_name} is out of stock")
                    return redirect('view_cart')
            
            # Create orders for each seller
            for seller, items in seller_items.items():
                # Calculate seller subtotal
                seller_subtotal = Decimal('0')
                for item in items:
                    seller_subtotal += item.product.price * item.quantity
                
                # Calculate seller total with shipping divided equally
                seller_shipping = Decimal('50.00') / Decimal(len(seller_items))
                seller_total = (seller_subtotal * Decimal(multiplier)) + seller_shipping
                
                # Create order for this seller
                order = Orders.objects.create(
                    customer=customer,
                    seller=seller,
                    order_id=generate_order_id(),
                    full_name=full_name,
                    phone=phone,
                    address=address,
                    city=city,
                    state=state,
                    pincode=pincode,
                    plan=plan,
                    start_date=start_date,
                    end_date=end_date,
                    total_amount=seller_total,
                    payment_status='pending',
                    order_status='pending'
                )
                
                # Create order items and reduce stock
                for item in items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity
                    )
                    
                    # Reduce stock
                    item.product.stock_quantity -= item.quantity
                    item.product.save()
                
                orders_created.append(order)
            
            # Clear cart
            cart_items.delete()
            
            # Send invoice emails - FIXED VERSION
            try:
                from .utils.pdf_utils import send_invoice_email
                
                email_count = 0
                for order in orders_created:
                    order_items = OrderItem.objects.filter(order=order)
                    
                    for item in order_items:
                        # ✅ Pass all 4 required parameters
                        result = send_invoice_email(order, customer, item.product, order.seller)
                        if result:
                            email_count += 1
                    
                    # Alternative: Send one email per order (if you modify send_invoice_email)
                    # send_invoice_email(order, customer, [item.product for item in order_items], order.seller)
                
                if email_count > 0:
                    messages.success(request, f'✅ Orders created! {email_count} invoice(s) sent to your email.')
                else:
                    messages.success(request, '✅ Orders created! (Invoice emails could not be sent)')
                    
            except Exception as e:
                print(f"❌ Email error in place_order_from_cart: {e}")
                import traceback
                traceback.print_exc()
                messages.success(request, '✅ Orders created! (Email sending failed)')
            
            # Redirect to payment for first order
            return redirect('initiate_payment', order_id=orders_created[0].id)
            
        except user.DoesNotExist:
            messages.error(request, 'User not found')
            return redirect('login')
        except Exception as e:
            print(f"❌ Error in place_order_from_cart: {e}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error placing order: {str(e)}')
            return redirect('checkout_from_cart')
    
    return redirect('checkout_from_cart')

def initiate_payment(request, order_id):
    """Initiate Razorpay payment"""
    order = get_object_or_404(Orders, id=order_id)
    
    if 'uid' not in request.session or order.customer.email != request.session['uid']:
        messages.error(request, 'Unauthorized access')
        return redirect('login')
    
    try:
        # Create Razorpay order
        razorpay_order = razorpay_client.order.create({
            "amount": int(order.total_amount * 100),  # Convert to paise
            "currency": "INR",
            "payment_capture": 1
        })
        
        # Save Razorpay order ID
        order.razorpay_order_id = razorpay_order['id']
        order.save()
        
        context = {
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'razorpay_order_id': razorpay_order['id'],
            'amount': order.total_amount,
            'amount_paise': int(order.total_amount * 100),
            'order': order,
            'customer_name': order.full_name,
            'customer_email': order.customer.email,
            'customer_phone': order.phone
        }
        return render(request, 'payment_page.html', context)
        
    except Exception as e:
        messages.error(request, f'Payment initiation failed: {str(e)}')
        return redirect('order_detail', order_id=order.id)
def payment_success(request):
    """Handle successful payment"""
    payment_id = request.GET.get('razorpay_payment_id')
    order_id = request.GET.get('razorpay_order_id')
    signature = request.GET.get('razorpay_signature')
    
    try:
        order = Orders.objects.get(razorpay_order_id=order_id)
        
        # Verify signature
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        
        # Verify payment signature
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Update order
        order.payment_status = 'paid'
        order.order_status = 'confirmed'
        order.save()
        
        messages.success(request, 'Payment successful! Your order is confirmed.')
        return render(request, 'payment_success.html', {'order': order})
        
    except Exception as e:
        messages.error(request, f'Payment verification failed: {str(e)}')
        return redirect('order_detail', order_id=order.id if 'order' in locals() else None)

def payment_failure(request):
    """Handle payment failure"""
    order_id = request.GET.get('order_id')
    
    try:
        order = Orders.objects.get(id=order_id)
        order.payment_status = 'failed'
        order.save()
        
        return render(request, 'payment_failure.html', {'order': order})
        
    except Orders.DoesNotExist:
        messages.error(request, 'Order not found')
        return redirect('home')

# Add these missing seller functions after your existing seller_orders function

def seller_inventory(request):
    """View for seller inventory"""
    # Check if seller is logged in - check both possible session keys
    seller_id = None
    if 'seller_id' in request.session:
        seller_id = request.session['seller_id']
    elif 'sid' in request.session:
        seller_id = request.session['sid']
    else:
        messages.warning(request, 'Please login to view inventory')
        return redirect('seller_login')
    
    try:
        # Try to get seller by ID first, then by email if needed
        try:
            seller = Seller.objects.get(id=seller_id)
        except (Seller.DoesNotExist, ValueError):
            # If seller_id is email string instead of ID
            seller = Seller.objects.get(email=seller_id)
        
        # Get all products for this seller
        products_list = products.objects.filter(seller=seller).order_by('-id')
        
        # Calculate statistics
        total_products = products_list.count()
        
        # Calculate total stock safely
        stock_agg = products_list.aggregate(Sum('stock_quantity'))
        total_stock = stock_agg['stock_quantity__sum'] or 0
        
        # Calculate total value
        total_value = 0
        for product in products_list:
            total_value += product.price * product.stock_quantity
        
        # Low stock products (less than 10 items)
        low_stock_count = products_list.filter(stock_quantity__lt=10).count()
        out_of_stock_count = products_list.filter(stock_quantity=0).count()
        
        # Pagination
        paginator = Paginator(products_list, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'seller': seller,
            'products': page_obj,
            'total_products': total_products,
            'total_stock': total_stock,
            'total_value': total_value,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
        }
        return render(request, 'seller_inventory.html', context)
        
    except Seller.DoesNotExist:
        messages.error(request, 'Seller not found. Please login again.')
        return redirect('seller_login')
    except Exception as e:
        messages.error(request, f'Error loading inventory: {str(e)}')
        return redirect('seller_dashboard')

def seller_profile(request):
    """View and edit seller profile"""
    # Check if seller is logged in
    if 'seller_id' not in request.session:
        messages.warning(request, 'Please login to view profile')
        return redirect('seller_login')
    
    try:
        seller = Seller.objects.get(id=request.session['seller_id'])
        
        if request.method == 'POST':
            # Update profile
            seller.company_name = request.POST.get('company_name', seller.company_name)
            seller.owner_name = request.POST.get('owner_name', seller.owner_name)
            seller.phone = request.POST.get('phone', seller.phone)
            seller.address = request.POST.get('address', seller.address)
            seller.email = request.POST.get('email', seller.email)
            
            # Check if password update requested
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if new_password and confirm_password:
                if new_password == confirm_password:
                    seller.password = new_password
                    messages.success(request, 'Password updated successfully')
                else:
                    messages.error(request, 'Passwords do not match')
            
            seller.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('seller_profile')
        
        # Get statistics for profile
        total_products = products.objects.filter(seller=seller).count()
        total_orders = Orders.objects.filter(seller=seller).count()
        total_revenue = Orders.objects.filter(
            seller=seller, 
            payment_status='paid'
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        context = {
            'seller': seller,
            'total_products': total_products,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
        }
        return render(request, 'seller_profile.html', context)
        
    except Seller.DoesNotExist:
        messages.error(request, 'Seller not found')
        return redirect('seller_login')
    except Exception as e:
        messages.error(request, f'Error loading profile: {str(e)}')
        return redirect('seller_dashboard')

def seller_dashboard_stats(request):
    """API endpoint for seller dashboard statistics"""
    if 'seller_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'Not authenticated'})
    
    try:
        seller = Seller.objects.get(id=request.session['seller_id'])
        
        # Get seller's product IDs
        seller_product_ids = products.objects.filter(seller=seller).values_list('id', flat=True)
        
        # Get orders containing seller's products
        order_ids = OrderItem.objects.filter(
            product_id__in=seller_product_ids
        ).values_list('order_id', flat=True).distinct()
        
        orders = Orders.objects.filter(id__in=order_ids)
        
        # Calculate statistics
        total_orders = orders.count()
        pending_orders = orders.filter(order_status='pending').count()
        confirmed_orders = orders.filter(order_status='confirmed').count()
        prepared_orders = orders.filter(order_status='prepared').count()
        dispatched_orders = orders.filter(order_status='dispatched').count()
        delivered_orders = orders.filter(order_status='delivered').count()
        cancelled_orders = orders.filter(order_status='cancelled').count()
        
        # Revenue
        total_revenue = orders.filter(payment_status='paid').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # Monthly revenue for chart
        monthly_revenue = []
        months = []
        today = timezone.now().date()
        
        for i in range(5, -1, -1):
            month_date = today - timedelta(days=30*i)
            month_start = month_date.replace(day=1)
            
            if month_date.month == 12:
                month_end = month_date.replace(day=31)
            else:
                month_end = (month_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            revenue = orders.filter(
                payment_status='paid',
                order_date__date__gte=month_start,
                order_date__date__lte=month_end
            ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            
            monthly_revenue.append(float(revenue))
            months.append(month_date.strftime('%b %Y'))
        
        # Recent orders
        recent_orders = orders.order_by('-order_date')[:5].values(
            'order_id', 'full_name', 'total_amount', 'order_status', 'payment_status'
        )
        
        return JsonResponse({
            'success': True,
            'stats': {
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'confirmed_orders': confirmed_orders,
                'prepared_orders': prepared_orders,
                'dispatched_orders': dispatched_orders,
                'delivered_orders': delivered_orders,
                'cancelled_orders': cancelled_orders,
                'total_revenue': float(total_revenue),
            },
            'monthly_revenue': monthly_revenue,
            'months': months,
            'recent_orders': list(recent_orders),
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def seller_analytics(request):
    """View for seller analytics dashboard"""
    if 'seller_id' not in request.session:
        messages.warning(request, 'Please login to view analytics')
        return redirect('seller_login')
    
    try:
        seller = Seller.objects.get(id=request.session['seller_id'])
        
        context = {
            'seller': seller,
        }
        return render(request, 'seller_analytics.html', context)
        
    except Seller.DoesNotExist:
        messages.error(request, 'Seller not found')
        return redirect('seller_login')
    except Exception as e:
        messages.error(request, f'Error loading analytics: {str(e)}')
        return redirect('seller_dashboard')

def seller_transactions(request):
    """View for seller transaction history"""
    if 'seller_id' not in request.session:
        messages.warning(request, 'Please login to view transactions')
        return redirect('seller_login')
    
    try:
        seller = Seller.objects.get(id=request.session['seller_id'])
        
        # Get paid orders for this seller
        transactions = Orders.objects.filter(
            seller=seller,
            payment_status='paid'
        ).order_by('-order_date')
        
        # Calculate totals
        total_earnings = transactions.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        total_transactions = transactions.count()
        
        # Pagination
        paginator = Paginator(transactions, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'seller': seller,
            'transactions': page_obj,
            'total_earnings': total_earnings,
            'total_transactions': total_transactions,
        }
        return render(request, 'seller_transactions.html', context)
        
    except Seller.DoesNotExist:
        messages.error(request, 'Seller not found')
        return redirect('seller_login')
    except Exception as e:
        messages.error(request, f'Error loading transactions: {str(e)}')
        return redirect('seller_dashboard')

def seller_notifications(request):
    """View for seller notifications"""
    if 'seller_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'Not authenticated'})
    
    try:
        seller = Seller.objects.get(id=request.session['seller_id'])
        
        # Get low stock notifications
        low_stock_products = products.objects.filter(
            seller=seller, 
            stock_quantity__lt=10
        ).values('product_name', 'stock_quantity')
        
        # Get pending orders
        seller_product_ids = products.objects.filter(seller=seller).values_list('id', flat=True)
        order_ids = OrderItem.objects.filter(
            product_id__in=seller_product_ids
        ).values_list('order_id', flat=True).distinct()
        
        pending_orders = Orders.objects.filter(
            id__in=order_ids,
            order_status='pending'
        ).count()
        
        notifications = []
        
        # Add low stock notifications
        for product in low_stock_products:
            notifications.append({
                'type': 'warning',
                'title': 'Low Stock Alert',
                'message': f"{product['product_name']} has only {product['stock_quantity']} items left",
                'link': '/seller-inventory/'
            })
        
        # Add pending order notification
        if pending_orders > 0:
            notifications.append({
                'type': 'info',
                'title': 'Pending Orders',
                'message': f"You have {pending_orders} pending order(s) to process",
                'link': '/seller-orders/?status=pending'
            })
        
        return JsonResponse({
            'success': True,
            'notifications': notifications,
            'count': len(notifications)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def restock_product(request):
    """Restock a single product"""
    if request.method == 'POST' and 'seller_id' in request.session:
        try:
            product_id = request.POST.get('product_id')
            quantity = int(request.POST.get('quantity', 0))
            
            product = get_object_or_404(products, id=product_id, seller_id=request.session['seller_id'])
            
            if quantity > 0:
                product.stock_quantity += quantity
                product.save()
                
                messages.success(request, f'Successfully restocked {product.product_name} with {quantity} units')
            else:
                messages.error(request, 'Invalid quantity')
                
        except Exception as e:
            messages.error(request, f'Error restocking product: {str(e)}')
            
        return redirect('seller_inventory')
    
    return redirect('seller_inventory')

def bulk_restock(request):
    """Restock multiple products at once"""
    if request.method == 'POST' and 'seller_id' in request.session:
        try:
            product_ids = request.POST.getlist('product_ids')
            quantities = request.POST.getlist('quantities')
            
            restocked_count = 0
            for product_id, quantity in zip(product_ids, quantities):
                if quantity and int(quantity) > 0:
                    product = get_object_or_404(products, id=product_id, seller_id=request.session['seller_id'])
                    product.stock_quantity += int(quantity)
                    product.save()
                    restocked_count += 1
            
            messages.success(request, f'Successfully restocked {restocked_count} products')
            
        except Exception as e:
            messages.error(request, f'Error in bulk restock: {str(e)}')
            
        return redirect('seller_inventory')
    
    return redirect('seller_inventory')

def get_product_details(request, product_id):
    """API endpoint to get product details for editing"""
    if 'seller_id' not in request.session and 'sid' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        # Get seller ID from session
        seller_id = None
        if 'seller_id' in request.session:
            seller_id = request.session['seller_id']
        elif 'sid' in request.session:
            seller_id = request.session['sid']
        
        # Get product and verify ownership
        product = products.objects.get(id=product_id)
        
        # Verify seller ownership
        try:
            seller = Seller.objects.get(id=seller_id)
        except (Seller.DoesNotExist, ValueError):
            seller = Seller.objects.get(email=seller_id)
        
        if product.seller.id != seller.id:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # Return all product details
        return JsonResponse({
            'id': product.id,
            'name': product.product_name,
            'description': product.description,
            'category': product.category,
            'calories': product.calories,
            'protein': float(product.protein) if product.protein else 0,
            'carbs': float(product.carbs) if product.carbs else 0,
            'fat': float(product.fat) if product.fat else 0,
            'fiber': float(product.fiber) if product.fiber else 0,
            'price': float(product.price),
            'stock': product.stock_quantity,
            'weight': product.weight
        })
        
    except products.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
def admin_chart_data(request):
    """API endpoint to get chart data based on date range"""
    if 'admin' not in request.session:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    # Get date parameters from request
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    
    try:
        if start_date and end_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            # Default to last 7 days
            end = timezone.now().date()
            start = end - timedelta(days=6)
        
        # Generate dates for the range
        dates = []
        counts = []
        current = start
        
        while current <= end:
            dates.append(current.strftime('%a'))
            count = Orders.objects.filter(order_date__date=current).count()
            counts.append(count)
            current += timedelta(days=1)
        
        return JsonResponse({
            'dates': dates,
            'counts': counts
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def send_order_emails(order, customer, product, quantity, plan):
    """
    Send order confirmation email to customer and notification to seller
    """
    # Calculate dates
    from datetime import datetime
    start_date = datetime.now()
    if plan == 'weekly':
        end_date = start_date + timedelta(days=7)
    elif plan == 'monthly':
        end_date = start_date + timedelta(days=30)
    else:
        end_date = start_date
    
    # Format dates
    start_date_str = start_date.strftime('%d %B %Y')
    end_date_str = end_date.strftime('%d %B %Y')
    
    # 1. Email to Customer
    customer_subject = f'Order Confirmed - FitBite Order #{order.order_id}'
    customer_message = f"""
    Dear {customer.name},
    
    Thank you for your order! Your order has been successfully placed.
    
    Order Details:
    --------------
    Order ID: {order.order_id}
    Product: {product.product_name}
    Quantity: {quantity}
    Plan: {plan.title()} Plan
    Duration: {start_date_str} to {end_date_str}
    Total Amount: ₹{order.total_amount}
    
    Delivery Address:
    ----------------
    {order.full_name}
    {order.phone}
    {order.address}
    {order.city}, {order.state} - {order.pincode}
    
    You can track your order status on our website.
    
    Thank you for choosing FitBite!
    
    Regards,
    FitBite Team
    """
    
    send_mail(
        subject=customer_subject,
        message=customer_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[customer.email],
        fail_silently=True,
    )
    
    # 2. Email to Seller
    seller_subject = f'New Order Received - FitBite Order #{order.order_id}'
    seller_message = f"""
    Dear {product.seller.company_name},
    
    You have received a new order!
    
    Order Details:
    --------------
    Order ID: {order.order_id}
    Product: {product.product_name}
    Quantity: {quantity}
    Plan: {plan.title()} Plan
    Delivery Period: {start_date_str} to {end_date_str}
    Total Amount: ₹{order.total_amount}
    
    Customer Details:
    ----------------
    Name: {order.full_name}
    Phone: {order.phone}
    Email: {customer.email}
    Address: {order.address}, {order.city}, {order.state} - {order.pincode}
    
    Please prepare the order for delivery.
    
    Regards,
    FitBite System
    """
    
    send_mail(
        subject=seller_subject,
        message=seller_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[product.seller.email],
        fail_silently=True,
    )


def user_profile(request):
    """View user profile"""
    if 'uid' not in request.session:
        messages.warning(request, 'Please login to view profile')
        return redirect('login')
    
    try:
        user_data = user.objects.get(email=request.session['uid'])
        context = {
            'user': user_data
        }
        return render(request, 'profile.html', context)
    except user.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('login')

def update_profile(request):
    """Update user profile (excluding email)"""
    if request.method == 'POST' and 'uid' in request.session:
        try:
            user_data = user.objects.get(email=request.session['uid'])
            
            # Check if this is an AJAX request for profile picture
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Handle profile picture upload
                if 'profile_pic' in request.FILES:
                    profile_pic = request.FILES['profile_pic']
                    
                    # Validate file type
                    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
                    ext = os.path.splitext(profile_pic.name)[1].lower()
                    
                    if ext not in valid_extensions:
                        return JsonResponse({
                            'success': False,
                            'error': 'Invalid image format. Please upload JPG, JPEG, PNG, GIF, or WEBP.'
                        })
                    
                    # Validate file size (max 2MB)
                    if profile_pic.size > 2 * 1024 * 1024:
                        return JsonResponse({
                            'success': False,
                            'error': 'Image size should be less than 2MB'
                        })
                    
                    # Delete old profile picture if exists and not default
                    if user_data.profile_pic and user_data.profile_pic.name != 'profile_pics/default-avatar.png':
                        if default_storage.exists(user_data.profile_pic.name):
                            default_storage.delete(user_data.profile_pic.name)
                    
                    # Save new profile picture
                    user_data.profile_pic = profile_pic
                    user_data.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Profile picture updated successfully!',
                        'image_url': user_data.profile_pic.url
                    })
                
                return JsonResponse({'success': False, 'error': 'No image file provided'})
            
            # Handle regular profile update (name, phone, address)
            name = request.POST.get('name', '').strip()
            phone = request.POST.get('phone', '').strip()
            address = request.POST.get('address', '').strip()
            
            # Validation
            errors = []
            
            if not name:
                errors.append("Name is required")
            elif len(name) < 2:
                errors.append("Name must be at least 2 characters long")
            elif any(char.isdigit() for char in name):
                errors.append("Name cannot contain numbers")
            
            if not phone:
                errors.append("Phone number is required")
            elif not phone.isdigit() or len(phone) != 10:
                errors.append("Please enter a valid 10-digit phone number")
            
            if not address:
                errors.append("Address is required")
            elif len(address) < 5:
                errors.append("Address must be at least 5 characters long")
            
            if errors:
                for error in errors:
                    messages.error(request, error)
                return redirect('user_profile')
            
            # Update user fields
            user_data.name = name
            user_data.phone = phone
            user_data.address = address
            user_data.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('user_profile')
            
        except user.DoesNotExist:
            messages.error(request, 'User not found')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
            return redirect('user_profile')
    
    return redirect('user_profile')

def change_password(request):
    """Change user password"""
    if request.method == 'POST' and 'uid' in request.session:
        try:
            user_data = user.objects.get(email=request.session['uid'])
            
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Verify current password
            if user_data.password != current_password:
                messages.error(request, 'Current password is incorrect')
                return redirect('user_profile')
            
            # Validate new password
            if not new_password or len(new_password) < 6:
                messages.error(request, 'New password must be at least 6 characters long')
                return redirect('user_profile')
            
            if not re.search(r'[A-Z]', new_password):
                messages.error(request, 'Password must contain at least one uppercase letter')
                return redirect('user_profile')
            
            if not re.search(r'[a-z]', new_password):
                messages.error(request, 'Password must contain at least one lowercase letter')
                return redirect('user_profile')
            
            if not re.search(r'[0-9]', new_password):
                messages.error(request, 'Password must contain at least one number')
                return redirect('user_profile')
            
            # Check if passwords match
            if new_password != confirm_password:
                messages.error(request, 'New passwords do not match')
                return redirect('user_profile')
            
            # Update password
            user_data.password = new_password
            user_data.save()
            
            messages.success(request, 'Password changed successfully!')
            return redirect('user_profile')
            
        except user.DoesNotExist:
            messages.error(request, 'User not found')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error changing password: {str(e)}')
            return redirect('user_profile')
    
    return redirect('user_profile')


from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

def admin_pending_sellers(request):
    """View for admin to see all seller requests with filtering by status"""
    if 'admin' not in request.session:
        messages.warning(request, 'Please login as admin')
        return redirect('log')
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')  # Default to 'all' instead of 'pending'
    search_query = request.GET.get('search', '')
    
    # Base queryset ordered by registration date (newest first)
    sellers = Seller.objects.all().order_by('-registered_date')
    
    # Apply status filter
    if status_filter != 'all':
        sellers = sellers.filter(status=status_filter)
    
    # Apply search filter
    if search_query:
        sellers = sellers.filter(
            Q(company_name__icontains=search_query) |
            Q(owner_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(gst_number__icontains=search_query)
        )
    
    # Statistics for all statuses
    stats = {
        'pending': Seller.objects.filter(status='pending').count(),
        'approved': Seller.objects.filter(status='approved').count(),
        'rejected': Seller.objects.filter(status='rejected').count(),
        'suspended': Seller.objects.filter(status='suspended').count(),
        'total': Seller.objects.count(),
    }
    
    # Pagination
    paginator = Paginator(sellers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'sellers': page_obj,
        'stats': stats,
        'status_filter': status_filter,
        'search_query': search_query,
        'admin_email': request.session['admin'],
    }
    return render(request, 'admin_pending_sellers.html', context)


def admin_seller_detail(request, seller_id):
    """View single seller details for verification with complete information"""
    if 'admin' not in request.session:
        messages.warning(request, 'Please login as admin')
        return redirect('log')
    
    seller = get_object_or_404(Seller, id=seller_id)
    
    # Get additional information about the seller
    from django.db.models import Count, Sum
    
    # Get product statistics for this seller
    product_count = products.objects.filter(seller=seller).count()
    total_stock = products.objects.filter(seller=seller).aggregate(Sum('stock_quantity'))['stock_quantity__sum'] or 0
    
    # Get order statistics (if you have orders linked to seller)
    try:
        order_count = Orders.objects.filter(seller=seller).count()
        total_revenue = Orders.objects.filter(seller=seller, payment_status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    except:
        order_count = 0
        total_revenue = 0
    
    context = {
        'seller': seller,
        'product_count': product_count,
        'total_stock': total_stock,
        'order_count': order_count,
        'total_revenue': total_revenue,
        'admin_email': request.session['admin'],
    }
    return render(request, 'admin_seller_detail.html', context)


def approve_seller(request, seller_id):
    """Approve a seller (works for pending, rejected, or suspended)"""
    if request.method == 'POST' and 'admin' in request.session:
        try:
            seller = get_object_or_404(Seller, id=seller_id)
            old_status = seller.status
            
            seller.status = 'approved'
            seller.verified_date = timezone.now()
            seller.rejection_reason = None  # Clear any previous rejection reason
            seller.save()
            
            messages.success(request, f'Seller {seller.company_name} has been approved successfully! (was {old_status})')
            
        except Exception as e:
            messages.error(request, f'Error approving seller: {str(e)}')
        
        return redirect('admin_pending_sellers')
    
    return redirect('log')


def reject_seller(request, seller_id):
    """Reject a seller with reason"""
    if request.method == 'POST' and 'admin' in request.session:
        try:
            seller = get_object_or_404(Seller, id=seller_id)
            reason = request.POST.get('rejection_reason', 'No reason provided')
            
            seller.status = 'rejected'
            seller.rejection_reason = reason
            seller.verified_date = timezone.now()
            seller.save()
            
            messages.success(request, f'Seller {seller.company_name} has been rejected.')
            
        except Exception as e:
            messages.error(request, f'Error rejecting seller: {str(e)}')
        
        return redirect('admin_pending_sellers')
    
    return redirect('log')


def suspend_seller(request, seller_id):
    """Suspend a seller with reason"""
    if request.method == 'POST' and 'admin' in request.session:
        try:
            seller = get_object_or_404(Seller, id=seller_id)
            reason = request.POST.get('suspension_reason', 'No reason provided')
            
            seller.status = 'suspended'
            seller.rejection_reason = reason  # Reuse rejection_reason field for suspension reason
            seller.verified_date = timezone.now()
            seller.save()
            
            messages.success(request, f'Seller {seller.company_name} has been suspended.')
            
        except Exception as e:
            messages.error(request, f'Error suspending seller: {str(e)}')
        
        return redirect('admin_pending_sellers')
    
    return redirect('log')


def unsuspend_seller(request, seller_id):
    """Unsuspend a seller (approve a suspended seller)"""
    if request.method == 'POST' and 'admin' in request.session:
        try:
            seller = get_object_or_404(Seller, id=seller_id)
            
            if seller.status != 'suspended':
                messages.error(request, f'Seller is not suspended (current status: {seller.status})')
                return redirect('admin_pending_sellers')
            
            seller.status = 'approved'
            seller.rejection_reason = None  # Clear suspension reason
            seller.verified_date = timezone.now()
            seller.save()
            
            messages.success(request, f'Seller {seller.company_name} has been unsuspended and approved.')
            
        except Exception as e:
            messages.error(request, f'Error unsuspending seller: {str(e)}')
        
        return redirect('admin_pending_sellers')
    
    return redirect('log')


def bulk_seller_action(request):
    """Handle bulk actions on sellers (approve, reject, delete, etc.)"""
    if request.method == 'POST' and 'admin' in request.session:
        action = request.POST.get('action')
        seller_ids = request.POST.getlist('seller_ids')
        
        if not seller_ids:
            messages.warning(request, 'Please select at least one seller')
            return redirect('admin_pending_sellers')
        
        try:
            if action == 'approve':
                # Approve selected sellers
                sellers = Seller.objects.filter(id__in=seller_ids)
                count = sellers.update(
                    status='approved',
                    verified_date=timezone.now(),
                    rejection_reason=None
                )
                messages.success(request, f'{count} seller(s) approved successfully')
            
            elif action == 'reject':
                # Reject selected sellers (requires reason - we'll use a default)
                reason = request.POST.get('bulk_rejection_reason', 'Rejected by admin')
                sellers = Seller.objects.filter(id__in=seller_ids)
                count = sellers.update(
                    status='rejected',
                    rejection_reason=reason,
                    verified_date=timezone.now()
                )
                messages.success(request, f'{count} seller(s) rejected')
            
            elif action == 'approve_rejected':
                # Approve previously rejected sellers
                sellers = Seller.objects.filter(id__in=seller_ids, status='rejected')
                count = sellers.update(
                    status='approved',
                    verified_date=timezone.now(),
                    rejection_reason=None
                )
                messages.success(request, f'{count} previously rejected seller(s) approved')
            
            elif action == 'unsuspend':
                # Unsuspend suspended sellers
                sellers = Seller.objects.filter(id__in=seller_ids, status='suspended')
                count = sellers.update(
                    status='approved',
                    verified_date=timezone.now(),
                    rejection_reason=None
                )
                messages.success(request, f'{count} suspended seller(s) unsuspended')
            
            elif action == 'delete':
                # Delete selected sellers
                count = Seller.objects.filter(id__in=seller_ids).delete()[0]
                messages.success(request, f'{count} seller(s) deleted')
            
            else:
                messages.error(request, f'Unknown action: {action}')
            
        except Exception as e:
            messages.error(request, f'Error performing bulk action: {str(e)}')
        
        return redirect('admin_pending_sellers')
    
    return redirect('log')


def admin_revenue(request):
    """Revenue report page showing platform fees breakdown"""
    if 'admin' not in request.session:
        messages.warning(request, 'Please login as admin')
        return redirect('log')
    
    # Get filter parameters
    date_range = request.GET.get('date_range', 'all')
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    payment_status = request.GET.get('payment_status', 'all')
    seller_id = request.GET.get('seller')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    orders = Orders.objects.all().order_by('-order_date')
    
    # Apply date filters
    today = timezone.now().date()
    
    # Handle custom date range from date picker
    if start_date and end_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            orders = orders.filter(order_date__date__gte=start_date_obj, 
                                  order_date__date__lte=end_date_obj)
            date_filter_applied = 'custom'
        except:
            # If date parsing fails, fall back to date_range
            start_date = None
            end_date = None
    
    # Apply predefined date ranges if no custom range
    if not start_date and not end_date:
        if date_range == 'today':
            orders = orders.filter(order_date__date=today)
        elif date_range == 'week':
            week_ago = today - timedelta(days=7)
            orders = orders.filter(order_date__date__gte=week_ago)
        elif date_range == 'month':
            month_ago = today - timedelta(days=30)
            orders = orders.filter(order_date__date__gte=month_ago)
        elif date_range == 'quarter':
            quarter_ago = today - timedelta(days=90)
            orders = orders.filter(order_date__date__gte=quarter_ago)
        elif date_range == 'year':
            year_ago = today - timedelta(days=365)
            orders = orders.filter(order_date__date__gte=year_ago)
        # 'all' means no date filter
    
    # Apply payment status filter
    if payment_status != 'all':
        orders = orders.filter(payment_status=payment_status)
    
    # Apply seller filter
    if seller_id and seller_id != 'all':
        orders = orders.filter(seller_id=seller_id)
    
    # Apply search
    if search_query:
        orders = orders.filter(
            Q(order_id__icontains=search_query) |
            Q(full_name__icontains=search_query)
        )
    
    # Calculate totals based on filtered orders
    paid_orders = orders.filter(payment_status='paid')
    total_platform_fees = paid_orders.count() * 50
    total_seller_earnings = paid_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_gmv = total_seller_earnings + total_platform_fees
    
    # Get all sellers for filter dropdown
    sellers = Seller.objects.filter(status='approved')
    
    # ===== FIXED: Monthly data for chart - NOW RESPECTS DATE FILTERS =====
    monthly_labels = []
    monthly_platform_fees = []
    
    # Determine the date range for monthly chart
    if start_date and end_date:
        # Use custom date range for chart
        chart_start = datetime.strptime(start_date, '%Y-%m-%d').date()
        chart_end = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        # Use predefined range or default to last 6 months
        if date_range == 'today':
            chart_start = today
            chart_end = today
        elif date_range == 'week':
            chart_start = today - timedelta(days=7)
            chart_end = today
        elif date_range == 'month':
            chart_start = today - timedelta(days=30)
            chart_end = today
        elif date_range == 'quarter':
            chart_start = today - timedelta(days=90)
            chart_end = today
        elif date_range == 'year':
            chart_start = today - timedelta(days=365)
            chart_end = today
        else:  # 'all' or default
            # Get the earliest and latest order dates
            earliest_order = Orders.objects.filter(payment_status='paid').order_by('order_date').first()
            if earliest_order:
                chart_start = earliest_order.order_date.date()
            else:
                chart_start = today - timedelta(days=180)  # Default to last 6 months
            chart_end = today
    
    # Generate monthly data based on the date range
    current_date = chart_start
    while current_date <= chart_end:
        # Get first and last day of the month
        month_start = current_date.replace(day=1)
        if current_date.month == 12:
            month_end = current_date.replace(day=31)
        else:
            month_end = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Ensure month_end doesn't exceed chart_end
        if month_end > chart_end:
            month_end = chart_end
        
        # Get paid orders for this month (respecting all filters)
        month_orders = orders.filter(
            order_date__date__gte=month_start,
            order_date__date__lte=month_end,
            payment_status='paid'
        )
        
        monthly_labels.append(current_date.strftime('%b %Y'))
        monthly_platform_fees.append(month_orders.count() * 50)
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
        
        # Limit to maximum 12 months to avoid too many bars
        if len(monthly_labels) >= 12:
            break
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'orders': page_obj,
        'sellers': sellers,
        'total_platform_fees': total_platform_fees,
        'total_seller_earnings': total_seller_earnings,
        'total_gmv': total_gmv,
        'total_orders': orders.count(),
        'paid_orders': paid_orders.count(),
        'pending_orders': orders.filter(payment_status='pending').count(),
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_platform_fees': json.dumps(monthly_platform_fees),
        'date_range': date_range,
        'payment_status': payment_status,
        'seller_id': seller_id,
        'search_query': search_query,
        'pending_sellers': Seller.objects.filter(status='pending').count(),
        'total_sellers': Seller.objects.count(),
        'total_users': user.objects.count(),
        'pending_orders': Orders.objects.filter(order_status='pending').count(),
        'admin_email': request.session['admin'],
        # Pass start and end dates to template for display
        'request': request,
    }
    return render(request, 'admin_revenue.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from .models import Feedbacks, Orders, OrderItem, products, Seller, user

def give_feedback(request):
    """Page for users to give feedback on purchased products"""
    if 'uid' not in request.session:
        messages.warning(request, 'Please login to give feedback')
        return redirect('login')
    
    try:
        customer = user.objects.get(email=request.session['uid'])
        
        # Get user's paid orders with their items
        from django.db.models import Prefetch
        
        # Get all paid orders for this customer
        user_orders = Orders.objects.filter(
            customer=customer,
            payment_status='paid'
        ).prefetch_related(
            Prefetch('items', queryset=OrderItem.objects.select_related('product'))
        ).order_by('-order_date')
        
        # Get all products the user has purchased (for dropdown)
        purchased_products = []
        for order in user_orders:
            for item in order.items.all():
                purchased_products.append({
                    'id': item.product.id,
                    'name': item.product.product_name,
                    'order_id': order.order_id,
                    'date': order.order_date
                })
        
        context = {
            'user': customer,
            'user_orders': user_orders,
            'purchased_products': purchased_products,
        }
        return render(request, 'give_feedback.html', context)
        
    except user.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('login')

def submit_feedback(request):
    """Submit feedback for a product"""
    if request.method == 'POST' and 'uid' in request.session:
        try:
            customer = user.objects.get(email=request.session['uid'])
            product_id = request.POST.get('product_id')
            rating = request.POST.get('rating')
            message = request.POST.get('message')
            
            # Validate
            if not all([product_id, rating, message]):
                messages.error(request, 'All fields are required')
                return redirect('give_feedback')
            
            # Get the product
            try:
                product = products.objects.get(id=product_id)
            except products.DoesNotExist:
                messages.error(request, 'Product not found')
                return redirect('give_feedback')
            
            # Check if user has purchased this product
            from django.db.models import Q
            order_item = OrderItem.objects.filter(
                Q(order__customer=customer) &
                Q(product=product) &
                Q(order__payment_status='paid')
            ).select_related('order').first()
            
            if not order_item:
                messages.error(request, 'You can only review products you have purchased')
                return redirect('give_feedback')
            
            # Check if already reviewed
            existing = Feedbacks.objects.filter(user=customer, product=product).first()
            if existing:
                messages.warning(request, 'You have already reviewed this product')
                return redirect('user_feedback')
            
            # Create feedback
            feedback = Feedbacks.objects.create(
                user=customer,
                product=product,
                order=order_item.order,
                rating=int(rating),
                message=message
            )
            
            messages.success(request, 'Thank you for your feedback!')
            return redirect('user_feedback')
            
        except Exception as e:
            messages.error(request, f'Error submitting feedback: {str(e)}')
            return redirect('give_feedback')
    
    return redirect('give_feedback')

def user_feedback(request):
    """Show user's feedback history"""
    if 'uid' not in request.session:
        messages.warning(request, 'Please login to view feedback')
        return redirect('login')
    
    try:
        customer = user.objects.get(email=request.session['uid'])
        feedbacks = Feedbacks.objects.filter(user=customer).select_related('product', 'order').order_by('-submitted_at')
        
        # Calculate stats
        total_feedbacks = feedbacks.count()
        avg_rating = feedbacks.aggregate(Avg('rating'))['rating__avg'] or 0
        five_star_count = feedbacks.filter(rating=5).count()
        
        context = {
            'user': customer,
            'feedbacks': feedbacks,
            'total_feedbacks': total_feedbacks,
            'avg_rating': round(avg_rating, 1),
            'five_star_count': five_star_count,
        }
        return render(request, 'user_feedback.html', context)
        
    except user.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('login')
def seller_feedback(request):
    """Show feedback for seller's products"""
    if 'seller_id' not in request.session:
        messages.warning(request, 'Please login to view feedback')
        return redirect('seller_login')
    
    try:
        seller = Seller.objects.get(id=request.session['seller_id'])
        
        # Get all products for this seller
        seller_products = products.objects.filter(seller=seller)
        
        # Get feedback for these products
        feedbacks = Feedbacks.objects.filter(product__in=seller_products).select_related('user', 'product', 'order').order_by('-submitted_at')
        
        # Calculate stats
        total_reviews = feedbacks.count()
        avg_rating = feedbacks.aggregate(Avg('rating'))['rating__avg'] or 0
        five_star_count = feedbacks.filter(rating=5).count()
        
        context = {
            'seller': seller,
            'feedbacks': feedbacks,
            'products': seller_products,
            'total_reviews': total_reviews,
            'avg_rating': avg_rating,
            'five_star_count': five_star_count,
            'response_rate': 100 if total_reviews > 0 else 0
        }
        return render(request, 'seller_feedback.html', context)
        
    except Seller.DoesNotExist:
        messages.error(request, 'Seller not found')
        return redirect('seller_login')

def admin_feedback(request):
    """Show all feedback for admin"""
    if 'admin' not in request.session:
        messages.warning(request, 'Please login as admin')
        return redirect('log')
    
    # Get filter parameters
    rating_filter = request.GET.get('rating', 'all')
    seller_filter = request.GET.get('seller', 'all')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    feedbacks = Feedbacks.objects.select_related('user', 'product', 'product__seller').all().order_by('-submitted_at')
    
    # Apply filters
    if rating_filter != 'all':
        feedbacks = feedbacks.filter(rating=int(rating_filter))
    
    if seller_filter != 'all':
        feedbacks = feedbacks.filter(product__seller_id=seller_filter)
    
    if search_query:
        feedbacks = feedbacks.filter(
            Q(user__name__icontains=search_query) |
            Q(product__product_name__icontains=search_query) |
            Q(message__icontains=search_query)
        )
    
    # Calculate stats
    total_reviews = Feedbacks.objects.count()
    avg_rating = Feedbacks.objects.aggregate(Avg('rating'))['rating__avg'] or 0
    five_star_count = Feedbacks.objects.filter(rating=5).count()
    unique_reviewers = Feedbacks.objects.values('user').distinct().count()
    
    # Get sellers for filter
    sellers = Seller.objects.filter(status='approved')
    
    # Pagination
    paginator = Paginator(feedbacks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'feedbacks': page_obj,
        'sellers': sellers,
        'total_reviews': total_reviews,
        'avg_rating': avg_rating,
        'five_star_count': five_star_count,
        'unique_reviewers': unique_reviewers,
        'admin_email': request.session['admin'],
    }
    return render(request, 'admin_feedback.html', context)

def newindex(request):
    """Home page with products and feedback"""
    all_products = products.objects.all()
    
    # Get recent feedbacks
    recent_feedbacks = Feedbacks.objects.select_related('user', 'product').order_by('-submitted_at')[:6]
    
    context = {
        'products': all_products,
        'feedbacks': recent_feedbacks,
    }
    return render(request, 'index.html', context)




from django.shortcuts import render, redirect
from django.contrib import messages
from .models import products, Cart, Orders
import json
import uuid

def checkout_view(request):
    """View for checkout page"""
    
    # Check if user is logged in
    if 'uid' not in request.session:
        messages.warning(request, 'Please login to continue')
        return redirect('login')
    
    user_email = request.session['uid']
    
    # Get cart data from database (if any)
    db_cart_items = Cart.objects.filter(user_email=user_email)
    
    # Get cart data from session/localStorage (sent via AJAX or form)
    cart_data = []
    
    if request.method == 'POST':
        # If cart data is sent via POST
        cart_json = request.POST.get('cart_data')
        if cart_json:
            try:
                cart_data = json.loads(cart_json)
            except:
                cart_data = []
    
    # Calculate totals
    subtotal = 0
    cart_items = []
    
    # If we have POST cart data, use that
    if cart_data:
        for item in cart_data:
            try:
                product = products.objects.get(id=item['id'])
                cart_items.append({
                    'product': product,
                    'quantity': item['quantity'],
                    'subtotal': float(product.price) * item['quantity']
                })
                subtotal += float(product.price) * item['quantity']
            except products.DoesNotExist:
                continue
    
    # Otherwise, use database cart
    elif db_cart_items.exists():
        for cart_item in db_cart_items:
            cart_items.append({
                'product': cart_item.product,
                'quantity': cart_item.quantity,
                'subtotal': float(cart_item.product.price) * cart_item.quantity
            })
            subtotal += float(cart_item.product.price) * cart_item.quantity
    
    # If no items in either cart
    if not cart_items:
        messages.warning(request, 'Your cart is empty')
        return redirect('opensearch')
    
    # Platform fee
    platform_fee = 50.00
    total = subtotal + platform_fee
    
    # Get customer details
    try:
        customer = user.objects.get(email=user_email)
    except user.DoesNotExist:
        customer = None
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'platform_fee': platform_fee,
        'total': total,
        'customer': customer,
        'cart_count': len(cart_items)
    }
    
    return render(request, 'checkout.html', context)



def admin_dietitians(request):
    """View all dietitians"""
    if 'admin' not in request.session:
        messages.warning(request, 'Please login as admin')
        return redirect('log')
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    
    # Base queryset
    dietitians = Dietitian.objects.all()
    
    # Apply search filter
    if search_query:
        dietitians = dietitians.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(specialization__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter == 'active':
        dietitians = dietitians.filter(is_active=True)
    elif status_filter == 'inactive':
        dietitians = dietitians.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(dietitians, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_dietitians = Dietitian.objects.count()
    active_dietitians = Dietitian.objects.filter(is_active=True).count()
    inactive_dietitians = Dietitian.objects.filter(is_active=False).count()
    
    context = {
        'dietitians': page_obj,
        'total_dietitians': total_dietitians,
        'active_dietitians': active_dietitians,
        'inactive_dietitians': inactive_dietitians,
        'search_query': search_query,
        'status_filter': status_filter,
        'admin_email': request.session['admin'],
    }
    
    return render(request, 'admin_dietitians.html', context)

def admin_add_dietitian(request):
    """Add new dietitian"""
    if 'admin' not in request.session:
        messages.warning(request, 'Please login as admin')
        return redirect('log')
    
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        qualification = request.POST.get('qualification')
        specialization = request.POST.get('specialization')
        address = request.POST.get('address')
        location = request.POST.get('location')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        image = request.FILES.get('image')
        
        # Validation
        errors = []
        
        if not name:
            errors.append('Name is required')
        if not age:
            errors.append('Age is required')
        elif int(age) < 18 or int(age) > 100:
            errors.append('Age must be between 18 and 100')
        if not email:
            errors.append('Email is required')
        elif Dietitian.objects.filter(email=email).exists():
            errors.append('Email already exists')
        if not phone:
            errors.append('Phone is required')
        if not password:
            errors.append('Password is required')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters')
        elif password != confirm_password:
            errors.append('Passwords do not match')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'admin_add_dietitian.html', {
                'form_data': request.POST,
                'admin_email': request.session['admin']
            })
        
        # Create dietitian
        dietitian = Dietitian(
            name=name,
            age=age,
            gender=gender,
            email=email,
            phone=phone,
            qualification=qualification,
            specialization=specialization,
            address=address,
            location=location,
            password=password,
            is_active=True
        )
        
        if image:
            dietitian.image = image
        
        dietitian.save()
        
        messages.success(request, f'Dietitian {name} added successfully!')
        return redirect('admin_dietitians')
    
    return render(request, 'admin_add_dietitian.html', {'admin_email': request.session['admin']})

def admin_edit_dietitian(request, dietitian_id):
    """Edit dietitian details"""
    if 'admin' not in request.session:
        messages.warning(request, 'Please login as admin')
        return redirect('log')
    
    dietitian = get_object_or_404(Dietitian, id=dietitian_id)
    
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        qualification = request.POST.get('qualification')
        specialization = request.POST.get('specialization')
        address = request.POST.get('address')
        location = request.POST.get('location')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        image = request.FILES.get('image')
        
        # Validation
        errors = []
        
        if not name:
            errors.append('Name is required')
        if not age:
            errors.append('Age is required')
        elif int(age) < 18 or int(age) > 100:
            errors.append('Age must be between 18 and 100')
        if not email:
            errors.append('Email is required')
        elif email != dietitian.email and Dietitian.objects.filter(email=email).exists():
            errors.append('Email already exists')
        if not phone:
            errors.append('Phone is required')
        if password:
            if len(password) < 6:
                errors.append('Password must be at least 6 characters')
            elif password != confirm_password:
                errors.append('Passwords do not match')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'admin_edit_dietitian.html', {
                'dietitian': dietitian,
                'form_data': request.POST,
                'admin_email': request.session['admin']
            })
        
        # Update dietitian
        dietitian.name = name
        dietitian.age = age
        dietitian.gender = gender
        dietitian.email = email
        dietitian.phone = phone
        dietitian.qualification = qualification
        dietitian.specialization = specialization
        dietitian.address = address
        dietitian.location = location
        
        if password:
            dietitian.password = password
        
        if image:
            dietitian.image = image
        
        dietitian.save()
        
        messages.success(request, f'Dietitian {name} updated successfully!')
        return redirect('admin_dietitians')
    
    return render(request, 'admin_edit_dietitian.html', {
        'dietitian': dietitian,
        'admin_email': request.session['admin']
    })

def admin_delete_dietitian(request, dietitian_id):
    """Delete dietitian"""
    if 'admin' not in request.session:
        messages.warning(request, 'Please login as admin')
        return redirect('log')
    
    dietitian = get_object_or_404(Dietitian, id=dietitian_id)
    
    if request.method == 'POST':
        name = dietitian.name
        dietitian.delete()
        messages.success(request, f'Dietitian {name} deleted successfully!')
        return redirect('admin_dietitians')
    
    return render(request, 'admin_delete_dietitian.html', {
        'dietitian': dietitian,
        'admin_email': request.session['admin']
    })

def admin_toggle_dietitian_status(request, dietitian_id):
    """Toggle dietitian active/inactive status"""
    if 'admin' not in request.session:
        messages.warning(request, 'Please login as admin')
        return redirect('log')
    
    dietitian = get_object_or_404(Dietitian, id=dietitian_id)
    dietitian.is_active = not dietitian.is_active
    dietitian.save()
    
    status = "activated" if dietitian.is_active else "deactivated"
    messages.success(request, f'Dietitian {dietitian.name} {status} successfully!')
    
    return redirect('admin_dietitians')


# ==================== USER APPOINTMENT BOOKING ====================

def get_dietitians(request):
    """Get all dietitians for dropdown"""
    dietitians = Dietitian.objects.filter(is_active=True)
    context = {
        'dietitians': dietitians,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,  # Add this
    }
    return render(request, 'dietitians_list.html', context)

def get_dietitian_slots(request):
    """Get available slots for a dietitian (AJAX)"""
    if request.method == 'GET':
        dietitian_id = request.GET.get('dietitian_id')
        date_str = request.GET.get('date')
        
        try:
            dietitian = Dietitian.objects.get(id=dietitian_id, is_active=True)
            slot_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
            
            # Check if dietitian is on leave
            if slot_date and DietitianLeave.objects.filter(dietitian=dietitian, leave_date=slot_date).exists():
                return JsonResponse({'error': 'Dietitian is on leave this day'}, status=400)
            
            # Get available slots
            slots = DietitianSlot.objects.filter(
                dietitian=dietitian,
                slot_date=slot_date,
                is_booked=False
            ).order_by('slot_time')
            
            slots_data = [{'time': slot.slot_time, 'id': slot.id} for slot in slots]
            
            return JsonResponse({'slots': slots_data})
            
        except Dietitian.DoesNotExist:
            return JsonResponse({'error': 'Dietitian not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# Update in views.py

def book_appointment(request):
    """Book an appointment with dietitian - WITH PAYMENT"""
    if 'uid' not in request.session:
        return JsonResponse({'error': 'Please login first'}, status=401)
    
    if request.method == 'POST':
        try:
            user_obj = user.objects.get(email=request.session['uid'])
            dietitian_id = request.POST.get('dietitian_id')
            slot_id = request.POST.get('slot_id')
            appointment_date = request.POST.get('appointment_date')
            appointment_time = request.POST.get('appointment_time')
            reason = request.POST.get('reason')
            symptoms = request.POST.get('symptoms', '')
            consultation_fee = float(request.POST.get('consultation_fee', 300))
            platform_fee = float(request.POST.get('platform_fee', 50))
            total_amount = consultation_fee + platform_fee
            
            # Get dietitian and slot
            dietitian = Dietitian.objects.get(id=dietitian_id, is_active=True)
            slot = DietitianSlot.objects.get(id=slot_id)
            
            if slot.is_booked:
                return JsonResponse({'error': 'This slot is already booked'}, status=400)
            
            # Create appointment with pending payment
            appointment = Appointment.objects.create(
                user=user_obj,
                dietitian=dietitian,
                slot=slot,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                reason=reason,
                symptoms=symptoms,
                consultation_fee=consultation_fee,
                platform_fee=platform_fee,
                total_amount=total_amount,
                status='pending',
                payment_status='pending'
            )
            
            # Create Razorpay Order
            razorpay_order = razorpay_client.order.create({
                "amount": int(total_amount * 100),  # Convert to paise
                "currency": "INR",
                "receipt": f"apt_{appointment.id}",
                "payment_capture": 1,
                "notes": {
                    "appointment_id": appointment.appointment_id,
                    "user_name": user_obj.name,
                    "dietitian_name": dietitian.name
                }
            })
            
            # Save Razorpay order ID
            appointment.razorpay_order_id = razorpay_order['id']
            appointment.save()
            
            # Return payment details to frontend
            return JsonResponse({
                'success': True,
                'appointment_id': appointment.id,
                'razorpay_order_id': razorpay_order['id'],
                'amount': total_amount,
                'amount_paise': int(total_amount * 100),
                'dietitian_name': dietitian.name,
                'message': 'Proceed to payment to confirm your appointment'
            })
            
        except Dietitian.DoesNotExist:
            return JsonResponse({'error': 'Dietitian not found'}, status=404)
        except DietitianSlot.DoesNotExist:
            return JsonResponse({'error': 'Slot not available'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def verify_appointment_payment(request):
    """Verify payment after Razorpay checkout"""
    if request.method == 'POST':
        try:
            appointment_id = request.POST.get('appointment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_signature = request.POST.get('razorpay_signature')
            
            # Verify signature
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            
            razorpay_client.utility.verify_payment_signature(params_dict)
            
            # Get appointment and update
            appointment = Appointment.objects.get(id=appointment_id)
            appointment.payment_status = 'paid'
            appointment.status = 'confirmed'
            appointment.razorpay_payment_id = razorpay_payment_id
            
            # Book the slot
            slot = appointment.slot
            slot.is_booked = True
            slot.booked_by = appointment.user
            slot.booked_at = timezone.now()
            slot.save()
            
            appointment.save()
            
            # Create notification message
            DietitianMessage.objects.create(
                dietitian=appointment.dietitian,
                user=appointment.user,
                message=f"Appointment confirmed for {appointment.appointment_date} at {appointment.appointment_time}. Fee: ₹{appointment.consultation_fee} paid.",
                is_from_user=True,
                is_read=False
            )
            
            # Send confirmation email (optional)
            try:
                send_appointment_confirmation_email(appointment)
            except:
                pass
            
            return JsonResponse({
                'success': True,
                'message': 'Payment successful! Your appointment is confirmed.',
                'appointment_id': appointment.appointment_id
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def send_appointment_confirmation_email(appointment):
    """Send appointment confirmation email"""
    from django.core.mail import send_mail
    
    subject = f'Appointment Confirmed - FitBite Consultation #{appointment.appointment_id}'
    message = f"""
    Dear {appointment.user.name},
    
    Your appointment with {appointment.dietitian.name} has been confirmed!
    
    Appointment Details:
    --------------------
    Appointment ID: {appointment.appointment_id}
    Dietitian: {appointment.dietitian.name}
    Specialization: {appointment.dietitian.specialization}
    Date: {appointment.appointment_date}
    Time: {appointment.appointment_time}
    
    Consultation Fee: ₹{appointment.consultation_fee}
    
    Reason: {appointment.reason}
    
    The dietitian will contact you at the scheduled time.
    
    You can cancel or reschedule your appointment from your dashboard.
    
    Thank you for choosing FitBite!
    
    Regards,
    FitBite Team
    """
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[appointment.user.email],
        fail_silently=True,
    )


def my_appointments(request):
    """View user's appointments"""
    if 'uid' not in request.session:
        return redirect('login')
    
    user_obj = user.objects.get(email=request.session['uid'])
    appointments = Appointment.objects.filter(user=user_obj).order_by('-appointment_date', '-appointment_time')
    
    # Calculate statistics
    total_appointments = appointments.count()
    confirmed_count = appointments.filter(status='confirmed').count()
    completed_count = appointments.filter(status='completed').count()
    pending_count = appointments.filter(status='pending').count()
    cancelled_count = appointments.filter(status='cancelled').count()
    
    # Calculate total spent on paid appointments
    from django.db.models import Sum
    total_spent = appointments.filter(
        payment_status='paid'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'appointments': appointments,
        'user': user_obj,
        'total_spent': total_spent,
        'total_appointments': total_appointments,
        'confirmed_count': confirmed_count,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'cancelled_count': cancelled_count,
    }
    
    return render(request, 'my_appointments.html', context)
def cancel_appointment(request, appointment_id):
    """Cancel an appointment"""
    if 'uid' not in request.session:
        return redirect('login')
    
    appointment = get_object_or_404(Appointment, id=appointment_id, user__email=request.session['uid'])
    
    if appointment.status == 'cancelled':
        messages.warning(request, 'Appointment is already cancelled')
    elif appointment.status == 'completed':
        messages.warning(request, 'Cannot cancel completed appointment')
    else:
        # Free up the slot
        if appointment.slot:
            appointment.slot.is_booked = False
            appointment.slot.booked_by = None
            appointment.slot.booked_at = None
            appointment.slot.save()
        
        appointment.status = 'cancelled'
        appointment.save()
        
        # Notify dietitian
        DietitianMessage.objects.create(
            dietitian=appointment.dietitian,
            user=appointment.user,
            message=f"Appointment for {appointment.appointment_date} at {appointment.appointment_time} has been cancelled",
            is_from_user=True,
            is_read=False
        )
        
        messages.success(request, 'Appointment cancelled successfully')
    
    return redirect('my_appointments')


def send_message_to_dietitian(request):
    """Send message to dietitian from user"""
    if 'uid' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    if request.method == 'POST':
        dietitian_id = request.POST.get('dietitian_id')
        message = request.POST.get('message')
        
        try:
            user_obj = user.objects.get(email=request.session['uid'])
            dietitian = Dietitian.objects.get(id=dietitian_id)
            
            DietitianMessage.objects.create(
                dietitian=dietitian,
                user=user_obj,
                message=message,
                is_from_user=True,
                is_read=False
            )
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Q
from datetime import datetime

def my_messages(request):
    """View user's messages with all dietitians (WhatsApp style)"""
    
    if 'uid' not in request.session:
        return redirect('login')
    
    user_obj = user.objects.get(email=request.session['uid'])
    
    # Get all active dietitians
    all_dietitians = Dietitian.objects.filter(is_active=True)
    
    conversations = []
    
    for dietitian in all_dietitians:
        # Last message
        last_message = DietitianMessage.objects.filter(
            dietitian=dietitian,
            user=user_obj
        ).order_by('-created_at').first()
        
        # Unread count
        unread_count = DietitianMessage.objects.filter(
            dietitian=dietitian,
            user=user_obj,
            is_read=False,
            is_from_user=False
        ).count()
        
        conversations.append({
            'dietitian': dietitian,
            'last_message': last_message,
            'unread_count': unread_count
        })
    
    # ✅ FIXED: timezone-safe sorting
    conversations.sort(
        key=lambda x: x['last_message'].created_at if x['last_message'] else timezone.now(),
        reverse=True
    )
    
    # Selected chat
    selected_dietitian_id = request.GET.get('dietitian_id')
    selected_messages = []
    selected_dietitian = None
    
    if selected_dietitian_id:
        try:
            selected_dietitian = Dietitian.objects.get(id=selected_dietitian_id)
            
            selected_messages = DietitianMessage.objects.filter(
                dietitian=selected_dietitian,
                user=user_obj
            ).order_by('created_at')
            
            # Mark messages as read
            DietitianMessage.objects.filter(
                dietitian=selected_dietitian,
                user=user_obj,
                is_read=False,
                is_from_user=False
            ).update(is_read=True)
        
        except Dietitian.DoesNotExist:
            selected_dietitian = None
    
    context = {
        'conversations': conversations,
        'selected_dietitian': selected_dietitian,
        'selected_messages': selected_messages,
        'user': user_obj,
    }
    
    return render(request, 'my_messages.html', context)
def get_dietitian_new_messages(request):
    """Get new messages for dietitian (AJAX)"""
    if 'dietitian_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    if request.method == 'GET':
        dietitian = Dietitian.objects.get(id=request.session['dietitian_id'])
        user_id = request.GET.get('user_id')
        last_message_id = request.GET.get('last_message_id', 0)
        
        try:
            patient = user.objects.get(id=user_id)
            
            new_messages = DietitianMessage.objects.filter(
                dietitian=dietitian,
                user=patient,
                id__gt=last_message_id,
                is_from_user=True  # Messages from user to dietitian
            ).order_by('created_at')
            
            messages_data = []
            for msg in new_messages:
                messages_data.append({
                    'id': msg.id,
                    'message': msg.message,
                    'is_from_user': msg.is_from_user,
                    'created_at': msg.created_at.strftime('%I:%M %p'),
                })
            
            return JsonResponse({'success': True, 'messages': messages_data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def dietitian_send_message(request):
    """Send message to user (AJAX)"""
    if 'dietitian_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        message = request.POST.get('message')
        
        try:
            dietitian = Dietitian.objects.get(id=request.session['dietitian_id'])
            customer = user.objects.get(id=user_id)
            
            # Save message
            msg = DietitianMessage.objects.create(
                dietitian=dietitian,
                user=customer,
                message=message,
                is_from_user=False,  # False because dietitian is sending
                is_read=False
            )
            
            return JsonResponse({'success': True, 'message_id': msg.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def send_message_to_dietitian(request):
    """Send message to dietitian (AJAX)"""
    if 'uid' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    if request.method == 'POST':
        dietitian_id = request.POST.get('dietitian_id')
        message = request.POST.get('message')
        
        try:
            user_obj = user.objects.get(email=request.session['uid'])
            dietitian = Dietitian.objects.get(id=dietitian_id, is_active=True)
            
            # Save message
            DietitianMessage.objects.create(
                dietitian=dietitian,
                user=user_obj,
                message=message,
                is_from_user=True,
                is_read=False
            )
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def get_new_messages(request):
    """Get new messages for auto-refresh (AJAX)"""
    if 'uid' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    if request.method == 'GET':
        user_obj = user.objects.get(email=request.session['uid'])
        dietitian_id = request.GET.get('dietitian_id')
        last_message_id = request.GET.get('last_message_id', 0)
        
        try:
            dietitian = Dietitian.objects.get(id=dietitian_id)
            
            new_messages = DietitianMessage.objects.filter(
                dietitian=dietitian,
                user=user_obj,
                id__gt=last_message_id
            ).order_by('created_at')
            
            messages_data = []
            for msg in new_messages:
                messages_data.append({
                    'id': msg.id,
                    'message': msg.message,
                    'is_from_user': msg.is_from_user,
                    'created_at': msg.created_at.strftime('%I:%M %p'),
                    'is_read': msg.is_read
                })
            
            # Mark as read
            DietitianMessage.objects.filter(
                dietitian=dietitian,
                user=user_obj,
                is_read=False,
                is_from_user=False
            ).update(is_read=True)
            
            return JsonResponse({'success': True, 'messages': messages_data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def dietitian_dashboard(request):
    """Dietitian dashboard"""
    if 'dietitian_id' not in request.session:
        return redirect('dietitian_login')
    
    dietitian = Dietitian.objects.get(id=request.session['dietitian_id'])
    
    # Get statistics
    today = date.today()
    pending_appointments = Appointment.objects.filter(dietitian=dietitian, status='pending', appointment_date__gte=today).count()
    today_appointments = Appointment.objects.filter(dietitian=dietitian, appointment_date=today).count()
    total_appointments = Appointment.objects.filter(dietitian=dietitian).count()
    unread_messages = DietitianMessage.objects.filter(dietitian=dietitian, is_read=False, is_from_user=True).count()
    
    # Upcoming appointments
    upcoming_appointments = Appointment.objects.filter(
        dietitian=dietitian, 
        appointment_date__gte=today,
        status__in=['pending', 'confirmed']
    ).order_by('appointment_date', 'appointment_time')[:10]
    
    # Recent messages
    recent_messages = DietitianMessage.objects.filter(
        dietitian=dietitian
    ).order_by('-created_at')[:10]
    
    # Today's slots
    today_slots = DietitianSlot.objects.filter(
        dietitian=dietitian,
        slot_date=today
    ).order_by('slot_time')
    
    context = {
        'dietitian': dietitian,
        'pending_appointments': pending_appointments,
        'today_appointments': today_appointments,
        'total_appointments': total_appointments,
        'unread_messages': unread_messages,
        'upcoming_appointments': upcoming_appointments,
        'recent_messages': recent_messages,
        'today_slots': today_slots,
    }
    
    return render(request, 'dietitian_dashboard.html', context)


def dietitian_messages(request):
    """View and reply to messages"""
    if 'dietitian_id' not in request.session:
        return redirect('dietitian_login')
    
    dietitian = Dietitian.objects.get(id=request.session['dietitian_id'])
    
    # Get all unique users who have messaged this dietitian
    conversations = {}
    
    # Get all messages ordered by creation time
    all_messages = DietitianMessage.objects.filter(dietitian=dietitian).order_by('created_at')
    
    for msg in all_messages:
        if msg.user.id not in conversations:
            conversations[msg.user.id] = {
                'user': msg.user,
                'messages': [],
                'unread_count': DietitianMessage.objects.filter(
                    dietitian=dietitian, 
                    user=msg.user, 
                    is_read=False, 
                    is_from_user=True
                ).count()
            }
        conversations[msg.user.id]['messages'].append(msg)
    
    # Mark messages as read when viewing
    selected_user_id = request.GET.get('user_id')
    if selected_user_id:
        DietitianMessage.objects.filter(
            dietitian=dietitian, 
            user_id=selected_user_id, 
            is_from_user=True, 
            is_read=False
        ).update(is_read=True)
    
    context = {
        'dietitian': dietitian,
        'conversations': conversations.values(),
        'selected_user_id': selected_user_id,
    }
    
    return render(request, 'dietitian_messages.html', context)

def dietitian_send_message(request):
    """Send message to user"""
    if 'dietitian_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        message = request.POST.get('message')
        
        try:
            dietitian = Dietitian.objects.get(id=request.session['dietitian_id'])
            customer = user.objects.get(id=user_id)
            
            # Create the message
            msg = DietitianMessage.objects.create(
                dietitian=dietitian,
                user=customer,
                message=message,
                is_from_user=False,  # False because dietitian is sending
                is_read=False
            )
            
            # Force a database commit
            msg.save()
            
            # Return success with the message ID
            return JsonResponse({
                'success': True, 
                'message_id': msg.id,
                'message': msg.message,
                'created_at': msg.created_at.strftime('%I:%M %p')
            })
        except Exception as e:
            print(f"Error sending message: {e}")
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

def dietitian_appointments(request):
    """Manage appointments"""
    if 'dietitian_id' not in request.session:
        return redirect('dietitian_login')
    
    dietitian = Dietitian.objects.get(id=request.session['dietitian_id'])
    
    # Filter parameters
    status_filter = request.GET.get('status', 'all')
    date_filter = request.GET.get('date', '')
    
    appointments = Appointment.objects.filter(dietitian=dietitian).order_by('-appointment_date', '-appointment_time')
    
    # Calculate counts
    total_count = appointments.count()
    pending_count = appointments.filter(status='pending').count()
    confirmed_count = appointments.filter(status='confirmed').count()
    completed_count = appointments.filter(status='completed').count()
    cancelled_count = appointments.filter(status='cancelled').count()
    
    if status_filter != 'all':
        appointments = appointments.filter(status=status_filter)
    
    if date_filter:
        appointments = appointments.filter(appointment_date=date_filter)
    
    context = {
        'dietitian': dietitian,
        'appointments': appointments,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'total_count': total_count,
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
    }
    
    return render(request, 'dietitian_appointments.html', context)

def dietitian_generate_slots(request):
    """Generate slots for dietitian"""
    if 'dietitian_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    if request.method == 'POST':
        try:
            dietitian = Dietitian.objects.get(id=request.session['dietitian_id'])
            action = request.POST.get('action')
            
            from datetime import date, timedelta
            
            if action == 'generate_all':
                # Generate slots for next 7 days
                for i in range(7):
                    slot_date = date.today() + timedelta(days=i)
                    for slot_time in DietitianSlot.SLOT_TIMES:
                        DietitianSlot.objects.get_or_create(
                            dietitian=dietitian,
                            slot_date=slot_date,
                            slot_time=slot_time[0],
                            defaults={'is_booked': False}
                        )
                return JsonResponse({'success': True, 'message': 'Slots generated for next 7 days'})
            
            elif action == 'generate_date':
                slot_date = request.POST.get('date')
                from datetime import datetime
                slot_date_obj = datetime.strptime(slot_date, '%Y-%m-%d').date()
                
                for slot_time in DietitianSlot.SLOT_TIMES:
                    DietitianSlot.objects.get_or_create(
                        dietitian=dietitian,
                        slot_date=slot_date_obj,
                        slot_time=slot_time[0],
                        defaults={'is_booked': False}
                    )
                return JsonResponse({'success': True, 'message': f'Slots generated for {slot_date}'})
            
            return JsonResponse({'error': 'Invalid action'}, status=400)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

def dietitian_update_appointment_status(request, appointment_id):
    """Update appointment status"""
    if 'dietitian_id' not in request.session:
        return redirect('dietitian_login')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        if appointment.dietitian.id != request.session['dietitian_id']:
            messages.error(request, 'Unauthorized')
            return redirect('dietitian_appointments')
        
        appointment.status = new_status
        if notes:
            appointment.notes = notes
        appointment.save()
        
        messages.success(request, f'Appointment status updated to {new_status}')
    
    return redirect('dietitian_appointments')
def get_latest_message_id(request):
    """Get the latest message ID for a conversation"""
    if 'dietitian_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    if request.method == 'GET':
        user_id = request.GET.get('user_id')
        
        try:
            dietitian = Dietitian.objects.get(id=request.session['dietitian_id'])
            customer = user.objects.get(id=user_id)
            
            latest_message = DietitianMessage.objects.filter(
                dietitian=dietitian,
                user=customer
            ).order_by('-id').first()
            
            return JsonResponse({
                'success': True,
                'last_message_id': latest_message.id if latest_message else 0
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

def dietitian_payment_report(request):
    """Dietitian view to see their own earnings"""
    if 'dietitian_id' not in request.session:
        messages.warning(request, 'Please login to view earnings')
        return redirect('dietitian_login')
    
    try:
        dietitian = Dietitian.objects.get(id=request.session['dietitian_id'])
        
        # Get filter parameters
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        
        # Base queryset - only completed and paid appointments
        appointments = Appointment.objects.filter(
            dietitian=dietitian,
            status='completed',
            payment_status='paid'
        )
        
        # Apply date filters
        if start_date:
            appointments = appointments.filter(appointment_date__gte=start_date)
        if end_date:
            appointments = appointments.filter(appointment_date__lte=end_date)
        
        from django.db.models import Sum
        from datetime import datetime, timedelta
        from calendar import monthrange
        
        # Calculate totals
        total_consultations = appointments.count()
        total_fees = appointments.aggregate(total=Sum('total_amount'))['total'] or 0
        total_platform_fees = total_consultations * 50
        total_earnings = total_fees - total_platform_fees
        
        # Monthly earnings for chart (last 6 months - using actual months)
        today = datetime.now().date()
        chart_labels = []
        chart_data = []
        
        # Get unique months for the last 6 months
        for i in range(5, -1, -1):
            # Calculate month start date correctly
            month_date = today.replace(day=1) - timedelta(days=30*i)
            month_start = month_date.replace(day=1)
            
            # Calculate month end date correctly
            last_day = monthrange(month_start.year, month_start.month)[1]
            month_end = month_start.replace(day=last_day)
            
            # Get appointments for this month
            month_appointments = Appointment.objects.filter(
                dietitian=dietitian,
                status='completed',
                payment_status='paid',
                appointment_date__year=month_start.year,
                appointment_date__month=month_start.month
            )
            
            month_fees = month_appointments.aggregate(total=Sum('total_amount'))['total'] or 0
            month_earnings = month_fees - (month_appointments.count() * 50)
            
            # Only add month if it has data OR it's within the last 6 months
            chart_labels.append(month_start.strftime('%b %Y'))
            chart_data.append(float(month_earnings))
        
        # Remove duplicates by creating a dictionary
        unique_months = {}
        for label, data in zip(chart_labels, chart_data):
            if label not in unique_months:
                unique_months[label] = data
        
        chart_labels = list(unique_months.keys())
        chart_data = list(unique_months.values())
        
        # Current month earnings
        current_month = today.strftime('%B %Y')
        month_start = today.replace(day=1)
        last_day = monthrange(today.year, today.month)[1]
        month_end = today.replace(day=last_day)
        
        month_appointments = Appointment.objects.filter(
            dietitian=dietitian,
            status='completed',
            payment_status='paid',
            appointment_date__year=today.year,
            appointment_date__month=today.month
        )
        month_fees = month_appointments.aggregate(total=Sum('total_amount'))['total'] or 0
        monthly_earnings = month_fees - (month_appointments.count() * 50)
        
        # Average per consultation
        avg_per_consultation = total_earnings / total_consultations if total_consultations > 0 else 0
        
        # Consultation history
        consultations = []
        for apt in appointments.select_related('user').order_by('-appointment_date'):
            consultations.append({
                'date': apt.appointment_date,
                'patient_name': apt.user.name,
                'fee': float(apt.total_amount),
                'platform_fee': 50,
                'earnings': float(apt.total_amount) - 50
            })
        
        # Debug print
        print("Chart Labels:", chart_labels)
        print("Chart Data:", chart_data)
        print("Total Earnings:", total_earnings)
        
        context = {
            'dietitian': dietitian,
            'consultations': consultations,
            'total_consultations': total_consultations,
            'total_fees': total_fees,
            'total_platform_fees': total_platform_fees,
            'total_earnings': total_earnings,
            'monthly_earnings': monthly_earnings,
            'current_month': current_month,
            'avg_per_consultation': avg_per_consultation,
            'start_date': start_date,
            'end_date': end_date,
            'chart_labels': json.dumps(chart_labels),
            'chart_data': json.dumps(chart_data),
            'total_earnings_filtered': total_earnings,
        }
        
        return render(request, 'dietitian_payment_report.html', context)
        
    except Dietitian.DoesNotExist:
        messages.error(request, 'Dietitian not found')
        return redirect('dietitian_login')
    except Exception as e:
        print(f"Error in dietitian_earnings: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Error loading earnings: {str(e)}')
        return redirect('dietitian_dashboard')
def dietitian_slots(request):
    """Manage time slots"""
    if 'dietitian_id' not in request.session:
        return redirect('dietitian_login')
    
    dietitian = Dietitian.objects.get(id=request.session['dietitian_id'])
    
    # Get or create slots for next 7 days
    today = date.today()
    dates_to_generate = []
    
    for i in range(7):
        slot_date = today + timedelta(days=i)
        dates_to_generate.append(slot_date)
        
        # Create slots for each date if not exists
        for slot_time in DietitianSlot.SLOT_TIMES:
            DietitianSlot.objects.get_or_create(
                dietitian=dietitian,
                slot_date=slot_date,
                slot_time=slot_time[0],
                defaults={'is_booked': False}
            )
    
    # Handle leave dates
    if request.method == 'POST':
        leave_date = request.POST.get('leave_date')
        reason = request.POST.get('reason', '')
        
        if leave_date:
            # Delete all slots for that date
            DietitianSlot.objects.filter(dietitian=dietitian, slot_date=leave_date).delete()
            
            # Create leave record
            DietitianLeave.objects.create(
                dietitian=dietitian,
                leave_date=leave_date,
                reason=reason
            )
            messages.success(request, f'Marked {leave_date} as leave')
        
        return redirect('dietitian_slots')
    
    # Get slots for each date
    slots_by_date = {}
    for slot_date in dates_to_generate:
        # Check if leave
        is_leave = DietitianLeave.objects.filter(dietitian=dietitian, leave_date=slot_date).exists()
        
        if is_leave:
            slots_by_date[slot_date] = {'is_leave': True, 'slots': []}
        else:
            slots = DietitianSlot.objects.filter(dietitian=dietitian, slot_date=slot_date).order_by('slot_time')
            slots_by_date[slot_date] = {'is_leave': False, 'slots': slots}
    
    # Get existing leaves
    leaves = DietitianLeave.objects.filter(dietitian=dietitian, leave_date__gte=today).order_by('leave_date')
    
    context = {
        'dietitian': dietitian,
        'slots_by_date': slots_by_date,
        'leaves': leaves,
        'slot_times': DietitianSlot.SLOT_TIMES,
    }
    
    return render(request, 'dietitian_slots.html', context)


def dietitian_slot_toggle(request):
    """Toggle slot availability"""
    if 'dietitian_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    if request.method == 'POST':
        slot_id = request.POST.get('slot_id')
        action = request.POST.get('action')  # 'block' or 'unblock'
        
        slot = get_object_or_404(DietitianSlot, id=slot_id)
        
        if action == 'block':
            slot.is_booked = True
            slot.save()
            return JsonResponse({'success': True, 'message': 'Slot blocked'})
        elif action == 'unblock' and not slot.is_booked:
            slot.delete()
            return JsonResponse({'success': True, 'message': 'Slot unblocked'})
        
        return JsonResponse({'error': 'Invalid action'}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def dietitian_remove_leave(request, leave_id):
    """Remove a leave date"""
    if 'dietitian_id' not in request.session:
        return redirect('dietitian_login')
    
    leave = get_object_or_404(DietitianLeave, id=leave_id)
    
    if leave.dietitian.id != request.session['dietitian_id']:
        messages.error(request, 'Unauthorized')
        return redirect('dietitian_slots')
    
    # Recreate slots for that date
    for slot_time in DietitianSlot.SLOT_TIMES:
        DietitianSlot.objects.get_or_create(
            dietitian=leave.dietitian,
            slot_date=leave.leave_date,
            slot_time=slot_time[0],
            defaults={'is_booked': False}
        )
    
    leave.delete()
    messages.success(request, f'Leave removed for {leave.leave_date}')
    
    return redirect('dietitian_slots')