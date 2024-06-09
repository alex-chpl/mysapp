
function selnav(){
    let el = $(this);
    $('article').hide();
    $("nav li.active").removeClass("active");
    el.addClass("active");
    let adt = el.find('a')[0],
	dt = adt.dataset['name'];
    dhref = adt.dataset['html'];
    if ($('#'+dt).length > 0){
        //if (dhref){
        //    $.get(dhref,function(d){$('#'+dt).html(d)});
        //};
	    $('#'+dt).show();
    }else{
	$('main').append($('<article id="'+dt+'"></article>')
			 .html('<h2>Страница '+dt+'</h2>'));
    };
    if (dhref){ //setTimeout(function(){
	$.get(dhref).then(d => $('#'+dt).html(d))
    }//,1000)};
}

$(function(){
    $('nav ul li').on('click',selnav);
    $('nav ul:first-child li:first-child').trigger('click')
})
