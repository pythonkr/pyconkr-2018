// TODO : i18n
var payment = {
    config: {},
    setConfig: function (config) {
        this.config = config;
    },
    handleResponse: function (response) {
        var payment = this;
        var $additionalPrice = $('#id_additional_price');

        response['csrfmiddlewaretoken'] = payment.config.csrf_token;
        response['name'] = $('#id_name').val();
        response['email'] = $('#id_email').val();
        response['base_price'] = parseInt(this.config.amount);
        response['additional_price'] = parseInt($additionalPrice.val()) ? parseInt($additionalPrice.val()) : 0;
        response['company'] = $('#id_company').val();
        response['top_size'] = $('#id_top_size').val();
        response['phone_number'] = $('#id_phone_number').val();
        response['payment_method'] = $('#id_payment_method').val();
        response['option'] = $('#id_option').val();

        $.ajax({
            method: 'POST',
            url: payment.config.payment_url,
            data: response,
            dataType: 'json'
        }).done(function (result) {
            if (!result.success) {
                alert('결제에 실패했습니다. ' + result.code + ' ' + result.message);
                window.location.reload();
                return;
            }
            alert('결제가 완료되었습니다.');
            window.location.href = payment.config.status_url;
        }.bind(this)).fail(function (xhr, status, error) {
            alert('결제에 실패했습니다. 다시 시도해 주세요.' + error);
            window.location.reload();
        }.bind(this));
    },
    iamportCard: function (initCode, uid, amount) {
        var payment = this;

        IMP.SBCR.init(initCode);
        IMP.SBCR.onetime({
            merchant_uid: uid,
            amount: amount,
            vat: 0
        }, function (response) {
            if (!response.token) {
                alert(response.message);
                return false;
            }
            payment.handleResponse(response);
        }.bind(this));
    },
    init: function (config) {
        this.setConfig(config);
        var payment = this;

        $('#submit-id-submit').attr('disabled', false);
        $('#registration-form').submit(function (e) {
            e.preventDefault();
            var $additionalPrice = $('#id_additional_price');
            var additionalPrice = parseInt($additionalPrice.val()) ? parseInt($additionalPrice.val()) : 0;
            var paymentMethod = $('#id_payment_method').val();
            var totalPrice = parseInt(payment.config.amount) + additionalPrice;

            if (paymentMethod === 'card-korean') {
                payment.iamportCard(payment.config.IMP_DOM_USER_CODE, payment.config.uid,  totalPrice);
            } else if (paymentMethod === 'card-foreign') {
                payment.iamportCard(payment.config.IMP_INTL_USER_CODE, payment.config.uid,  totalPrice);
            } else if (paymentMethod === 'vbank') {
                IMP.init(payment.config.IMP_DOM_USER_CODE);
                IMP.request_pay({
                    pg: 'nice',
                    pay_method: 'vbank',
                    merchant_uid: payment.config.uid,
                    name: $('#id_option').val(),
                    amount: totalPrice,
                    buyer_email: $('#id_email').val(),
                    buyer_name: $('#id_name').val(),
                    buyer_tel: $('#id_phone_number').val(),
                    buyer_addr: '',
                    buyer_postcode: ''
                }, function (rsp) {
                    if (rsp.success) {
                        payment.handleResponse(rsp);
                    } else {
                        var msg = '결제에 실패하였습니다.';
                        msg += '에러내용 : ' + rsp.error_msg;
                        alert(msg);
                    }
                });
            } else {
                // ?????
            }
        });
    }
};
