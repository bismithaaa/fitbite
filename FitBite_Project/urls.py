"""
URL configuration for FitBite_Project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from FitBite_App.views import *
from django.conf import settings
from django.conf.urls.static import static
from FitBite_App.views import seller_products


urlpatterns = [
    path('admin/', admin.site.urls),
    path('',index),
    path('log',openlogin, name='log'),
    path('reg',openreg),
    path('register',userreg, name='register'),
    path('cregister',sellerreg, name='cregister'),
    path('login',userlogin, name='login'),
    path('users',showuser),
    path('sellers',showseller),
    
    path('products',seller_products),
    path('logout',logout,name='logout'),
    path('update-product/',update_product, name='update_product'),
    path('delete-product/<int:pk>/',delete_product, name='delete_product'),
     path('opensearch/', openserch, name='opensearch'),
    path('searchproduct/', searchproduct, name='searchproduct'),
     path('profile/', user_profile, name='user_profile'),
    path('profile/update/', update_profile, name='update_profile'),
    path('profile/change-password/', change_password, name='change_password'),

    # Cart URLs
    path('add-to-cart/', add_to_cart, name='add_to_cart'),
    path('cart/', view_cart, name='view_cart'),
    path('update-cart/', update_cart_quantity, name='update_cart'),
    path('remove-from-cart/<int:cart_id>/', remove_from_cart, name='remove_from_cart'),
    path('get-cart-count/', get_cart_count, name='get_cart_count'),

    path('order/<int:product_id>/', place_order, name='place_order'),
    path('my-orders/', order_history, name='order_history'),
    path('order/<int:order_id>/', order_detail, name='order_detail'),
    path('order/<int:order_id>/track/', order_tracking, name='order_tracking'),
    path('order/<int:order_id>/cancel/', cancel_order, name='cancel_order'),
    path('my-orders/', order_history, name='order_history'),
    path('order/<int:order_id>/', order_detail, name='order_detail'),
    path('order/<int:order_id>/track/',order_tracking, name='order_tracking'),
    path('order/<int:order_id>/cancel/', cancel_order, name='cancel_order'),
    path('order/<int:order_id>/reorder/',reorder, name='reorder'),
    path('seller-dashboard/', seller_dashboard, name='seller_dashboard'),
    path('seller-logout/', seller_logout, name='seller_logout'),
    # Payment URLs
    path('payment/<int:order_id>/', initiate_payment, name='initiate_payment'),
    path('payment-success/', payment_success, name='payment_success'),
path('seller-dashboard/', seller_dashboard, name='seller_dashboard'),
    path('seller-products/', seller_products, name='seller_products'),
    path('add-product/', addproducts, name='add_product'),
    path('update-product/', update_product, name='update_product'),
    path('delete-product/<int:pk>/', delete_product, name='delete_product'),
    path('seller-orders/', seller_orders, name='seller_orders'),
    path('seller-order/<int:order_id>/', seller_order_detail, name='seller_order_detail'),
    path('update-order-status/<int:order_id>/', update_order_status, name='update_order_status'),
    path('seller-inventory/', seller_inventory, name='seller_inventory'),
    path('seller-profile/', seller_profile, name='seller_profile'),
    path('seller-analytics/', seller_analytics, name='seller_analytics'),
    path('seller-transactions/', seller_transactions, name='seller_transactions'),
    path('seller-notifications/', seller_notifications, name='seller_notifications'),
    path('seller-dashboard-stats/', seller_dashboard_stats, name='seller_dashboard_stats'),
    path('restock-product/', restock_product, name='restock_product'),
path('bulk-restock/', bulk_restock, name='bulk_restock'),
path('get-product/<int:product_id>/', get_product_details, name='get_product_details'),

     path('admin-chart-data/', admin_chart_data, name='admin_chart_data'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin-users/', admin_users, name='admin_users'),
    path('admin-sellers/', admin_sellers, name='admin_sellers'),
    path('admin-products/', admin_products, name='admin_products'),
    path('admin-orders/', admin_orders, name='admin_orders'),
    path('admin-logout/', admin_logout, name='admin_logout'),
    path('checkout/', checkout_from_cart, name='checkout_from_cart'),
    path('place-order-from-cart/', place_order_from_cart, name='place_order_from_cart'),
    path('payment/<int:order_id>/', initiate_payment, name='initiate_payment'),
    path('payment-success/', payment_success, name='payment_success'),
    path('payment-failure/', payment_failure, name='payment_failure'),
    
    # Cart Data API
    path('cart-data/', cart_data, name='cart_data'),
    path('clear-cart/', clear_cart, name='clear_cart'),
    path('userdashboard/', userdashboard, name='userdashboard'),
     path('admin-pending-sellers/', admin_pending_sellers, name='admin_pending_sellers'),
    path('admin-seller/<int:seller_id>/', admin_seller_detail, name='admin_seller_detail'),
    path('approve-seller/<int:seller_id>/', approve_seller, name='approve_seller'),
    path('reject-seller/<int:seller_id>/', reject_seller, name='reject_seller'),
    path('suspend-seller/<int:seller_id>/', suspend_seller, name='suspend_seller'),
    path('bulk-seller-action/', bulk_seller_action, name='bulk_seller_action'),
    path('admin-revenue/',admin_revenue, name='admin_revenue'),

    path('give-feedback/',give_feedback, name='give_feedback'),
    path('submit-feedback/',submit_feedback, name='submit_feedback'),
    path('my-feedback/',user_feedback, name='user_feedback'),
    path('seller-feedback/',seller_feedback, name='seller_feedback'),
    path('admin-feedback/',admin_feedback, name='admin_feedback'),
    path('userfeedback/',user_feedback, name='user_feedback'),


    # Add to your urlpatterns
path('admin-dietitians/', admin_dietitians, name='admin_dietitians'),
path('admin-add-dietitian/', admin_add_dietitian, name='admin_add_dietitian'),
path('admin-edit-dietitian/<int:dietitian_id>/', admin_edit_dietitian, name='admin_edit_dietitian'),
path('admin-delete-dietitian/<int:dietitian_id>/', admin_delete_dietitian, name='admin_delete_dietitian'),
path('admin-toggle-dietitian-status/<int:dietitian_id>/', admin_toggle_dietitian_status, name='admin_toggle_dietitian_status'),
# Add to your urlpatterns:
# Dietitian URLs

path('dietitian-dashboard/',dietitian_dashboard, name='dietitian_dashboard'),
path('dietitian-messages/', dietitian_messages, name='dietitian_messages'),
path('dietitian-send-message/', dietitian_send_message, name='dietitian_send_message'),
path('dietitian-appointments/', dietitian_appointments, name='dietitian_appointments'),
path('dietitian-update-appointment/<int:appointment_id>/', dietitian_update_appointment_status, name='dietitian_update_appointment'),
path('dietitian-slots/', dietitian_slots, name='dietitian_slots'),
path('dietitian-slot-toggle/', dietitian_slot_toggle, name='dietitian_slot_toggle'),
path('dietitian-remove-leave/<int:leave_id>/', dietitian_remove_leave, name='dietitian_remove_leave'),

# User Appointment URLs
path('dietitians/', get_dietitians, name='get_dietitians'),
path('get-dietitian-slots/', get_dietitian_slots, name='get_dietitian_slots'),
path('book-appointment/', book_appointment, name='book_appointment'),
path('verify-appointment-payment/',verify_appointment_payment, name='verify_appointment_payment'),
path('my-appointments/',my_appointments, name='my_appointments'),
path('cancel-appointment/<int:appointment_id>/', cancel_appointment, name='cancel_appointment'),
path('send-message-to-dietitian/', send_message_to_dietitian, name='send_message_to_dietitian'),
path('my-messages/', my_messages, name='my_messages'),
path('get-new-messages/', get_new_messages, name='get_new_messages'),
# In urls.py, add:
path('get-dietitian-new-messages/', get_dietitian_new_messages, name='get_dietitian_new_messages'),
path('get-latest-message-id/',get_latest_message_id, name='get_latest_message_id'),
path('dietitian-generate-slots/', dietitian_generate_slots, name='dietitian_generate_slots'),
path('dietitian-payment-report/', dietitian_payment_report, name='dietitian_payment_report'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



