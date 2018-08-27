# -*- coding: utf-8 -*-
import datetime
import logging
from uuid import uuid4

import pytz
from constance import config
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView
from iamport import Iamport

from pyconkr.helper import render_io_error
from pyconkr.models import SprintProposal, SprintCheckin, Speaker
from .forms import (RegistrationForm, RegistrationAdditionalPriceForm,
                    ManualPaymentForm, IssueSubmitForm, RegistrationFormWithoutTopSize)
from .iamporter import IamporterError
from .models import Option, Registration, ManualPayment, IssueTicket, EVENT_CONFERENCE, EVENT_YOUNG, EVENT_BABYCARE, \
    EVENT_TUTORIAL

logger = logging.getLogger(__name__)
payment_logger = logging.getLogger('payment')


def index(request):
    is_registered = False

    if request.user.is_authenticated():
        is_registered = (Registration.objects.active_conference()
                         .filter(user=request.user, payment_status__in=['paid', 'ready'])
                         .exists())

    options = Option.objects.active_conference()
    ctx = {
        'options': options,
        'is_registered': is_registered
    }
    return render(request, 'registration/info.html', ctx)


@login_required
def status(request, option_id):
    option = Option.objects.get(id=option_id)
    registrations = Registration.objects.filter(user=request.user, option=option)

    context = {
        'registrations': registrations,
        'option': option,
        'title': _("Registration Status"),
    }
    return render(request, 'registration/status.html', context)


def _redirect_registered(option):
    return redirect('registration_status', option.id)


@login_required
def certificates(request):
    registered = Registration.objects.filter(user=request.user,
                                             payment_status='paid',
                                             option__event_type='conference').exists()
    context = {
        'user': request.user
    }
    if not registered:
        # Not Registered
        return render(request, 'registration/certificates_not_registered.html', context)
    registration = Registration.objects.filter(user=request.user,
                                               payment_status='paid',
                                               option__event_type='conference').first()
    visited = IssueTicket.objects.filter(registration=registration).exists()
    if not visited:
        # Not Visited
        return render(request, 'registration/certificates_not_visited.html', context)
    current_date = datetime.datetime.now()
    seoul_date = current_date.astimezone(pytz.timezone('Asia/Seoul'))
    context = {
        'registration': registration,
        'year': seoul_date.year,
        'month': seoul_date.month,
        'day': seoul_date.day
    }
    return render(request, 'registration/certificates.html', context)


@login_required
def certificates_sprint(request):
    registered = SprintCheckin.objects.filter(user=request.user).exists()
    context = {
        'user': request.user
    }
    if not registered:
        # Not Registered
        return render(request, 'registration/certificates_sprint_not_registered.html', context)
    current_date = datetime.datetime.now()
    seoul_date = current_date.astimezone(pytz.timezone('Asia/Seoul'))
    context = {
        'user': request.user,
        'year': seoul_date.year,
        'month': seoul_date.month,
        'day': seoul_date.day
    }
    return render(request, 'registration/certificates_sprint.html', context)


@login_required
def certificates_tutorial(request):
    registered = Registration.objects.filter(user=request.user,
                                             payment_status='paid',
                                             option__event_type='tutorial').exists()
    context = {
        'user': request.user
    }
    if not registered:
        # Not Registered
        return render(request, 'registration/certificates_tutorial_not_registered.html', context)
    registration = Registration.objects.filter(user=request.user,
                                               payment_status='paid',
                                               option__event_type='tutorial').first()
    visited = IssueTicket.objects.filter(registration=registration).exists()
    if not visited:
        # Not Visited
        return render(request, 'registration/certificates_tutorial_not_visited.html', context)
    current_date = datetime.datetime.now()
    seoul_date = current_date.astimezone(pytz.timezone('Asia/Seoul'))
    context = {
        'registration': registration,
        'year': seoul_date.year,
        'month': seoul_date.month,
        'day': seoul_date.day
    }
    return render(request, 'registration/certificates_tutorial.html', context)


