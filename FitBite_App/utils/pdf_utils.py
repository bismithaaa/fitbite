from django.template.loader import get_template
from django.core.mail import EmailMessage
from django.conf import settings
from django.template import Context
from io import BytesIO
from xhtml2pdf import pisa
import logging
import socket
import smtplib

logger = logging.getLogger(__name__)

def generate_invoice_pdf(order, customer, product):
    """Generate PDF invoice for order"""
    try:
        # Load template
        template = get_template('invoice.html')
        
        # Calculate total with shipping
        subtotal = float(order.total_amount)
        shipping = 50.00
        grand_total = subtotal + shipping
        
        # Get plan name
        if order.plan == 'single':
            plan_name = 'Single Day'
        elif order.plan == 'weekly':
            plan_name = 'Weekly Plan'
        else:
            plan_name = 'Monthly Plan'
        
        context = {
            'order': order,
            'customer': customer,
            'product': product,
            'subtotal': subtotal,
            'shipping': shipping,
            'grand_total': grand_total,
            'order_date': order.order_date,
            'plan_name': plan_name,
        }
        
        html = template.render(context)
        
        # Create PDF
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        
        if not pdf.err:
            logger.info(f"PDF generated successfully for order {order.order_id}")
            return result.getvalue()
        else:
            logger.error(f"PDF generation error for order {order.order_id}: {pdf.err}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating PDF for order {order.order_id}: {str(e)}")
        return None

def send_invoice_email(order, customer, product, seller):
    """Send invoice PDF to customer and seller"""
    
    try:
        # Check email configuration
        if not all([settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD]):
            logger.error("Email configuration is incomplete")
            return False, "Email configuration is incomplete"
        
        # Generate PDF
        pdf_content = generate_invoice_pdf(order, customer, product)
        
        # Plan name
        if order.plan == 'single':
            plan_name = 'Single Day'
        elif order.plan == 'weekly':
            plan_name = 'Weekly Plan'
        else:
            plan_name = 'Monthly Plan'
        
        # Calculate totals
        subtotal = float(order.total_amount)
        shipping = 50.00
        grand_total = subtotal + shipping
        platform_fee = 50.00
        seller_payout = subtotal
        
        # Format date
        order_date = order.order_date.strftime('%d %B %Y, %I:%M %p')
        
        # ========== CUSTOMER EMAIL ==========
        customer_subject = f'🧾 Your Invoice - FitBite Order #{order.order_id}'
        
        customer_message = f"""
Dear {customer.name},

Thank you for your order! Your invoice is attached to this email.

📋 ORDER DETAILS
════════════════════════════════
Order ID: {order.order_id}
Order Date: {order_date}

🛍️ PRODUCT DETAILS
────────────────────────────
Product: {product.product_name}
Seller: {seller.company_name}
Plan: {plan_name}
Quantity: 1

💰 PRICE BREAKDOWN
────────────────────────────
Subtotal: ₹{subtotal:.2f}
Platform Fee: ₹{shipping:.2f}
Total Amount: ₹{grand_total:.2f}

📍 DELIVERY ADDRESS
────────────────────────────
{order.full_name}
{order.phone}
{order.address}
{order.city}, {order.state} - {order.pincode}

📅 Delivery Schedule: {order.start_date} to {order.end_date}

Thank you for choosing FitBite!

Regards,
FitBite Team
"""
        
        # ========== SELLER EMAIL ==========
        seller_subject = f'💰 New Order Received - FitBite Order #{order.order_id}'
        
        seller_message = f"""
Dear {seller.company_name},

Great news! You've received a new order through FitBite.

📋 ORDER DETAILS
════════════════════════════════
Order ID: {order.order_id}
Order Date: {order_date}

🛍️ PRODUCT DETAILS
────────────────────────────
Product: {product.product_name}
Plan: {plan_name}
Quantity: 1

💰 PAYMENT BREAKDOWN
────────────────────────────
Product Price: ₹{subtotal:.2f}
Platform Fee: ₹{platform_fee:.2f}
Your Payout: ₹{seller_payout:.2f}

👤 CUSTOMER DETAILS
────────────────────────────
Name: {order.full_name}
Phone: {order.phone}
Email: {customer.email}

📍 SHIPPING ADDRESS
────────────────────────────
{order.address}
{order.city}, {order.state} - {order.pincode}

📅 Delivery Schedule: {order.start_date} to {order.end_date}

Please process this order soon.

Regards,
FitBite Team
"""
        
        success_count = 0
        errors = []
        
        # Test SMTP connection first
        try:
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
            server.starttls()
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            server.quit()
            logger.info("SMTP connection test successful")
        except Exception as e:
            logger.error(f"SMTP connection test failed: {str(e)}")
            return False, f"Email server connection failed: {str(e)}"
        
        # Send to customer
        try:
            customer_email = EmailMessage(
                subject=customer_subject,
                body=customer_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[customer.email],
                reply_to=[settings.DEFAULT_FROM_EMAIL],
            )
            
            if pdf_content:
                customer_email.attach(f'invoice_{order.order_id}.pdf', pdf_content, 'application/pdf')
            
            customer_email.send(fail_silently=False)
            logger.info(f"✅ Customer email sent to {customer.email}")
            success_count += 1
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"Email authentication failed. Check your email password/app password."
            logger.error(f"❌ {error_msg}")
            errors.append(error_msg)
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            errors.append(error_msg)
        except socket.error as e:
            error_msg = f"Network error: Check your internet connection"
            logger.error(f"❌ {error_msg}")
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"Customer email failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            errors.append(error_msg)
        
        # Send to seller
        try:
            seller_email = EmailMessage(
                subject=seller_subject,
                body=seller_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[seller.email],
                reply_to=[settings.DEFAULT_FROM_EMAIL],
            )
            
            if pdf_content:
                seller_email.attach(f'invoice_{order.order_id}.pdf', pdf_content, 'application/pdf')
            
            seller_email.send(fail_silently=False)
            logger.info(f"✅ Seller email sent to {seller.email}")
            success_count += 1
        except Exception as e:
            error_msg = f"Seller email failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            errors.append(error_msg)
        
        if success_count > 0:
            return True, f"✅ Emails sent successfully: {success_count}/2"
        else:
            error_text = "; ".join(errors)
            return False, f"❌ All emails failed: {error_text}"
            
    except Exception as e:
        logger.error(f"❌ Email function error: {str(e)}")
        return False, str(e)