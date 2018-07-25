# -*- coding: utf-8 -*-
from constance import config
from django.contrib import admin
from django.core.mail import send_mass_mail
from django.shortcuts import render
from django.utils import timezone
from iamport import Iamport

from .models import Registration, Option, ManualPayment, IssueTicket


def send_email_about_pending_vbank_transfer(modeladmin, request, queryset):
    messages = []
    subject = '파이콘 한국 2018 가상 계좌 입금 대기 안내, Please Check your virtual bank transfer for PyCon Korea 2018 Ticket'
    body = '''
안녕하세요. 파이콘 한국 2018 준비위원회입니다.

파이콘 한국 2018 신청의 결제 방법으로 가상 계좌를 선택해주셨으나,
입금 여부가 확인되지 않고 있습니다.

혹시 다른 이름으로 입금하신 분은 support@pycon.kr로 메일 남겨주시기 바랍니다.

입금 마감 기간은 구매일로부터 일주일 입니다.
감사합니다.

Hi, This is PyCon Korea 2018 Organizing Team.

You choose the virtual bank transfer for PyCon Korea 2018 Registration,
But we still cannot check your transfer history.

If you already transferred, please send an e-mail to support@pycon.kr.
If you did not, you can transfer by a week from you registered date.
Thank you.

Best Regards.
    '''
    from_email = 'pyconkr@pycon.kr'
    for obj in queryset:
        email = obj.email
        message = (subject, body, from_email, [email])
        messages.append(message)
    send_mass_mail(messages, fail_silently=False)


send_email_about_pending_vbank_transfer.short_description = 'Send Virtual Bank Transfer Email'


def cancel_registration(modeladmin, request, queryset):
    messages = []
    subject = '파이콘 한국 2018 결제 취소 알림, PyCon Korea 2018 Ticket is cancelled successfully'
    body = '''
안녕하세요. 파이콘 한국 2018 준비위원회입니다.

결제가 취소되었음을 알려드립니다.
결제 대행사 사정에 따라 다소 늦게 결제 취소가 이뤄질 수 있습니다.

다른 문의 사항은 support@pycon.kr 로 메일 부탁드립니다.
감사합니다.

Hi, This is PyCon Korea 2018 Organizing Team.

We are sending this email for your PyCon Korea 2018 Ticket is cancelled successfully.
Because of Payment Gateway's reasons, It will be delayed.

If you have a question, feel free to e-mail to support@pycon.kr.
Thank you.

Best Regards.
    '''
    from_email = 'pyconkr@pycon.kr'

    results = []
    now = timezone.now()

    for obj in queryset:
        if obj.payment_method != 'card':
            obj.cancel_reason = '카드 결제만 취소 가능'
            results.append(obj)
            continue

        if obj.payment_status != 'paid':
            obj.cancel_reason = '결제 완료만 취소 가능'
            results.append(obj)
            continue

        if not obj.option.is_cancelable:
            obj.cancel_reason = '취소 불가능 옵션 (얼리버드 등)'
            results.append(obj)
            continue

        if obj.option.cancelable_date and obj.option.cancelable_date < now:
            obj.cancel_reason = '취소가능일자가 아니므로 취소 불가능'
            results.append(obj)
            continue

        try:
            iamport = Iamport(imp_key=config.IMP_DOM_API_KEY, imp_secret=config.IMP_DOM_API_SECRET)
            iamport.cancel_by_merchant_uid('Django Admin에서 결제 취소', obj.merchant_uid)
        except IOError:
            obj.cancel_status = 'IOError'
            results.append(obj)
            continue
        except Iamport.HttpError as e:
            obj.cancel_status = e.code
            obj.cancel_reason = e.reason
            results.append(obj)
            continue
        except Iamport.ResponseError as e:
            obj.cancel_status = e.code
            obj.cancel_reason = e.message
            results.append(obj)
            continue

        obj.canceled = now
        obj.payment_status = 'cancelled'
        obj.save(update_fields=['payment_status', 'canceled'])

        obj.cancel_status = 'CANCELLED'
        results.append(obj)

        message = (subject, body, from_email, [obj.email])
        messages.append(message)

    send_mass_mail(messages, fail_silently=False)
    return render(request, 'registration/cancellation_result.html', {'results': results})


cancel_registration.short_description = 'Cancel registration'


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_type', 'conference_type', 'is_active',
                    'begin_at', 'closed_at',
                    'price', 'is_cancelable', 'cancelable_date',)
    list_editable = ('is_active',)
    ordering = ('id',)


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'option', 'name', 'email', 'payment_method',
                    'payment_status', 'created', 'confirmed', 'canceled')
    list_editable = ('payment_status',)
    list_filter = ('option', 'payment_method', 'payment_status')
    csv_fields = ['name', 'email', 'company', 'option', ]
    search_fields = ('name', 'email', 'merchant_uid', 'transaction_code',)
    readonly_fields = ('created', 'merchant_uid', 'transaction_code',)
    ordering = ('id',)
    actions = (send_email_about_pending_vbank_transfer, cancel_registration)


@admin.register(IssueTicket)
class IssueTicketAdmin(admin.ModelAdmin):
    list_display = ('registration', 'issuer', 'issue_date')
    ordering = ('issue_date',)


@admin.register(ManualPayment)
class ManualPaymentAdmin(admin.ModelAdmin):
    list_display = ('title', 'payment_status', 'user',)
    list_filter = ('payment_status',)
    search_fields = ('user__email', 'description',)
    raw_id_fields = ('user',)

    class Meta:
        model = ManualPayment