@login_required
def payment(request, option_id):
    product = Option.objects.get(id=option_id)

    if not product.is_opened:
        return redirect('registration_index')

    is_registered = Registration.objects.filter(
        user=request.user, option=product,
        payment_status__in=['paid', 'ready']
    ).exists()

    if is_registered and product.event_type != EVENT_YOUNG:
        return _redirect_registered(product)

    uid = str(uuid4()).replace('-', '')

    if product.has_additional_price:
        form = RegistrationAdditionalPriceForm(initial={'email': request.user.email,
                                                        'option': product,
                                                        'base_price': product.price})
    elif product.event_type != EVENT_CONFERENCE:
        form = RegistrationFormWithoutTopSize(initial={'email': request.user.email,
                                                       'option': product,
                                                       'base_price': product.price})
    else:
        form = RegistrationForm(initial={'email': request.user.email,
                                         'option': product,
                                         'base_price': product.price})

    sold_out = False
    has_conference_ticket = False
    if product.event_type == EVENT_YOUNG:
        render_page = 'registration/payment_youngcoder.html'
        sold_out = product.is_sold_out
    elif product.event_type == EVENT_BABYCARE:
        options = Option.objects.filter(event_type=EVENT_CONFERENCE)
        has_conference_ticket = Registration.objects.filter(user=request.user,
                                                            option__in=options,
                                                            payment_status__in=['paid']).exists()

        render_page = 'registration/payment_babycare.html'
        sold_out = product.is_sold_out
    else:
        render_page = 'registration/payment.html'

    return render(request, render_page, {
        'title': _('Registration'),
        'form': form,
        'uid': uid,
        'product_name': product.name,
        'has_conference_ticket': has_conference_ticket,
        'option_id': int(option_id),
        'sold_out': sold_out,
        'amount': product.price,
    })


@staff_member_required
def registrations(request, option_id):
    option = Option.objects.get(id=option_id)
    registrations = Registration.objects.filter(option=option, payment_status__in=['paid'])

    return render(request, 'registration/registration_list.html', {
        'title': '티켓 구매자 명단',
        'option': option,
        'registrations': registrations
    })


@staff_member_required
def checkins(request, proposal_id):
    sprint = SprintProposal.objects.get(id=proposal_id)
    checkins = SprintCheckin.objects.filter(sprint=sprint)

    return render(request, 'registration/checkin_list.html', {
        'title': '참가자 명단',
        'sprint': sprint,
        'checkins': checkins
    })


