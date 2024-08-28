from django.http import JsonResponse
import razorpay
import json
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Wallet, Transaction
from django.contrib.auth.decorators import login_required
from decimal import Decimal


# def wallet(request):
#     wallet = Wallet.objects.get_or_create(user=request.user)
#     transaction = Transaction.objects.filter(wallet=wallet).order_by('-timestamp')

#     context = {
#         'wallet' : wallet,
#         'transaction' : transaction,
#     }
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required
def wallet_recharge(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        if not amount or not amount.isdigit() or int(amount) <= 0:
            print('amount is missing')
            messages.error(request, 'Please enter a valid amount.')
            return redirect('user:my_account')
        amount = Decimal(amount)
        print('amount', amount)
        receipt_maker ='text'
        notes = {'order-type':'Recharge for waller'}
        razorpay_order = razorpay_client.order.create(dict(
                    amount = int(amount * 100 ) ,
                    currency = 'INR',
                    notes = notes,
                    receipt = receipt_maker,
                    payment_capture  = '1'
                ))
        callback_url = 'http://127.0.0.1:8000/wallet/payment_success/'
        
        context = {
            
            'key': settings.RAZORPAY_KEY_ID,
            'amount': int(amount * 100),
            'id': razorpay_order['id'],
            'callback_url':callback_url,
            'user': request.user
        }
    return render(request, 'user_side/my_account.html', context)
    

@csrf_exempt
def payment_success(request):
    if request.method == 'POST':
        user = request.user
        try:
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_signature = request.POST.get('razorpay_signature')
            print('payment_id',razorpay_payment_id)
            print('razorpay_signature',razorpay_signature)

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
                messages.error(request, 'Payment failed: Missing payment information.')
                return redirect('user:my_account')
            
            try:
                client.utility.verify_payment_signature({
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature

                    })
               
            except razorpay.errors.SignatureVerificationError:
                messages.error(request, 'Payment verification failed.')
                return redirect('user:my_account')
            
            payment_details = client.payment.fetch(razorpay_payment_id)
            amount = Decimal(payment_details['amount']) / 100

            wallet = Wallet.objects.get(user=user)
            wallet.balance += Decimal(amount)
            wallet.save()

            Transaction.objects.create(wallet=wallet, amount=amount, description='Wallet Recharge')
            messages.success(request, 'Wallet recharged successfully!')
            return redirect('user:my_account')
        
        except Exception as e:
            print(f'Error-------------------------: {e}--------------------------')
            messages.error(request, 'Payment verification failed!')
            return redirect('user:my_account')
        
    return render(request,'user_side/my_account.html')