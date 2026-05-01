from django.db import models
from datetime import datetime

class user(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    password = models.CharField(max_length=100)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True, default='profile_pics/default-avatar.png')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

from django.db import models

class Seller(models.Model):
    # Status choices
    STATUS_CHOICES = (
        ('pending', 'Pending Verification'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    )

    company_name = models.CharField(max_length=150)
    owner_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)  # Make email unique
    phone = models.CharField(max_length=15)
    address = models.TextField()
    gst_number = models.CharField(max_length=15, unique=True)
    password = models.CharField(max_length=100)
    
    # New fields for verification
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    registered_date = models.DateTimeField(auto_now_add=True)
    verified_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    verified_by = models.ForeignKey('user', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_sellers')
    
    # Documents for verification (optional)
    gst_certificate = models.FileField(upload_to='seller_documents/gst/', null=True, blank=True)
    business_license = models.FileField(upload_to='seller_documents/license/', null=True, blank=True)
    address_proof = models.FileField(upload_to='seller_documents/address/', null=True, blank=True)

    def __str__(self):
        return f"{self.company_name} - {self.get_status_display()}"

    class Meta:
        ordering = ['-registered_date']

class meals(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    meal_type = models.CharField(max_length=10)

class products(models.Model):
    seller = models.ForeignKey(Seller,on_delete=models.CASCADE)
    product_name = models.CharField(max_length=150)
    description = models.TextField()
    image = models.ImageField(upload_to='product_images/',null=True,blank=True)
    category = models.CharField(max_length=200)
    calories = models.PositiveIntegerField(null=True)
    protein = models.FloatField(null=True, blank=True)
    carbs = models.FloatField(null=True, blank=True)
    fat = models.FloatField(null=True, blank=True)
    fiber= models.FloatField(null=True, blank=True)
    price = models.DecimalField(max_digits=8,decimal_places=2)
    stock_quantity = models.PositiveIntegerField()
    weight = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return self.product_name
    



class Orders(models.Model):

    ORDER_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('prepared', 'Prepared'),
        ('dispatched', 'Dispatched'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    PLAN_CHOICES = (
        ('single', 'Single Day'),
        ('weekly', 'Weekly Plan'),
        ('monthly', 'Monthly Plan'),
    )

    # 🔗 Relations
    customer = models.ForeignKey(user, on_delete=models.CASCADE, related_name='orders')
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, null=True, blank=True)

    # 📦 Order Info
    order_id = models.CharField(max_length=100, unique=True)
    order_date = models.DateTimeField(auto_now_add=True)

    # 🏠 Delivery Address
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)

    # 🗓️ Subscription / Plan
    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default='single'
    )
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)

    # 💰 Payment
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    razorpay_order_id = models.CharField(max_length=200, null=True, blank=True) 
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )

    # 🚚 Order Status
    order_status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='pending'
    )

    def __str__(self):
        return f"Order {self.order_id} - {self.customer.name}"
    
class OrderItem(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(products, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.product_name} ({self.quantity})"
class Feedbacks(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE)
    product = models.ForeignKey(products, on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, null=True, blank=True)
    rating = models.IntegerField(default=5, choices=[(i, i) for i in range(1, 6)])
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.user.name} - {self.rating}★"

    class Meta:
        ordering = ['-submitted_at']

class Cart(models.Model):
    user_email = models.EmailField()
    product = models.ForeignKey(products, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user_email', 'product']  # Prevent duplicate products for same user
    
    def __str__(self):
        return f"{self.user_email} - {self.product.product_name} ({self.quantity})"
    
    @property
    def total_price(self):
        return self.product.price * self.quantity


class Dietitian(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    
    # Personal Information
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    
    # Professional Information
    qualification = models.CharField(max_length=200)  # e.g., "M.Sc. Nutrition, Registered Dietitian"
    specialization = models.CharField(max_length=200)  # e.g., "Weight Management, Sports Nutrition"
    
    # Contact Information
    address = models.TextField()
    location = models.CharField(max_length=100)  # e.g., "Downtown", "North Side"
    
    # Media
    image = models.ImageField(upload_to='dietitians/', null=True, blank=True)
    
    # Account Information
    password = models.CharField(max_length=128)  # For login access
    
    # Status and Timestamps
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.specialization}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Dietitian'
        verbose_name_plural = 'Dietitians'


class DietitianLeave(models.Model):
    """Model for dietitian leave dates"""
    dietitian = models.ForeignKey(Dietitian, on_delete=models.CASCADE, related_name='leaves')
    leave_date = models.DateField()
    reason = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['dietitian', 'leave_date']
    
    def __str__(self):
        return f"{self.dietitian.name} - {self.leave_date}"


class DietitianSlot(models.Model):
    """Model for dietitian time slots (10 slots per day)"""
    SLOT_TIMES = [
        ('09:00', '09:00 AM'),
        ('09:30', '09:30 AM'),
        ('10:00', '10:00 AM'),
        ('10:30', '10:30 AM'),
        ('11:00', '11:00 AM'),
        ('11:30', '11:30 AM'),
        ('12:00', '12:00 PM'),
        ('12:30', '12:30 PM'),
        ('14:00', '02:00 PM'),
        ('14:30', '02:30 PM'),
        ('15:00', '03:00 PM'),
        ('15:30', '03:30 PM'),
        ('16:00', '04:00 PM'),
        ('16:30', '04:30 PM'),
        ('17:00', '05:00 PM'),
        ('17:30', '05:30 PM'),
    ]
    
    dietitian = models.ForeignKey(Dietitian, on_delete=models.CASCADE, related_name='slots')
    slot_date = models.DateField()
    slot_time = models.CharField(max_length=5, choices=SLOT_TIMES)
    is_booked = models.BooleanField(default=False)
    booked_by = models.ForeignKey('user', on_delete=models.SET_NULL, null=True, blank=True, related_name='booked_slots')
    booked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['dietitian', 'slot_date', 'slot_time']
    
    def __str__(self):
        return f"{self.dietitian.name} - {self.slot_date} {self.slot_time}"


class DietitianMessage(models.Model):
    """Model for chat messages between users and dietitians"""
    dietitian = models.ForeignKey(Dietitian, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey('user', on_delete=models.CASCADE, related_name='dietitian_messages')
    message = models.TextField()
    is_from_user = models.BooleanField(default=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{'User' if self.is_from_user else 'Dietitian'} - {self.dietitian.name}"

class Appointment(models.Model):
    """Model for dietitian appointments"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    )
    
    appointment_id = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey('user', on_delete=models.CASCADE, related_name='appointments')
    dietitian = models.ForeignKey(Dietitian, on_delete=models.CASCADE, related_name='appointments')
    slot = models.ForeignKey(DietitianSlot, on_delete=models.CASCADE, related_name='appointment')
    appointment_date = models.DateField()
    appointment_time = models.CharField(max_length=5)
    
    # Appointment details
    reason = models.TextField()
    symptoms = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=300.00)
    platform_fee = models.DecimalField(max_digits=8, decimal_places=2, default=50.00)
    total_amount = models.DecimalField(max_digits=8, decimal_places=2, default=350.00)  # Set your fee
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    razorpay_order_id = models.CharField(max_length=200, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=200, null=True, blank=True)
    
    def __str__(self):
        return f"Appointment {self.appointment_id} - {self.user.name} with {self.dietitian.name}"
    
    def save(self, *args, **kwargs):
        if not self.appointment_id:
            import random
            import string
            self.appointment_id = f"APT{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100,999)}"
        super().save(*args, **kwargs)