@login_required
def payment_process(request):
    # 비정상적 접근으로 등록 메인 페이지로 이동합니다.
    if request.method == 'GET':
        return redirect('registration_index')

    payment_logger.debug(request.POST)

    try:
        product = Option.objects.get(id=request.POST.get('option'))
    except Option.DoesNotExist:
        return redirect('registration_index')

    if product.has_additional_price:
        form = RegistrationAdditionalPriceForm(request.POST)
    elif product.event_type != EVENT_CONFERENCE:
        form = RegistrationFormWithoutTopSize(request.POST)
    else:
        form = RegistrationForm(request.POST)

    # TODO : more form validation
    # eg) merchant_uid
    if not form.is_valid():
        form_errors_string = "\n".join(('%s:%s' % (k, v[0]) for k, v in form.errors.items()))
        return JsonResponse({
            'success': False,
            'message': form_errors_string,
        })

    cleaned_form = form.cleaned_data

    if product.event_type == EVENT_CONFERENCE:
        # 이미 등록된 사용자로 등록 현황 페이지로 이동합니다.
        registration = Registration.objects.active_conference().filter(user=request.user,
                                                                       payment_status__in=['paid', 'ready'])
        if registration.exists():
            return _redirect_registered(registration.option)

        # 후원 추가 금액이 0원 미만일 때
        if form.cleaned_data.get('additional_price', 0) < 0:
            return JsonResponse({
                'success': False,
                'message': u'후원 금액은 0원 이상이어야 합니다.',
            })

        remain_ticket_count = (
                config.TOTAL_TICKET - Registration.objects.active_conference().filter(
            payment_status__in=['paid', 'ready']).count())
    elif product.event_type == EVENT_YOUNG:
        registration_query = Registration.objects.filter(option=product, payment_status__in=['paid', 'ready'])
        remain_ticket_count = (product.total - registration_query.filter(payment_status__in=['paid', 'ready']).count())
    else:
        registration_query = Registration.objects.filter(option=product, payment_status__in=['paid', 'ready'])
        registration = registration_query.filter(user=request.user)
        if registration.exists():
            return _redirect_registered(registration.option)

        remain_ticket_count = (product.total - registration_query.filter(payment_status__in=['paid', 'ready']).count())

    # 매진 상태
    if remain_ticket_count <= 0:
        return JsonResponse({
            'success': False,
            'message': '티켓이 매진 되었습니다',
        })

    registration = Registration(
        user=request.user,
        email=request.user.email,
        merchant_uid=request.POST.get('merchant_uid'),
        name=cleaned_form.get('name'),
        additional_price=cleaned_form.get('additional_price', 0),
        company=cleaned_form.get('company', ''),
        top_size=cleaned_form.get('top_size', ''),
        phone_number=cleaned_form.get('phone_number', ''),
        option=cleaned_form.get('option'),
        payment_method=cleaned_form.get('payment_method')
    )

    # 다시 한 번 매진 확인
    if registration.option.is_sold_out:
        return JsonResponse({
            'success': False,
            'message': '{name} 티켓이 매진 되었습니다'.format(name=registration.option.name),
        })

    try:
        product = registration.option
        post_data = request.POST

        # 한국인용 카드 결제일 때
        if registration.payment_method == 'card-korean':
            iamport = Iamport(config.IMP_DOM_API_KEY, config.IMP_DOM_API_SECRET)

            # TODO : use validated and cleaned data
            iamport_params = dict(
                name=product.name,
                amount=product.price + registration.additional_price,
                token=post_data.get('token'),
                merchant_uid=post_data.get('merchant_uid'),
                card_number=post_data.get('card_number'),
                expiry=post_data.get('expiry'),
                birth=post_data.get('birth'),
                pwd_2digit=post_data.get('pwd_2digit'),
                vat=0,
                buyer_name=post_data.get('name'),
                buyer_email=post_data.get('email'),
                buyer_tel=post_data.get('phone_number')
            )

            iamport.pay_onetime(**iamport_params)

            confirm = iamport.find_by_merchant_uid(post_data.get('merchant_uid'))

            # 결제한 금액과 Form에 입력된 결제 금액들이 다를 때
            if confirm['amount'] != product.price + registration.additional_price:
                # TODO : 결제 취소하는 로직 있어야 함
                return render_io_error("amount is not same as product.price. it will be canceled")

            registration.transaction_code = confirm.get('pg_tid')
            registration.payment_method = confirm.get('pay_method')
            registration.payment_status = confirm.get('status')
            registration.payment_message = confirm.get('fail_reason')
            registration.vbank_name = confirm.get('vbank_name', None)
            registration.vbank_num = confirm.get('vbank_num', None)
            registration.vbank_date = confirm.get('vbank_date', None)
            registration.vbank_holder = confirm.get('vbank_holder', None)
            registration.save()

        elif registration.payment_method == 'card-foreign':
            iamport = Iamport(config.IMP_INTL_API_KEY, config.IMP_INTL_API_SECRET)

            # TODO : use validated and cleaned data
            iamport_params = dict(
                name=product.name,
                amount=product.price + registration.additional_price,
                token=post_data.get('token'),
                merchant_uid=post_data.get('merchant_uid'),
                card_number=post_data.get('card_number'),
                expiry=post_data.get('expiry'),
                birth=post_data.get('birth'),
                pwd_2digit=post_data.get('pwd_2digit'),
                vat=0,
                buyer_name=post_data.get('name'),
                buyer_email=post_data.get('email'),
                buyer_tel=post_data.get('phone_number')
            )
            iamport.pay_foreign(**iamport_params)

            confirm = iamport.find_by_merchant_uid(post_data.get('merchant_uid'))

            # 결제한 금액과 Form에 입력된 결제 금액들이 다를 때
            if confirm['amount'] != product.price + registration.additional_price:
                # TODO : 결제 취소하는 로직 있어야 함
                return render_io_error("amount is not same as product.price. it will be canceled")

            registration.transaction_code = confirm.get('pg_tid')
            registration.payment_method = confirm.get('pay_method')
            registration.payment_status = confirm.get('status')
            registration.payment_message = confirm.get('fail_reason')
            registration.vbank_name = confirm.get('vbank_name', None)
            registration.vbank_num = confirm.get('vbank_num', None)
            registration.vbank_date = confirm.get('vbank_date', None)
            registration.vbank_holder = confirm.get('vbank_holder', None)
            registration.save()

        elif registration.payment_method == 'vbank':
            registration.transaction_code = post_data.get('pg_tid')
            registration.payment_method = post_data.get('pay_method')
            registration.payment_status = post_data.get('status')
            registration.payment_message = post_data.get('fail_reason')
            registration.vbank_name = post_data.get('vbank_name', None)
            registration.vbank_num = post_data.get('vbank_num', None)
            registration.vbank_date = post_data.get('vbank_date', None)
            registration.vbank_holder = post_data.get('vbank_holder', None)
            registration.save()

        else:
            raise Exception('Unknown payment method')

    except Exception as e:
        # TODO : other status code
        return JsonResponse({
            'success': False,
            'code': e.code,
            'message': e.message,
        })
    else:
        return JsonResponse({
            'success': True,
        })


