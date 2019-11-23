from django.shortcuts import render
from .models import Item, Order, OrderItem, BillingAddress, Payment, Coupon, Refund
from .forms import CheckoutForm, CouponForm,RefundForm
from django.views.generic import ListView, DetailView, View
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
import random
import string
# `source` is obtained with Stripe.js; see https://stripe.com/docs/payments/accept-a-payment-charges#web-create-token

# Create your views here.

def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

class HomeView(ListView):
    model = Item
    paginate_by = 10
    template_name = "home-page.html"

class CheckoutView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }
            return render(self.request, "checkout-page.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You don't have an active order")        
            return redirect("my_app:checkout")
        

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zipp = form.cleaned_data.get('zipp')
                # same_billing_address = form.cleaned_data.get('same_billing_address')
                # save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')
                billing_address = BillingAddress(
                    user = self.request.user,
                    street_address = street_address,
                    apartment_address = apartment_address,
                    country = country,
                    zipp = zipp,                
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()

                if payment_option == 'S':            
                    return redirect('my_app:payment', payment_option='stripe')
                elif payment_option == 'S':               
                    return redirect('my_app:payment', payment_option='stripe')
                else:
                    messages.warning(self.request, "Invalid payment option selected")
                    return redirect('my_app:checkout')
        except ObjectDoesNotExist:
            messages.warning(request, "You don not have an active order")
            return redirect("my_app:order-summary")
        

class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False
            }
            return render(self.request, "payment.html", context)
        else:
            messages.warning(request, "You have not added a billing address")
            return redirect("my_app:checkout") 

    def post(self, *args, **kwargs):
        print("girdiii")
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        amount = int(order.get_total() * 100) 

        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency="usd",
                source=token,
                description="Charge for " + self.request.user.username,
            )
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total()
            payment.save()

            order_items = order.items.all()
            order_items.update(ordered=True)
            for item in order_items:
                item.save()

 
            order.ordered = True
            order.payment = payment
            order.ref_code = create_ref_code()
            order.save()

            messages.success(self.request, "Successful Payment")
            return redirect("/")


        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            messages.warning(self.request, "Rate Limit Error")
            return redirect("/")

            # Since it's a decline, stripe.error.CardError will be caught

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.warning(self.request, "Invalid parameters")
            return redirect("/")

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.warning(self.request, "Invalid Request")
            return redirect("/")

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.warning(self.request, "Not authenticated")
            return redirect("/")

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.warning(self.request, "Network Error")
            return redirect("/")

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.warning(self.request, "Something went wrong")
            return redirect("/")

        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            messages.warning(self.request, "Something went terribly wrong")
            return redirect("/")

       

class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                    'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You don not have an active order")
            return redirect("/")

class ItemDetailView(DetailView):
    model = Item
    template_name = "product-page.html"

# class ProdcuctDetailView(DetailView):
#     model = Item
#     template_name = "product-page.html"

def item_list(request):
    context = {
        "items": Item.objects.all()
    }
    return render(request, "item_list.html", context)

def products(request):
    return render(request, "product-page.html") 

@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item qunatity was updated")
            return redirect("my_app:product", slug=slug)
        else:
            messages.info(request, "This item was added to your cart")
            order.items.add(order_item)
            return redirect("my_app:product", slug=slug)

    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart")
        return redirect("my_app:product", slug=slug)

@login_required
def remove_from_cart(request, slug):   
    full_path = "http://" + request.META.get('REMOTE_ADDR') + ":" + request.META['SERVER_PORT'] + "/order-summary/"    
    requested_path = request.META.get('HTTP_REFERER')
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False 
    )
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0] 
            order.items.remove(order_item)
            messages.info(request, "This item was removed from your cart")            
            if requested_path == full_path:
                return redirect("my_app:order-summary")                
            return redirect("my_app:product", slug=slug)
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("my_app:product", slug=slug)
    else:
        messages.info(request, "You don't have an active order")
        return redirect("my_app:product", slug=slug)

@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated")
            return redirect("my_app:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("my_app:product", slug=slug)
    else:
        messages.info(request, "You don't have an active order")
        return redirect("my_app:product", slug=slug)

@login_required
def add_single_item_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated")
            return redirect("my_app:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("my_app:order-summaryt")
    else:
        messages.info(request, "You don't have an active order")
        return redirect("my_app:order-summary")


def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This is not a valid coupon code")        
        return redirect("my_app:checkout")

class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(user=request.user, ordered=False)
                order.coupon = get_coupon(request, code) 
                order.save()
                messages.success(request, "Successful")        
                return redirect("my_app:checkout")
            except ObjectDoesNotExist:
                messages.info(request, "You don't have an active order")        
                return redirect("my_app:checkout")

class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }
        return render(self.request, "request_refund.html", context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST or None)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save() 

                messages.info(self.request, "Your request was recieved")
                return redirect("my_app:request-refund")

            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist")
                return redirect("my_app:request-refund")