$(document).ready(function(){
/********************************************************************************************************/

$("#date").val(new Date().toJSON().slice(0,10));



var stickyNavTop = $('.navbar-static-top').offset().top;  
  
var stickyNav = function(){  
var scrollTop = $(window).scrollTop();  
       
if (scrollTop > stickyNavTop) {   
//    $('.navbar-static-top').fadeOut(1000).stop();
	    $('.navbar-static-top').addClass('navbar-fixed-top');
} else {  
    $('.navbar-fixed-top').removeClass('navbar-fixed-top');   
}  
};  
  
stickyNav();  
  
$(window).scroll(function() {  
    stickyNav();  
});


$('.dropdown-menu li input, .dropdown-menu li label, .dropdown-menu li span, .dropdown-menu select').click(function(e) {
	e.stopPropagation();
});



/*
 *__________________________________________NOTIFICATION SCRIPTS_____________________________
 */ 
  		$("ul.notification-list li").click(function(){
	  		var indis = $(this).index() + 1;
	  		$(this).find('div.notification-row').slideDown();
  		}); 
  		
  		
	  	$(document).on("click", ".notificationStatusBtn", function(){
  		var id = $(this).parent().find("span").text();
		var operation = 'notification-readStatus';
		var value = 'id=' + id + '&readStatus=True'
  		var objRow = $(this).parent().parent();
// 		var objLine = $(this).parent().parent().parent();

		
		$.ajax({
			url: "./ajax/ajax.php",	
			type: "POST",
			data: value + "&operation=" + operation,
			dataType: "json",
			success: function(answer)
				{
					if(answer.errors)
						{	
						}
					else
						
						{
							$(objRow).slideUp();
							$(objRow).parent().fadeOut(500);
							var count = $("span.badge-notification").text();
							count--;
							if (count == 0){
								window.location.href= "notifications.php";
							}else{
								$("span.badge-notification").text(count);
							}
						}
				},
				error: function(a,b,c){
					alert(b,c);
				}
			})		  		
	  	});
  		
  		
/*
 *____________________________________________________________________________________________
 */


/*
 *_________________________________TICKET Scripts_______________________________________________
 */

 	$("#category").click(function(){

	 	$("#conditionBtn").html('Category <span class="caret"></span>');
	 	var orderSentence = $.trim($("#orderBtn").text());
	 	var orderBy = (orderSentence == "Updated Date") ? "modified_on" : "submitted_on";
	 	var sortBy = '';
	 	if ($("#ascBtn").hasClass("btn-danger")){
		 	sortBy = "SORT_ASC";
	 	}else{
		 	sortBy = "SORT_DESC";
	 	}
	 	$(location).attr('href', 'ticket.php?' + 'condition=category&condition_value=Facilities&orderBy=' + orderBy + '&sortBy=' + sortBy);	 	

	 	
 	});
 	
 	$("#assigned").click(function(){
 	
	 	$("#conditionBtn").html('Assigned to <span class="caret"></span>');
	 	var orderSentence = $.trim($("#orderBtn").text());
	 	var orderBy = (orderSentence == "Updated Date") ? "modified_on" : "submitted_on";
	 	if ($("#ascBtn").hasClass("btn-danger")){
		 	sortBy = "SORT_ASC";
	 	}else{
		 	sortBy = "SORT_DESC";
	 	}
	 	$(location).attr('href', 'ticket.php?' + 'condition=assigned_to&condition_value=cmscompinfrasup-facilities&orderBy=' + orderBy + '&sortBy=' + sortBy);	 	
	 	
 	});


 	$("#updatedBtn").click(function(){

	 	$("#orderBtn").html('Updated Date <span class="caret"></span>');
	 	var conditionBtn = $.trim($("#conditionBtn").text());
	 	var orderSentence = (conditionBtn == "Category") ? "condition=category&condition_value=Facilities" : 																						    			   "condition=assigned_to&condition_value=cmscompinfrasup-facilities";
	 	if ($("#ascBtn").hasClass("btn-danger")){
		 	sortBy = "SORT_ASC";
	 	}else{
		 	sortBy = "SORT_DESC";
	 	}
	 	$(location).attr('href', 'ticket.php?' + orderSentence + '&orderBy=modified_on' + '&sortBy=' + sortBy);	 	
	 	
 	});
 	
 	$("#createdBtn").click(function(){
 	
	 	$("#orderBtn").html('Created Date <span class="caret"></span>');
	 	var conditionBtn = $.trim($("#conditionBtn").text());
	 	var orderSentence = (conditionBtn == "Category") ? "condition=category&condition_value=Facilities" : 																										   "condition=assigned_to&condition_value=cmscompinfrasup-facilities";
	 	if ($("#ascBtn").hasClass("btn-danger")){
		 	sortBy = "SORT_ASC";
	 	}else{
		 	sortBy = "SORT_DESC";
	 	}

	 	$(location).attr('href', 'ticket.php?' + orderSentence + '&orderBy=submitted_on' + '&sortBy=' + sortBy); 	
	 	
 	});


 	$("#descBtn").click(function(){

	 	var conditionBtn = $.trim($("#conditionBtn").text());
//	 	var orderSentence = (conditionBtn == "Category") ? "condition=category&condition_value=Facilities" : 																						    			   "condition=assigned_to&condition_value=cmscompinfrasup-facilities";
		var querySentence = $("#querySentence").text();
		querySentence = querySentence.replace('&sortBy=SORT_DESC', '');
		querySentence = querySentence.replace('&sortBy=SORT_ASC', '');
	 	$(location).attr('href', 'ticket.php?' + querySentence  + '&sortBy=SORT_DESC');	 	
	 	
 	});

 	$("#ascBtn").click(function(){

	 	var conditionBtn = $.trim($("#conditionBtn").text());
//	 	var orderSentence = (conditionBtn == "Category") ? "condition=category&condition_value=Facilities" : 																						    			   "condition=assigned_to&condition_value=cmscompinfrasup-facilities";
		var querySentence = $("#querySentence").text();
		querySentence = querySentence.replace('&sortBy=SORT_DESC', '');
		querySentence = querySentence.replace('&sortBy=SORT_ASC', '');
	 	$(location).attr('href', 'ticket.php?' + querySentence + '&sortBy=SORT_ASC');	 	
	 	
 	});




/*
 *______________________________________________________________________________________________
 */

/*
 ** ******* startDate and endDate ************************************************************
 */
	$("#startDate" ).datepicker({dateFormat: 'yy-mm-dd'});//"option" , "width" , 100);
	$("#endDate" ).datepicker({dateFormat: 'yy-mm-dd', maxDate: '0'});//"option" , "width" , 100);
	

/*	$(".btnstartDate" ).datepicker({dateFormat: 'yy-mm-dd'});//"option" , "width" , 100);
	$(".btnendDate" ).datepicker({dateFormat: 'yy-mm-dd', maxDate: '0'});//"option" , "width" , 100);
*/

	$("#startDate").val(new Date().toJSON().slice(0,10));
	$("#endDate").val(new Date().toJSON().slice(0,10));

	var date = moment().add('days',-7).format().substring(0, 10);
	$(".btnstartDate").val(date);
	$(".btnendDate").val(new Date().toJSON().slice(0,10));

	$("#startDate").datepicker("setDate" , "-7");
	$("#startDateGroup").hide();
	$("#endDateGroup").hide();
/********************************************************************************************************/
	
	$("#divCheckbox").hide();
	$("#chartType").change(function(){
	var value = $(this).val().toLowerCase();
		if (value == 'pie'){
			$("#divCheckbox").hide();
		}else{
			$("#divCheckbox").show();}
	});

	$("#chartTypeStat").change(function(){
	var value = $(this).val().toLowerCase();
		if (value == 'pie'){
			$("#divCheckbox").hide();
		}else{
			$("#divCheckbox").show();}
	});
	
	$("#timePeriod").change(function(){
		
		var value = $(this).val();
		if(value == '24h'){
			$("#startDate").datepicker("setDate" , "-1");
			$("#startDateGroup").hide();
			$("#endDateGroup").hide();
		}
		
		if(value == '48h'){
			$("#startDate").datepicker("setDate" , "-2");
			$("#startDateGroup").hide();
			$("#endDateGroup").hide();
			
		}

		if(value == 'Lweek'){
			$("#startDate").datepicker("setDate" , "-7");
			$("#startDateGroup").hide();
			$("#endDateGroup").hide();

		}

		if(value == 'L2week'){
			$("#startDate").datepicker("setDate" , "-15");
			$("#startDateGroup").hide();
			$("#endDateGroup").hide();

		}
		
		if(value == 'Lmonth'){
			$("#startDate").datepicker("setDate" , "-30");
			$("#startDateGroup").hide();
			$("#endDateGroup").hide();

		}

		if(value == 'L2months'){
			$("#startDate").datepicker("setDate" , "-61");
			$("#startDateGroup").hide();
			$("#endDateGroup").hide();

		}

		if(value == 'L3months'){
			$("#startDate").datepicker("setDate" , "-91");
			$("#startDateGroup").hide();
			$("#endDateGroup").hide();

		}

		if(value == 'custom'){
			$("#startDateGroup").show();
			$("#endDateGroup").show();
		}

	});
	
/************************************Fill Sites in Combobox*********************************************************/	
	$.get('data/links.txt', function(data) {
            var lines = data.split("\n");
            $.each(lines, function(n, elem) {
                $('#goodT2fT1').append('<option value="' + elem + '">' + elem + '</option>');
                $('#goodT2tT1').append('<option value="' + elem + '">' + elem + '</option>');
  
            });
        });
/********************************************************************************************************/

/************************************Fill Sites in Combobox*********************************************************/	
	$.get('data/hcerrors.txt', function(data) {
            var lines = data.split("\n");
            $.each(lines, function(n, elem) {
                $('#hcexitcode').append('<option value="' + elem + '">' + elem + '</option>');
            });
        });


/************************************Fill Links in Combobox*********************************************************/	
	$.get('data/sites.txt', function(data) {
            var lines = data.split("\n");
            $.each(lines, function(n, elem) {
                $('#siteName').append('<option value="' + elem + '">' + elem + '</option>');
  
            });
        });
/********************************************************************************************************/

var count = 0;
$('.findSiteText').keyup(function(event) {
		var id = $(this).attr('id');
		var delta = id.length - 9;
		var chartName = id.substr(0, delta);
		var search_text = $("#" + id).val();
		var rg = new RegExp(search_text,'i');
		$("#" + chartName + "SiteList" + " ." + chartName + "SiteListItems").each(function(){
 			if($.trim($(this).html()).search(rg) == -1) {
 				$(this).css('display', 'none');
			}	
			else {
				$(this).css('display', 'block');
			}
		});
	});

/********************************************************************************************************/



$("#saveWeeklyBtn").click(function(){
var operation = 'saveweekly';
$.ajax({
	url: "./ajax/ajax.php",
	data: "operation=" + operation,
	type: "POST",
	dataType: "JSON",
	success: function(answer){
		if(answer.errors)
			{
				$(".alert-danger").html(answer.errors).fadeIn(500);
				$(".alert-danger").html(answer.errors).fadeOut(2000);	

			}
		else
			{
				alert(answer.ok);
				$(".alert-success").html(answer.ok).fadeIn(500);
				$(".alert-success").html(answer.ok).fadeOut(2000);	
			}
	},
	error: function(XMLHttpRequest, textStatus, errorThrown) { 
                    alert("Status: " + textStatus); alert("Error: " + errorThrown); 
                }     	
	});
});



/************************************Select All Button Code*********************************************/

function SelectText(element) {
    var doc = document
        , text = doc.getElementById(element)
        , range, selection
    ;    
    if (doc.body.createTextRange) {
        range = document.body.createTextRange();
        range.moveToElementText(text);
        range.select();
    } else if (window.getSelection) {
        selection = window.getSelection();        
        range = document.createRange();
        range.selectNodeContents(text);
        selection.removeAllRanges();
        selection.addRange(range);
    }
}

$(function() {
    $('#twikicodeSelect').click(function() {
        SelectText('twikicoderesult');
    });
});

$("#twikiFileMorgue").click(function(){
	
	$.ajax({  
			type: "GET",
			data: "operation=saveTwiki&section=morgue",
			url: "./ajax/ajax.php",             
			dataType: "JSON",                
			success: function(response){                    
			   alert("File was saved."); 
			},
			error: function(a,b,c){
				alert(b);
			},
	    });
	
});


$("#twikiFileWr").click(function(){
	$.ajax({  
			type: "POST",
			data: "operation=saveTwiki",
			url: "./ajax/ajax.php",             
			dataType: "JSON",                
			success: function(response){                    
			   alert("File was saved."); 
			},
			error: function(a,b,c){
				alert(b);
			},
	    });
	
});


/*************************************EMPTY WAITING ROOM LIST********************************************/

var liste = $(".waitingRoomList a").size();

if (liste == 0)
	{
		$('.waitingRoomList').append('<a href="#" id="noRecord" class="list-group-item">There is no any site in WaitingRoom &nbsp; <b class="btn btn-success btn-sm">Add New Site</b> </a>');

	}
/********************************************************************************************************/

/*****************************************GET WAITINGROOM LIST FROM DB***********************************/

$.gethcrecords = function(id){
$.ajax({    //create an ajax request to load_page.php
		type: "GET",
		data: "idWr=" + id + "&operation=hc",
		url: "./ajax/ajax_read.php",             
		dataType: "html",   //expect html to be returned                
		success: function(response){                    
		    $("#hcList").html(response); 
		}

    });

};


$.getsamrecords = function(id){
$.ajax({    //create an ajax request to load_page.php
		type: "GET",
		data: "idWr=" + id + "&operation=sam",
		url: "./ajax/ajax_read.php",             
		dataType: "html",   //expect html to be returned                
		success: function(response){                    
		    $("#samList").html(response); 
		}

    });


};


$.getlinksrecords = function(id){
$.ajax({    //create an ajax request to load_page.php
		type: "GET",
		data: "idWr=" + id + "&operation=links",
		url: "./ajax/ajax_read.php",             
		dataType: "html",   //expect html to be returned                
		success: function(response){                    
		    $("#linksList").html(response); 
		}

    });


};

//****************************************************************************************************************

$.getRecord = function(id){
	$("#siteerror-panel").fadeIn(500);
	$("div#wrId").html(id);
	$.gethcrecords(id);
	$.getsamrecords(id);
	$.getlinksrecords(id);
	$('#siteSaveBtn').attr('disabled' , 'disabled');
	var	nesne = $("#siteErrorPanel").offset();
	var	ust = nesne.top - 30;
	$('html,body').animate({scrollTop: ust}, 500);

};

$(document).on("click", "div#waitingRoomList a", function(){
//$("div#waitingRoomList a").on("click" ,function(){
	var indis = $(this).index();
	var idWR = $("div#waitingRoomList a span.waitingRoomListItem:eq(" + indis + ")").html();
	$.getRecord(idWR);	
});

/********************************************************************************************************/

/************************************Read Form and Sent Data ajax.php************************************/	
$.cleanForm = function(){
	$("#date").val(new Date().toJSON().slice(0,10));
	$("#siteName").val('');
	$("#ticketNumber").val('');
	$("#ticketUrl").val('');
};



/*
 *  **********************save JSON code to txt file ****************************
 */ 
 
 $.saveJSON = function(data){
    var fileName = "site(s)Information";
    var uri = 'data:txt/csv;charset=utf-8,' + data;
    var link = document.createElement("a");    
    link.href = uri;
    link.style = "visibility:hidden";
	link.download = fileName + ".txt";
    document.body.appendChild(link);
    link.click();
	document.body.removeChild(link);
} 

 
/*
 ********************************************************************************
 */


$.kayitlar = function(data, chartName, valueField){

var obj = data;
var lang = '';
var count = 0;
var str = '';
switch(valueField){
	case "Days":
		str = " day(s)";
		break;
	case "average":
		str = "%";
		break;
	case "number":
		str = " Number";
		break;
}
var percentage_value = 0;
  $.each(obj, function() {
	    percentage_value = 0;
  		percentage_value = (valueField == "average") ? percentage_value = Math.ceil(this[valueField]) : this[valueField];
  		lang += '<a class="list-group-item ' + chartName + 'SiteListItems SiteListItems">' + this['siteName'] +  '<span class="badge">' + percentage_value + str + '</span></a>';
  		count++;
  });
  
  
  $("#" + chartName + "SiteList").html(lang);
$("#" + chartName + "ListSum").html("Total <span class='spanSiteCount' id ='" + chartName + "SiteCount'>" + count + "</span> Sites").show();
$("#" + chartName + "EndDate").html($("#endDate").val());
$("#" + chartName + "StartDate").html($("#startDate").val());
$("#" + chartName +"ListHead").show();
$("#" + chartName + "JsonSaveBtn span").text(JSON.stringify(data));
$("#" + chartName + "JsonCode").text(JSON.stringify(data));

};


$.abc = function(chartNameOne, chartNameTwo, chartNameThree){
	var data = $("#queryFormStat").serialize();
//	var chartType = $("#chartTypeStat").val().toLowerCase();
	var chartType = "bar";
	var chartRotate = "true";	
	var startDate = $("#startDate").val();
	var endDate = $("#endDate").val();
	var errorSelect = $("#errorSelect").val();
//	if ($('#chartRotate').is(":checked")) {chartRotate = 'true'} else {chartRotate = 'false'};
	if (chartType == 'pie') {chartRotate = 'false'}; 

	$.ajaxSetup({
		type : "POST",
		dataType : "JSON",
		url : "./ajax/ajaxfonk.php"
	}); 


	$.ajax({
		data: data + "&metric=&colorName=&DB=SAM&tier=",
		success: function(answer){
			makeChart(answer, chartType, chartRotate, "number" , chartNameOne + "Chart");
			$.kayitlar(answer, chartNameOne , "number");
			$("#" + chartNameOne + "SubheadLine").text("Sam Tests");
			$("#" + chartNameOne + "SubheadLineDate").text(startDate + " / " + endDate);
			
		},
		error: function(a,b,c){
			alert(b + "-" + c);
		}
	});



	$.ajax({
		data: data + "&metric=&colorName=&DB=HC&tier=",
		success: function(answer){
			makeChart(answer, chartType, chartRotate, "number" , chartNameTwo + "Chart");
			$.kayitlar(answer, chartNameTwo , "number");
			$("#" + chartNameTwo + "SubheadLine").text("Hc Test");
			$("#" + chartNameTwo + "SubheadLineDate").text(startDate + " / " + endDate);
			
			
		},
		error: function(){
//			alert("Error:8080");
		}
	});


$.ajax({
		data: data + "&metric=&colorName=&DB=links&tier=",
		success: function(answer){
			makeChart(answer, chartType, chartRotate, "number" , chartNameThree + "Chart", 'links');
			$.kayitlar(answer, chartNameThree , "number");
			$("#" + chartNameThree + "SubheadLine").text("Links");
			$("#" + chartNameThree + "SubheadLineDate").text(startDate + " / " + endDate);
		},
		error: function(){
//			alert("Error:8080");
		}
	});


	switch(errorSelect){
		case 'S' : 
			{
				$("#" + chartNameOne + "Chart").show(); 
				$("#" + chartNameOne + "SubheadLine").parent().show();
				$("#" + chartNameOne + "SubheadLineDate").show();
				$("#" + chartNameOne + "CsvSaveBtn").show();
				$("#" + chartNameOne + "JsonSaveBtn").show();
				$("#" + chartNameOne + "ChartTypeBtnGroup").show();
				$("#" + chartNameOne + "ChartRotateBtnGroup").show();
				$("#" + chartNameOne + "charDateBtn").show();
				$("#" + chartNameOne + "chartqueryBtn").show();
				
				$("#" + chartNameTwo + "Chart").hide(); 
				$("#" + chartNameTwo + "SubheadLine").parent().hide();
				$("#" + chartNameTwo + "SubheadLineDate").hide();
				$("#" + chartNameTwo + "CsvSaveBtn").hide();
				$("#" + chartNameTwo + "JsonSaveBtn").hide();
				$("#" + chartNameTwo + "ChartTypeBtnGroup").hide();
				$("#" + chartNameTwo + "ChartRotateBtnGroup").hide();
				$("#" + chartNameTwo + "charDateBtn").hide();
				$("#" + chartNameTwo + "chartqueryBtn").hide();
				


				$("#" + chartNameThree + "Chart").hide();
				$("#" + chartNameThree + "SubheadLine").parent().hide();
				$("#" + chartNameThree + "SubheadLineDate").hide();
				$("#" + chartNameThree + "CsvSaveBtn").hide();
				$("#" + chartNameThree + "JsonSaveBtn").hide();
				$("#" + chartNameThree + "ChartTypeBtnGroup").hide();
				$("#" + chartNameThree + "ChartRotateBtnGroup").hide();
				$("#" + chartNameThree + "charDateBtn").hide();
				$("#" + chartNameThree + "charqueryBtn").hide();
				
				break;
			};

		case 'H' : 
			{
			
				$("#" + chartNameOne + "Chart").hide(); 
				$("#" + chartNameOne + "SubheadLine").parent().hide();
				$("#" + chartNameOne + "SubheadLineDate").hide();
				$("#" + chartNameOne + "CsvSaveBtn").hide();
				$("#" + chartNameOne + "JsonSaveBtn").hide();
				$("#" + chartNameOne + "ChartTypeBtnGroup").hide();
				$("#" + chartNameOne + "ChartRotateBtnGroup").hide();
				$("#" + chartNameOne + "charDateBtn").hide();
				$("#" + chartNameOne + "chartqueryBtn").hide();
				
				
				

				$("#" + chartNameTwo + "Chart").show(); 
				$("#" + chartNameTwo + "SubheadLine").parent().show();
				$("#" + chartNameTwo + "SubheadLineDate").show();
				$("#" + chartNameTwo + "CsvSaveBtn").show();
				$("#" + chartNameTwo + "JsonSaveBtn").show();
				$("#" + chartNameTwo + "ChartTypeBtnGroup").show();
				$("#" + chartNameTwo + "ChartRotateBtnGroup").show();				
				$("#" + chartNameTwo + "charDateBtn").show();
				$("#" + chartNameTwo + "chartqueryBtn").show();
				
				


				$("#" + chartNameThree + "Chart").hide();
				$("#" + chartNameThree + "SubheadLine").parent().hide();
				$("#" + chartNameThree + "SubheadLineDate").hide();
				$("#" + chartNameThree + "CsvSaveBtn").hide();
				$("#" + chartNameThree + "JsonSaveBtn").hide();
				$("#" + chartNameThree + "ChartTypeBtnGroup").hide();
				$("#" + chartNameThree + "ChartRotateBtnGroup").hide();
				$("#" + chartNameThree + "charDateBtn").hide();
				$("#" + chartNameThree + "chartqueryBtn").hide();
				break;
			};

		case 'L' : 
			{
				$("#" + chartNameOne + "Chart").hide(); 
				$("#" + chartNameOne + "SubheadLine").parent().hide();
				$("#" + chartNameOne + "SubheadLineDate").hide();
				$("#" + chartNameOne + "CsvSaveBtn").hide();
				$("#" + chartNameOne + "JsonSaveBtn").hide();
				$("#" + chartNameOne + "ChartTypeBtnGroup").hide();
				$("#" + chartNameOne + "ChartRotateBtnGroup").hide();
				$("#" + chartNameOne + "charDateBtn").hide();
				$("#" + chartNameOne + "chartqueryBtn").hide();


				$("#" + chartNameTwo + "Chart").hide();
				$("#" + chartNameTwo + "SubheadLine").parent().hide();
				$("#" + chartNameTwo + "SubheadLineDate").hide();
				$("#" + chartNameTwo + "CsvSaveBtn").hide();
				$("#" + chartNameTwo + "JsonSaveBtn").hide();
				$("#" + chartNameTwo + "ChartTypeBtnGroup").hide();
				$("#" + chartNameTwo + "ChartRotateBtnGroup").hide();
				$("#" + chartNameTwo + "charDateBtn").hide();
				$("#" + chartNameTwo + "chartqueryBtn").hide();

				
				$("#" + chartNameThree + "Chart").show();
				$("#" + chartNameThree + "SubheadLine").parent().show();
				$("#" + chartNameThree + "SubheadLineDate").show();
				$("#" + chartNameThree + "CsvSaveBtn").show();
				$("#" + chartNameThree + "JsonSaveBtn").show();
				$("#" + chartNameThree + "ChartTypeBtnGroup").show();
				$("#" + chartNameThree + "ChartRotateBtnGroup").show();					
				$("#" + chartNameThree + "charDateBtn").show();
				$("#" + chartNameThree + "chartqueryBtn").show();
								
				break;
			}

		case 'HS' : 
			{
			
				$("#" + chartNameOne + "Chart").show(); 
				$("#" + chartNameOne + "SubheadLine").parent().show();
				$("#" + chartNameOne + "SubheadLineDate").show();
				$("#" + chartNameOne + "CsvSaveBtn").show();
				$("#" + chartNameOne + "JsonSaveBtn").show();
				$("#" + chartNameOne + "ChartTypeBtnGroup").show();
				$("#" + chartNameOne + "ChartRotateBtnGroup").show();							
				$("#" + chartNameOne + "charDateBtn").show();
				$("#" + chartNameOne + "chartqueryBtn").show();
				

				$("#" + chartNameTwo + "Chart").show(); 
				$("#" + chartNameTwo + "SubheadLine").parent().show();
				$("#" + chartNameTwo + "SubheadLineDate").show();
				$("#" + chartNameTwo + "CsvSaveBtn").show();
				$("#" + chartNameTwo + "JsonSaveBtn").show();
				$("#" + chartNameTwo + "ChartTypeBtnGroup").show();
				$("#" + chartNameTwo + "ChartRotateBtnGroup").show();					
				$("#" + chartNameTwo + "charDateBtn").show();
				$("#" + chartNameTwo + "chartqueryBtn").show();


				$("#" + chartNameThree + "Chart").hide();
				$("#" + chartNameThree + "SubheadLine").parent().hide();
				$("#" + chartNameThree + "SubheadLineDate").hide();
				$("#" + chartNameThree + "CsvSaveBtn").hide();
				$("#" + chartNameThree + "JsonSaveBtn").hide();
				$("#" + chartNameThree + "ChartTypeBtnGroup").hide();
				$("#" + chartNameThree + "ChartRotateBtnGroup").hide();				
				$("#" + chartNameThree + "charDateBtn").hide();
				$("#" + chartNameThree + "chartqueryBtn").hide();
				
				
				break;
			};

		case 'HL' : 
			{
			
				$("#" + chartNameOne + "Chart").hide(); 
				$("#" + chartNameOne + "SubheadLine").parent().hide();
				$("#" + chartNameOne + "SubheadLineDate").hide();
				$("#" + chartNameOne + "CsvSaveBtn").hide();
				$("#" + chartNameOne + "JsonSaveBtn").hide();
				$("#" + chartNameOne + "ChartTypeBtnGroup").hide();
				$("#" + chartNameOne + "ChartRotateBtnGroup").hide();				
				$("#" + chartNameOne + "charDateBtn").hide();
				$("#" + chartNameOne + "chartqueryBtn").hide();
				
				
				
				$("#" + chartNameTwo + "Chart").show(); 
				$("#" + chartNameTwo + "SubheadLine").parent().show();
				$("#" + chartNameTwo + "SubheadLineDate").show();
				$("#" + chartNameTwo + "CsvSaveBtn").show();
				$("#" + chartNameTwo + "JsonSaveBtn").show();
				$("#" + chartNameTwo + "ChartTypeBtnGroup").show();
				$("#" + chartNameTwo + "ChartRotateBtnGroup").show();					
				$("#" + chartNameTwo + "charDateBtn").show();
				$("#" + chartNameTwo + "chartqueryBtn").show();
				


				$("#" + chartNameThree + "Chart").show();
				$("#" + chartNameThree + "SubheadLine").parent().show();
				$("#" + chartNameThree + "SubheadLineDate").show();
				$("#" + chartNameThree + "CsvSaveBtn").show();
				$("#" + chartNameThree + "JsonSaveBtn").show();
				$("#" + chartNameThree + "ChartTypeBtnGroup").show();
				$("#" + chartNameThree + "ChartRotateBtnGroup").show();					
				$("#" + chartNameThree + "charDateBtn").show();
				$("#" + chartNameThree + "chartqueryBtn").show();
				
				break;
			};
		

		case 'SL' : 
			{
			
				$("#" + chartNameOne + "Chart").show(); 
				$("#" + chartNameOne + "SubheadLine").parent().show();
				$("#" + chartNameOne + "SubheadLineDate").show();
				$("#" + chartNameOne + "CsvSaveBtn").show();
				$("#" + chartNameOne + "JsonSaveBtn").show();
				$("#" + chartNameOne + "ChartTypeBtnGroup").show();
				$("#" + chartNameOne + "ChartRotateBtnGroup").show();						
				$("#" + chartNameOne + "charDateBtn").show();
				$("#" + chartNameOne + "chartqueryBtn").show();
				

				$("#" + chartNameTwo + "Chart").hide(); 
				$("#" + chartNameTwo + "SubheadLine").parent().hide();
				$("#" + chartNameTwo + "SubheadLineDate").hide();
				$("#" + chartNameTwo + "CsvSaveBtn").hide();
				$("#" + chartNameTwo + "JsonSaveBtn").hide();
				$("#" + chartNameTwo + "ChartTypeBtnGroup").hide();
				$("#" + chartNameTwo + "ChartRotateBtnGroup").hide();					
				$("#" + chartNameTwo + "charDateBtn").hide();
				$("#" + chartNameTwo + "chartqueryBtn").hide();


				$("#" + chartNameThree + "Chart").show();
				$("#" + chartNameThree + "SubheadLine").parent().show();
				$("#" + chartNameThree + "SubheadLineDate").show();
				$("#" + chartNameThree + "CsvSaveBtn").show();
				$("#" + chartNameThree + "JsonSaveBtn").show();
				$("#" + chartNameThree + "ChartTypeBtnGroup").show();
				$("#" + chartNameThree + "ChartRotateBtnGroup").show();						
				$("#" + chartNameThree + "charDateBtn").show();
				$("#" + chartNameThree + "chartqueryBtn").show();
				
				break;
			};
		
		default:{
			
			$("#" + chartNameOne + "Chart").show(); 
				$("#" + chartNameOne + "SubheadLine").parent().show();
				$("#" + chartNameOne + "SubheadLineDate").show();
				$("#" + chartNameOne + "CsvSaveBtn").show();
				$("#" + chartNameOne + "JsonSaveBtn").show();
				$("#" + chartNameOne + "ChartTypeBtnGroup").show();
				$("#" + chartNameOne + "ChartRotateBtnGroup").show();						
				$("#" + chartNameOne + "charDateBtn").show();
				$("#" + chartNameOne + "chartqueryBtn").show();

				$("#" + chartNameTwo + "Chart").show(); 
				$("#" + chartNameTwo + "SubheadLine").parent().show();
				$("#" + chartNameTwo + "SubheadLineDate").show();
				$("#" + chartNameTwo + "CsvSaveBtn").show();
				$("#" + chartNameTwo + "JsonSaveBtn").show();
				$("#" + chartNameTwo + "ChartTypeBtnGroup").show();
				$("#" + chartNameTwo + "ChartRotateBtnGroup").show();						
				$("#" + chartNameTwo + "charDateBtn").show();
				$("#" + chartNameTwo + "chartqueryBtn").show();


				$("#" + chartNameThree + "Chart").show();
				$("#" + chartNameThree + "SubheadLine").parent().show();
				$("#" + chartNameThree + "SubheadLineDate").show();
				$("#" + chartNameThree + "CsvSaveBtn").show();
				$("#" + chartNameThree + "JsonSaveBtn").show();
				$("#" + chartNameThree + "ChartTypeBtnGroup").show();
				$("#" + chartNameThree + "ChartRotateBtnGroup").show();						
				$("#" + chartNameThree + "charDateBtn").show();
				$("#" + chartNameThree + "chartqueryBtn").show();

			
			
		}



	};



};


$(document).on("click", ".showMessageBtn" , function(){
	var itemID = $(this).find('span').text();
	var message =   $("span#message" + itemID).text(); // + $(this).parent().find('span').text();
	var modifiedby = $("span#modifiedBy" + $(this).find('span').text()).text();
	$("div#submitModalBody").html('<pre>' + message + '</pre>');
	$("h4#submitModalLabel").html("Last message submitted by " + modifiedby);
	
});


$.queryDB = function(chartNameOne, chartNameTwo, chartNameThree){
	$("#conditionBtn").html("General Overview " + "<span class=caret></span>");
	
	var data = $("form#queryForm").serialize();
//	var chartType = $("#chartType").val().toLowerCase();
	var chartType = 'bar';
	if ($('#chartRotate').is(":checked")) {chartRotate = 'true'} else {chartRotate = 'false'};
//	if (chartType == 'pie') {chartRotate = 'false'}; 
	var chartRotate = 'true';	
	var tier = $("#tier").val();

	$.ajaxSetup({
		type : "POST",
		dataType : "JSON",
		url : "./ajax/ajaxfonk.php",
	}); 

		$.ajax({
			data: data + "&metric=153&colorName=red&DB=",
			success: function(answer){
				makeChart(jQuery.parseJSON(answer), chartType, chartRotate, "Days" , chartNameOne + "Chart");
				$.kayitlar(jQuery.parseJSON(answer), chartNameOne , "Days");
			},
			
			error: function(XMLHttpRequest, textStatus, errorThrown) { 
	                    alert("Status: " + textStatus); alert("Error: " + errorThrown); 
	                }       
		});

	$.ajax({
		data: data + "&metric=158&colorName=yellow&DB=",
		success: function(answer){
			makeChart(jQuery.parseJSON(answer), chartType, chartRotate, "Days", chartNameTwo + "Chart");
			$.kayitlar(jQuery.parseJSON(answer), chartNameTwo, "Days");
		}
	});


	$.ajax({
		data: data + "&metric=45&colorName=sr&DB=",
		success: function(answer){
			makeChart(jQuery.parseJSON(answer), (chartType == 'pie') ? "bar" : chartType , "false", "average", chartNameThree + "Chart");
			$.kayitlar(jQuery.parseJSON(answer), chartNameThree, "average");
		},
		error: function(jqXHR, textStatus, errorThrown){
			if (textStatus === "timeout"){
				alert("zaman asimi");
			}else alert(textStatus);
		}
	});


} 


$("a.saveBtn").click(function(){
	var data = $(this).find('span').text();
	$.saveJSON(data);
})

/*
 *********************************search date****************************************
 */ 

$(".searchDateBtn, .searchDateBtnBox").click(function(){
	var id = $(this).attr("id");
	var chartName = id.substring(0, id.length - 7);
	var chartType 	= $("#" + chartName + "queryCodeType").text();
	var rotateState = $("#" + chartName + "queryCodeRotate").text(); 
	if (rotateState == 'Horizontal') {rotateState = 'true'} else {rotateState = 'false'};

	var startDate = $("#" + chartName + "btnstartDate").val();
	var endDate   = $("#" + chartName + "btnendDate").val();
	var tier = $.trim($("#" + chartName + "queryCodeTier").text());
	var tierr = '';
	
	if(tier == 'T1')   {tierr = 'T0/1';} 
	if(tier == 'T2')   {tierr = 'T2';} 
	if(tier == 'T1/T2'){tierr = 'all';}


	var valueFieldd = '';
	var data = "timePeriod=&startDate=" + startDate + "&endDate=" + endDate + "&tier=" + tierr + "&chartType=" + chartType;

	if(chartType == '') {chartType = 'bar'};
	if(rotateState == '') {rotateState = 'false'}
		
	if(chartName == 'Drain' || chartName == 'WRoom'){
		valueFieldd = 'Days';
		rotateState = 'true';
		if (chartName == 'Drain'){
			data = data + "&metric=158&colorName=yellow&DB=";
		}else{
			data = data + "&metric=153&colorName=red&DB=";
		}
	}
	
	if(chartName == 'Readiness'){
		valueFieldd = 'average';
		data = data + 	"&metric=45&colorName=sr&DB=";
	}

	if(chartName.substring(0, 10) == 'statistics'){
		valueFieldd = 'number';
		if (chartName.substring(10, 13) == 'SAM'){DB = 'SAM';} else {DB = 'HC'};
		data = data + "&metric=&colorName=&DB=" + DB + "&tier=&errorSelect=HSL";
	}
	
	$.ajaxSetup({
		type : "POST",
		dataType : "JSON",
		url : "./ajax/ajaxfonk.php",
	}); 

		$.ajax({
			data: data,
			success: function(answer){
				if(valueFieldd != 'number'){
					makeChart(jQuery.parseJSON(answer), chartType, rotateState, valueFieldd, chartName + "Chart");
					$.kayitlar(jQuery.parseJSON(answer), chartName , valueFieldd);
					
				}else{
					makeChart(answer, chartType, rotateState, valueFieldd, chartName + "Chart");
					$.kayitlar(answer, chartName , valueFieldd);
				}
			},
			
			error: function(XMLHttpRequest, textStatus, errorThrown) { 
	                    alert("Status: " + textStatus); alert("Error: " + errorThrown); 
	                }       
		});
//}

});


$(".searchDateBtnClose").click(function(){
	var id = $(this).attr("id");
	var chartName = id.substring(0, id.length - 7);
	$("#" + chartName + "customDatePanel").hide();
	

});

/*
 ************************************************************************************
 */

/*
 *____________________chart Type_____________________________
 */

 $(".chartTypeBtn").click(function(){
 
	var id = $(this).attr("id");
	var valueField = '';
	var chartName = id.substring(0, id.length - 8); //chartName tüm elementlere ulasmamizi saglayan anahtar degisken.
	
	if(chartName.substring(0, 10) == 'statistics'){ //grafigin yazdirilmasi icin gerekli olan field adinin belirlenmesi.....
		valueField = 'number';
	}
	else{
		if(chartName == 'Readiness'){valueField = 'average';} else {valueField = 'Days';}
	}
	
	var chartTypeLbl = $.trim($(this).text().substring(0, 4)); // butonun üzerine yazilmasi icin gerekli olan label.
	var chartType = $.trim($(this).text().substring(0, 4)).toLowerCase(); //chartType'in belirlenmesi icin kullanilan degisken.
	$("#" + chartName + "chartBtn").html(chartTypeLbl + " Chart " + "<span class=caret></span>"); //butonun uzerine yazilan yazi.

	$("#" + chartName + "queryCodeValueField").text(valueField);
	$("#" + chartName + "queryCodeType").text(chartType);
 });
 
 
$(".chartRotateBtn").click(function(){
	var id = $(this).attr("id");
	var rotateState = $.trim(id.substring(id.length -5));
	var chartName = id.substring(0, id.length - 16); //chartName tüm elementlere ulasmamizi saglayan anahtar degisken.
	if (rotateState == 'True') {rotateState = 'Horizontal'} else {rotateState = 'Vertical'};
	$("#" + chartName + "chartRotateBtn").html(rotateState + " " + "<span class=caret> </span>");
	$("#" + chartName + "queryCodeRotate").text(rotateState);
	
}) ;



 $(".chartTierBtn").click(function(){
	var id = $(this).attr("id");
	var chartName = id.substring(0, id.length - 8); //chartName tüm elementlere ulasmamizi saglayan anahtar degisken.
	var tier = $.trim($(this).text()); // butonun üzerine yazilmasi icin gerekli olan label.
	
	if (tier == 'T1'){
		$("#conditionDropDown").html('<li><a class= "chartconditionalBtn" id="' + chartName + 'chartgener00G">General Overview</a></li>' + 
		  '<li><a class= "chartconditionalBtn" id="' + chartName + 'chartabove60A"><b>Above 60%</b>Overview</a></li>' +
		  '<li><a class= "chartconditionalBtn" id="' + chartName + 'chartbelow60B"><b>Below 60%</b> Overview</a></li>'); 
		  
	}else if(tier == 'T2'){
		$("#conditionDropDown").html('<li><a class= "chartconditionalBtn"  id="' + chartName + 'chartgener00G">General Overview</a></li>' + 
		  '<li><a class= "chartconditionalBtn" id="' + chartName + 'chartabove80A"><b>Above 80%</b>Overview</a></li>' +
		  '<li><a class= "chartconditionalBtn" id="' + chartName + 'chartbelow80B"><b>Below 80%</b> Overview</a></li>'); 
		
	}else{
		$("#conditionDropDown").html('<li><a class= "chartconditionalBtn" id="' + chartName + 'chartgener00G">General Overview</a></li>' + 
		  '<li><a class= "chartconditionalBtn" id="' + chartName + 'chartabove60A"><b>Above 60%</b>Overview</a></li>' +
		  '<li><a class= "chartconditionalBtn" id="' + chartName + 'chartbelow60B"><b>Below 60%</b> Overview</a></li>' +
		  '<li><a class= "chartconditionalBtn" id="' + chartName + 'chartabove80A"><b>Above 80%</b>Overview</a></li>' +
		  '<li><a class= "chartconditionalBtn" id="' + chartName + 'chartbelow80B"><b>Below 80%</b> Overview</a></li>'); 
		  
	}
	
	$("#" + chartName + "chartTierBtn").html(tier + " <span class=caret></span>"); //butonun uzerine yazilan yazi.
	$("#" + chartName + "queryCodeTier").text(tier);
 });






 

$(".chartqueryBtn").click(function(){
	//_____________verilerin cekilip fonksiyona parametre olarak gonderilecegi ve grafing olusturalacagi bolum______________
	var id = $(this).attr("id");
	var chartName 	= $.trim(id.substring(0, id.length - 13));
	var jsonCode	= $("#" + chartName + "JsonCode").text(); // verilerin saglagan json kodunn cekildigi yer..
	var chartType 	= $("#" + chartName + "queryCodeType").text();
	var rotateState = $("#" + chartName + "queryCodeRotate").text(); 
	var valueField  = $("#" + chartName + "queryCodeValueField").text(); 
	if (rotateState == 'Horizontal') {rotateState = 'true'} else {rotateState = 'false'};
	makeChart(jQuery.parseJSON(jsonCode), chartType, rotateState, valueField , chartName + "Chart");
	
});

/*
 *___________________________________________________________
 */
 
 
 /*
  *****************Chart Date Combobox icin gerekli tarih islemleri*************************
  */
 
 	$(".siteListHead select, .dateGroup select").change(function(){
		var id = $(this).attr("id");
		var chartName 	= $.trim(id.substring(0, id.length - 10));
		var value = $(this).val();
		
		if(value == '24h'){
			var date = moment().add('days',-1).format().substring(0, 10);
			$("#" + chartName + "btnstartDate").val(date);
			$("#" + chartName + "customDatePanel").hide();

		}
		
		if(value == '48h'){
			var date = moment().add('days',-2).format().substring(0, 10);
			$("#" + chartName + "btnstartDate").val(date);
			$("#" + chartName + "customDatePanel").hide();
			
		}

		if(value == 'Lweek'){
			var date = moment().add('days',-7).format().substring(0, 10);
			$("#" + chartName + "btnstartDate").val(date);
			$("#" + chartName + "customDatePanel").hide();

		}

		if(value == 'L2week'){
			var date = moment().add('days',-15).format().substring(0, 10);
			$("#" + chartName + "btnstartDate").val(date);
			$("#" + chartName + "customDatePanel").hide();

		}
		
		if(value == 'Lmonth'){
			var date = moment().add('days',-30).format().substring(0, 10);
			$("#" + chartName + "btnstartDate").val(date);
			$("#" + chartName + "customDatePanel").hide();


		}

		if(value == 'L2months'){
			var date = moment().add('days',-61).format().substring(0, 10);
			$("#" + chartName + "btnstartDate").val(date);
			$("#" + chartName + "customDatePanel").hide();

		}

		if(value == 'L3months'){
			var date = moment().add('days',-91).format().substring(0, 10);
			$("#" + chartName + "btnstartDate").val(date);
			$("#" + chartName + "customDatePanel").hide();
		}

		if(value == 'custom'){
			$("#" + chartName + "customDatePanel").show();
		}
	});
 
 /*
  ******************************************************************************************
  */
 


/*
 *****************************site Readiness Buttons***************************************
 */



$(document).on("click", ".chartconditionalBtn", function(){
	
	var id = $(this).attr("id");
	var chartName = id.substring(0, id.length - 13); //chartName tüm elementlere ulasmamizi saglayan anahtar degisken.
	var conditionValue = id.substring(id.length - 3, id.length - 1);
	var condition      = id.substring(id.length - 1, id.length);
	var chartType = $("#" + chartName + "queryCodeType").text();
	
	var tier = $.trim($("#" + chartName + "queryCodeTier").text());
	var tierr = '';
	
	if(tier == 'T1')   {tierr = 'T0/1';} 
	if(tier == 'T2')   {tierr = 'T2';} 
	if(tier == 'T1/T2'){tierr = 'all';}
	
	if (condition == 'A') {conditionValue = conditionValue}
	if (condition == 'B') {conditionValue = conditionValue - 1}
	if (condition == 'G') {conditionValue = 0}

	var startDate = $("#" + chartName + "btnstartDate").val();
	var endDate   = $("#" + chartName + "btnendDate").val();
	
	var data = "startDate=" + startDate +  "&endDate=" + endDate + "&tier=" + tierr + "&chartType=" + chartType;

	$.ajaxSetup({
		type : "POST",
		dataType : "JSON",
		url : "./ajax/ajaxfonk2.php"
	}); 

	$.ajax({
		data: data + "&metric=45&colorName=sr&condition=" + conditionValue,
		success: function(answer){
		makeChart(jQuery.parseJSON(answer), "line", "false", "average" , "ReadinessChart");
		$.kayitlar(jQuery.parseJSON(answer), "Readiness" , "average");
		}
	});


	
	
});

/*
 ******************************** end ofsite Readiness Buttons********************************
 */


$.save = function(){
	var value = $("form#siteForm").serialize();
	var operation = 'save';
	$.ajax({
		url: "./ajax/ajax.php",	
		type: "POST",
		data: value + "&operation=" + operation,
		dataType: "json",
		success: function(answer)
		{
			if(answer.errors)
				{	
					$(".alert-danger").html(answer.errors).fadeIn(500);
					$(".alert-danger").html(answer.errors).fadeOut(2000);	
					$.cleanForm();				
					$("#siteName").focus();
				}
			else
				
				{	
					$("#siteerror-panel").fadeIn(500);
					$('#siteSaveBtn').attr('disabled' , 'disabled');
					$("#siteName").focus();
					$("div#wrId").html(answer.id);
					var siteName = $("#siteName").val();
					var	nesne = $("#siteErrorPanel").offset();
			 		var	ust = nesne.top - 30;
					$('html,body').animate({scrollTop: ust}, 500);
					$('.waitingRoomList').append('<a href="#" class="list-group-item waitingRoomListItems">' + siteName + '<span style="display:none;" class="waitingRoomListItem">' + answer.id + '</span>' + '<span class= "pull-right"><button type="button" class="btn btn-danger btn-xs" data-toggle="modal" data-target="#myModalMorg" style="margin-right:5px;">Send to Morgue</button>' + '<button type="button" class="btn btn-danger btn-xs" data-toggle="modal" data-target="#myModal">Get Out of WaitingRoom</button>' +
						'</span>' +  '</a>');
					var noRecord = $('.waitingRoomList a#noRecord');
					if (noRecord.find())
						{
							noRecord.remove();
						}

				}
		},
		error: function (xhr, ajaxOptions, thrownError) {
		alert(thrownError);
       }
	});
};



$(document).on("click", ".waitingRoomListItems", function(){
	var indis = $(this).index();
	$("div#waitingRoomListid").html(indis);

});



$(document).on("click", "#removeSite", function(){
	var id = $("div#wrId").html();
	var indis = $("div#waitingRoomListid").html();
	var operation = 'remove';
	$.ajax({
	url: "./ajax/ajax.php",
	data: "operation=" + operation + "&idWR=" + id,
	type: "POST",
	dataType: "JSON",
	success: function(answer){
		if(answer.errors)
			{
				alert(answer.errors);
			}
		else
			{
				$("div.waitingRoomList a.waitingRoomListItems:eq(" + indis + ")").remove();
			}
	},
	error: function(){
		
	}
	});


});


/************************************************HC Errors************************************************/
$(document).on("click", ".hcremoveExitCode", function(){
	var idHC = $(this).parent('td').prev('td').prev('td').html();
	var operation ="remove";
	$.ajax({
		url: "./ajax/ajax_hc.php",
		data: "operation=" + operation + "&idHC=" + idHC,
		type: "POST",
		dataType: "JSON",
		success: function(answer){
			if(answer.errors)
				{
					alert(answer.errors);
				}
		},
		error: function(){
			
		}
	});

    $(this).parent().parent().remove();
});
		


$.addHCExitCode = function (){
	var value_hc = $("form#hcForm").serialize();
	var idWR = $("div#wrId").html();
	var operation = 'addhc';
	$.ajax({
		url: "./ajax/ajax_hc.php",
		data: value_hc + "&idWR=" + idWR + "&operation=" + operation,
		type: "POST",
		dataType: "JSON",
		success: function(answer){
			if(answer.errors)
				{
					$(".alert-danger").html(answer.errors).fadeIn(500);
					$(".alert-danger").html(answer.errors).fadeOut(2000);	
				}
			else
				{
					var idHC = answer.idHC;
					var hcExitCode = $("#hcexitcode").val();
					var liste = $("table.hcList tr").size() - 1;
					var liste = $("table.hcList").append('<tr>'+ '<td>' + idHC + '</td>' + '<td class="hcexitcode">' + hcExitCode + '</td>' + '<td>' + '<a class="btn btn-danger btn-xs hcremoveExitCode"> Remove </a>' + '</td>' + '</tr>');
				}
		},
		error: function(){
		
		}
	});
	
};

		
/*******************************************SAM ERRORS ***************************************************/
$(document).on("click", ".samremoveExitCode", function(){
	//var indis = $(this).parent().find('.hcexitcode').text();
	//var indis = $(this).parent().find('td.hcexitcode').text();
	var idSAM = $(this).parent('td').prev('td').prev('td').html();
	var operation ="remove";
	$.ajax({
		url: "./ajax/ajax_sam.php",
		data: "operation=" + operation + "&idSAM=" + idSAM,
		type: "POST",
		dataType: "JSON",
		success: function(answer){
			if(answer.errors)
				{
					alert(answer.errors);
				}
		},
		error: function(){
			
		}
	});

    $(this).parent().parent().remove();
});


$.addSAMExitCode = function (){
	var value_sam = $("form#samForm").serialize();
	var idWR = $("div#wrId").html();
	var operation = 'addsam';
	$.ajax({
		url: "./ajax/ajax_sam.php",
		data: value_sam + "&idWR=" + idWR + "&operation=" + operation,
		type: "POST",
		dataType: "JSON",
		success: function(answer){
			if(answer.errors)
				{
					alert("error");
					$(".alert-danger").html(answer.errors).fadeIn(500);
					$(".alert-danger").html(answer.errors).fadeOut(2000);	
				}
			else
				{
					var idSAM = answer.idSAM;
					var samexitcode = $("#samexitcode").val();
					var liste = $("table.samList tr").size() - 1;
					var liste = $("table.samList").append('<tr>'+ '<td>' + idSAM + '</td>' + '<td class="samexitcode">' + samexitcode + '</td>' + '<td>' + '<a class="btn btn-danger btn-xs samremoveExitCode"> Remove </a>' + '</td>' + '</tr>');
				}
		},
		error: function(){
			
		}
	});
	
};



/*********************************************************************************************************/




/*******************************************LINKS ERRORS ***************************************************/
$(document).on("click", ".linksremoveExitCode", function(){
//$(".linksremoveExitCode").on("click", function(){
	//var indis = $(this).parent().find('.hcexitcode').text();
	//var indis = $(this).parent().find('td.hcexitcode').text();
	var idLINKS = $(this).parent('td').prev('td').prev('td').prev('td').prev('td').prev('td').html();
	var operation ="remove";
	$.ajax({
		url: "./ajax/ajax_links.php",
		data: "operation=" + operation + "&idLINKS=" + idLINKS,
		type: "POST",
		dataType: "JSON",
		success: function(answer){
			if(answer.errors)
				{
					alert(answer.errors);
				}
		},
		error: function(){
			
		}
	});

    $(this).parent().parent().remove();
});


$.addLINKSExitCode = function (){
	var value_links = $("form#linksForm").serialize();
	var idWR = $("div#wrId").html();
	var operation = 'addlinks';
	$.ajax({
		url: "./ajax/ajax_links.php",
		data: value_links + "&idWR=" + idWR + "&operation=" + operation,
		type: "POST",
		dataType: "JSON",
		success: function(answer){
			if(answer.errors)
				{
					alert("error");
					$(".alert-danger").html(answer.errors).fadeIn(500);
					$(".alert-danger").html(answer.errors).fadeOut(2000);	
				}
			else
				{
					var idLINKS = answer.idLINKS;
					var goodT2tT1 = $("#goodT2tT1").val();
					var goodT2fT1 = $("#goodT2fT1").val();
					var activeT2tT1 = $("#activeT2tT1").val();
					var activeT2fT1 = $("#activeT2fT1").val();

					var liste = $("table.linksList tr").size() - 1;
					var liste = $("table.linksList").append('<tr>'+ '<td>' + idLINKS + '</td>' + '<td>' + goodT2fT1 + '</td>' + '<td>' + goodT2tT1 + '</td>' + '<td>' + activeT2fT1 + '</td>' + '<td>' + activeT2tT1 + '</td>' + '<td>' + '<a class="btn btn-danger btn-xs linksremoveExitCode"> Remove </a>' + '</td>' + '</tr>');
				}
		},
		error: function(XMLHttpRequest, textStatus, errorThrown) { 
                    alert("Status: " + textStatus); alert("Error: " + errorThrown); 
                }       
	});
	
};


/*********************************************************************************************************/


/*********************************************************************************************************
 *      MORGUE and WaitingRoom //wrlist
 */


$(document).on("click" ,  "#sendMorgue", function(){
	
	var id = $("span#siteID").text();
	var operation = 'sendmorgue';
	$.ajax({
	url: "./ajax/ajax.php",
	data: "operation=" + operation + "&idWR=" + id,
	type: "POST",
	dataType: "JSON",
	success: function(answer){
		if(answer.errors)
			{
				alert(answer.errors);
			}
		else
			{
				window.location.href=window.location.href;
			}
		},
	});	

	
});



$(document).on("click" ,  "#sendMorguefromadd", function(){
	
	var id = $("div#wrId").html();
	var operation = 'sendmorgue';
	//alert(id);
	$.ajax({
	url: "./ajax/ajax.php",
	data: "operation=" + operation + "&idWR=" + id,
	type: "POST",
	dataType: "JSON",
	success: function(answer){
		if(answer.errors)
			{
				alert("Error Code : " + answer.errors);
			}
		else
			{
				window.location.href="addsite.php";
				
			}
		},
	});	

	
});



$(document).on("click" ,  "#removeMorgue", function(){
	
	var id = $("span#siteID").text();
	var operation = 'removemorgue';
	$.ajax({
	url: "./ajax/ajax.php",
	data: "operation=" + operation + "&idWR=" + id,
	type: "POST",
	dataType: "JSON",
	success: function(answer){
		if(answer.errors)
			{
				alert("Error Code : " + answer.errors);
			}
		else
			{
				window.location.href=window.location.href;
			}
		},
	});	

	
});



$(document).on("click", ".panelID", function(){
	
	var value = $(this).attr("id");
	$("span#siteID").text(value);
	
});

$(document).on("click", "#getOutWr", function(){
	var id = $("span#siteID").text();
	var operation = 'remove';
	$.ajax({
	url: "./ajax/ajax.php",
	data: "operation=" + operation + "&idWR=" + id,
	type: "POST",
	dataType: "JSON",
	success: function(answer){
		if(answer.errors)
			{
				alert("Error Code : " + answer.errors);
			}
		else
			{
				window.location.href=window.location.href;
			}
		},
	});
	// veri tabani islemleri

});
/**********************************************************************************************************/

$(document).ready(function() {
   $("li.disabled a").click(function() {
     return false;
   });
});

});