@csrf_exempt
def payment_callback(request):
    merchant_uid = request.POST.get('merchant_uid')
    registration = Registration.objects.filter(merchant_uid=merchant_uid)

    if not registration.exists():
        return HttpResponse(status=404)

    try:
        iamport = Iamport(config.IMP_DOM_API_KEY, config.IMP_DOM_API_SECRET)
        result = iamport.find_by_merchant_uid(merchant_uid)
        registration = registration.first()

        if result['status'] == 'paid':
            registration.confirmed = datetime.datetime.now()
        elif result['status'] == 'cancelled':
            registration.canceled = datetime.datetime.now()

        registration.payment_status = result['status']
        registration.save()
        return HttpResponse()
    except Iamport.ResponseError as iamport_error:
        if iamport_error.code == 401 or iamport_error.code == 404:
            iamport = Iamport(config.IMP_INTL_API_KEY, config.IMP_INTL_API_SECRET)
            result = iamport.find_by_merchant_uid(merchant_uid)
            registration = registration.first()

            if result['status'] == 'paid':
                registration.confirmed = datetime.datetime.now()
            elif result['status'] == 'cancelled':
                registration.canceled = datetime.datetime.now()

            registration.payment_status = result['status']
            registration.save()
            return HttpResponse()

    return HttpResponse(status=404)


@login_required
def manual_registration(request, manual_payment_id):
    mp = get_object_or_404(ManualPayment, pk=manual_payment_id, user=request.user)
    uid = str(uuid4()).replace('-', '')
    form = ManualPaymentForm(initial={
        'title': mp.title,
        'base_price': mp.price,
        'email': request.user.email,
    })

    return render(request, 'registration/manual_payment.html', {
        'title': _('Registration'),
        'manual_payment_id': manual_payment_id,
        'form': form,
        'uid': uid,
        'product_name': mp.title,
        'amount': mp.price,
        'payment_status': mp.payment_status,
    })


@login_required
def manual_payment_process(request):
    if request.method == 'GET':
        return redirect('registration_index')

    payment_logger.debug(request.POST)
    form = ManualPaymentForm(request.POST)

    if not form.is_valid():
        form_errors_string = "\n".join(('%s:%s' % (k, v[0]) for k, v in form.errors.items()))
        return JsonResponse({
            'success': False,
            'message': form_errors_string,  # TODO : ...
        })

    # check already payment
    try:
        mp = ManualPayment.objects.get(pk=request.POST.get('manual_payment_id'))
    except ManualPayment.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '결제할 내역이 존재하지 않습니다. 다시 한번 확인해 주시기 바랍니다.',
        })

    if mp.payment_status == 'paid':
        return JsonResponse({
            'success': False,
            'message': '이미 지불되었습니다. 문의사항은 support@pycon.kr 로 문의주시기 바랍니다.',
        })

    # Only card
    try:
        imp_client = Iamport(config.IMP_DOM_API_KEY, config.IMP_DOM_API_SECRET)

        imp_params = dict(
            token=request.POST.get('token'),
            merchant_uid=request.POST.get('merchant_uid'),
            amount=mp.price,
            card_number=request.POST.get('card_number'),
            expiry=request.POST.get('expiry'),
            birth=request.POST.get('birth'),
            pwd_2digit=request.POST.get('pwd_2digit'),
            name=mp.title,
            buyer_name=request.POST.get('name', ''),
            buyer_email=request.POST.get('email'),
            buyer_tel=request.POST.get('phone_number', '')
        )

        imp_client.pay_onetime(**imp_params)
        confirm = imp_client.find_by_merchant_uid(request.POST.get('merchant_uid'))

        if confirm['amount'] != mp.price:
            return render_io_error("amount is not same as product.price. it will be canceled")

        mp.transaction_code = confirm.get('pg_tid')
        mp.imp_uid = confirm.get('imp_uid')
        mp.merchant_uid = confirm.get('merchant_uid')
        mp.payment_method = confirm.get('pay_method')
        mp.payment_status = confirm.get('status')
        mp.payment_message = confirm.get('fail_reason')
        mp.confirmed = timezone.now()
        mp.save()
    except IamporterError as e:
        return JsonResponse({
            'success': False,
            'code': e.code,
            'message': e.message,
        })
    else:
        return JsonResponse({
            'success': True,
        })


