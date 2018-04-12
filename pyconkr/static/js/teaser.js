$(document).ready(function(){
  var mapOptions = {
    center: new naver.maps.LatLng(37.5117731, 127.0592041),
    zoom: 10,
    zoomControl: true
  };

  var map = new naver.maps.Map('map', mapOptions);

  var marker = new naver.maps.Marker({
    position: new naver.maps.LatLng(37.5117731, 127.0592041),
    map: map
  });

  var Slickconfig = {
    dots: true,
    prevArrow: false,
    nextArrow: false,
    autoplay: true,
    autoplaySpeed: 5000
  };

  $('.js_slick').slick(Slickconfig);
});