class RegistrationReceiptDetail(DetailView):
    def get_object(self, queryset=None):
        option_conference = Option.objects.active_conference()
        return get_object_or_404(Registration, option__in=option_conference, payment_status='paid',
                                 user_id=self.request.user.pk)

    def get_context_data(self, **kwargs):
        context = super(RegistrationReceiptDetail, self).get_context_data(**kwargs)
        context['title'] = _("Registration Receipt")
        return context


def group_required(*group_names):
    def in_groups(u):
        if u.is_authenticated():
            if bool(u.groups.filter(name__in=group_names)) or u.is_superuser:
                return True
        return False

    return user_passes_test(in_groups)


@group_required('admin', 'organizer', 'volunteer')
def issue(request):
    registration = Registration.objects.filter(payment_status='paid')

    options = None
    if request.GET.get('type', None) == 'tutorial':
        options = Option.objects.filter(event_type=EVENT_TUTORIAL)

    if request.GET.get('type', None) == 'sponsor':
        options = Option.objects.filter(event_type=EVENT_TUTORIAL)

    if request.GET.get('type', None) is None:
        options = Option.objects.filter(event_type=EVENT_CONFERENCE)

    if options is not None:
        registration = registration.filter(option__in=options)

    context = {
        'registration': registration,
        'title': _("Issue Ticket System"),
    }
    return render(request, 'registration/issue_ticket.html', context)


@group_required('admin', 'organizer', 'volunteer')
def sprint(request):
    checkins = SprintCheckin.objects.all()

    context = {
        'checkins': checkins,
        'title': _("Issue Ticket System"),
    }
    return render(request, 'registration/sprint_checkin.html', context)


@group_required('admin', 'organizer', 'volunteer')
def issue_print(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id)
    name = registration.user.profile.name if registration.user.profile.name != '' \
        else registration.name
    company = registration.user.profile.organization if \
        registration.user.profile.organization != '' else registration.company
    company = '' if company is None else company

    # 개인후원
    personal_patron = True if registration.option.id == 1 else False
    # 발표자
    speaker = True if Speaker.objects.filter(email=registration.user.email).exists() else False
    # 아이돌봄
    options = Option.objects.filter(event_type=EVENT_BABYCARE)
    baby_care = True if Registration.objects.filter(user=registration.user).filter(option__in=options).exists() else False
    # 영코더
    options = Option.objects.filter(event_type=EVENT_YOUNG)
    young_coder = True if Registration.objects.filter(user=registration.user).filter(option__in=options).exists() else False

    if personal_patron or speaker or baby_care or young_coder:
        additional_ticket = {
            'patron': personal_patron,
            'speaker': speaker,
            'baby_care': baby_care,
            'young_coder': young_coder,
        }
    else:
        additional_ticket = None

    context = {
        'name': name,
        'company': company,
        'registration': registration,
        'title': _("Ticket Print"),
        'additional_ticket': additional_ticket,
    }
    return render(request, 'registration/issue_print.html', context)


@group_required('admin', 'organizer', 'volunteer')
def sprint_print(request, checkin_id):
    checkin = get_object_or_404(SprintCheckin, id=checkin_id)
    name = checkin.user.profile.name
    # 수정 필요
    company = checkin.user.profile.organization if checkin.user.profile is not None else '.'
    company = checkin.user.profile.organization if checkin.user.profile.organization is not None else '.'
    dict_map = {1: 'Nekoyume', 2: '니름', 3: 'Hearthstone++', 4: 'pandas', 6: 'Backend.Al'}

    context = {
        'name': name,
        'company': company,
        'sprint_title': dict_map[checkin.sprint.id],
        'title': _("Sprint Print"),
    }
    return render(request, 'registration/sprint_print.html', context)


@group_required('admin', 'organizer', 'volunteer')
@require_http_methods(["POST"])
def issue_submit(request):
    user_data = IssueSubmitForm(request.POST)

    if not user_data.is_valid():
        return HttpResponseBadRequest('invalid form value')

    user_id = user_data.cleaned_data['user_id']
    registration = Registration.objects.get(payment_status='paid',
                                            id=user_id)
    issue = IssueTicket(
        registration=registration,
        issuer=request.user
    ).save()

    return JsonResponse({
        'success': True,
        'message': u'발권완료',
    })
