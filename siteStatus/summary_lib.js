/* JavaScript ************************************************************** */
"use strict";



/* ************************************************************************* */
/* data:                                                                     */
/* ************************************************************************* */
var sizeCnvs;
var noBins;



/* ************************************************************************* */
/* functons:                                                                 */
/* ************************************************************************* */
function dateString1(timeInSeconds) {
   // function to return a full time string like "Th, 1970-Jan-01 00:00"
   var timeStr = "";
   var dayNames = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
   var monthNames = [ "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

   var timeObj = new Date( timeInSeconds * 1000 );

   timeStr = dayNames[ timeObj.getUTCDay() ] + ", " +
      timeObj.getUTCFullYear() + "-" + monthNames[ timeObj.getUTCMonth() ];
   if ( timeObj.getUTCDate() < 10 ) {
      timeStr += "-0" + timeObj.getUTCDate();
   } else {
      timeStr += "-" + timeObj.getUTCDate();
   }
   if ( timeObj.getUTCHours() < 10 ) {
      timeStr += " 0" + timeObj.getUTCHours();
   } else {
      timeStr += " " + timeObj.getUTCHours();
   }
   if ( timeObj.getUTCMinutes() < 10 ) {
      timeStr += ":0" + timeObj.getUTCMinutes();
   } else {
      timeStr += ":" + timeObj.getUTCMinutes();
   }

   return timeStr;
}

function dateString2(timeInSeconds) {
   // function to return an abbreviated date string like "Su, Jan-01"
   var timeStr = "";
   var dayNames = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
   var monthNames = [ "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

   var timeObj = new Date( timeInSeconds * 1000 );

   if ( timeObj.getUTCDate() < 10 ) {
      timeStr = dayNames[ timeObj.getUTCDay() ] + ", " +
         monthNames[ timeObj.getUTCMonth() ] + "-0" + timeObj.getUTCDate();
   } else {
      timeStr = dayNames[ timeObj.getUTCDay() ] + ", " +
         monthNames[ timeObj.getUTCMonth() ] + "-" + timeObj.getUTCDate();
   }

   return timeStr;
}

function writeTable() {

   var myWidth = 1600;
   if ( window.innerWidth ) {
      myWidth = window.innerWidth;
   }
   if ( myWidth < 1440 ) {
      var fontHdrSite = 'font-size: 20px; font-weight: 700;';
      var fontHdrGGUS = 'font-size: 14px; font-weight: 600;';
      var fontHdrOthr = 'font-size: 18px; font-weight: 600;';
      var fontSiteName = 'font-size: 18px; font-weight: 500;';
      // Previous Month:   (4*30)+30+1   Magnified: 4*(4*30)+2*30
      // Previous Week:    (7*24)+28+1   Magnified: 4*(7*24)+2*28
      // Yesterday:        (24*4)+24+1   Magnified: 4*(24*4)+2*24
      // Today:          2*(24*4)+24+1   Magnified: 5*(24*4)+2*24
      // Following Week:   (7*24)+28+1   Magnified: 4*(7*24)+2*28
      sizeCnvs = [ "151", "197", "121", "217", "197" ];
      var sizeMagn = [ "540", "728", "432", "528", "728" ];
      noBins  = [ 1, 1, 1, 2, 1 ];
   } else if ( myWidth < 2048 ) {
      // standard page/view:
      var fontHdrSite = 'font-size: 22px; font-weight: 700;';
      var fontHdrGGUS = 'font-size: 16px; font-weight: 600;';
      var fontHdrOthr = 'font-size: 20px; font-weight: 600;';
      var fontSiteName = 'font-size: 18px; font-weight: 500;';
      // Previous Month: 2*(4*30)+30+2   Magnified: 4*(4*30)+2*30
      // Previous Week:    (7*24)+28+2   Magnified: 4*(7*24)+2*28
      // Yesterday:      2*(24*4)+24+2   Magnified: 4*(24*4)+2*24
      // Today:          3*(24*4)+24+2   Magnified: 5*(24*4)+2*24
      // Following Week:   (7*24)+28+2   Magnified: 4*(7*24)+2*28
      sizeCnvs = [ "272", "198", "218", "314", "197" ];
      var sizeMagn = [ "540", "728", "432", "528", "728" ];
      noBins  = [ 2, 1, 2, 3, 1 ];
   } else {
      // 4k display (QSXGA and higher):
      var fontHdrSite = 'font-size: 26px; font-weight: 700;';
      var fontHdrGGUS = 'font-size: 18px; font-weight: 600;';
      var fontHdrOthr = 'font-size: 24px; font-weight: 700;';
      var fontSiteName = 'font-size: 20px; font-weight: 500;';
      // Previous Month: 3*(4*30)+30+2   Magnified: 4*(4*30)+2*30
      // Previous Week:  2*(7*24)+28+2   Magnified: 4*(7*24)+2*28
      // Yesterday:      3*(24*4)+24+2   Magnified: 4*(24*4)+2*24
      // Today:          5*(24*4)+24+2   Magnified: 5*(24*4)+2*24
      // Following Week:   (7*24)+28+2   Magnified: 4*(7*24)+2*28
      sizeCnvs = [ "392", "366", "314", "506", "197" ];
      var sizeMagn = [ "540", "728", "432", "528", "728" ];
      noBins  = [ 3, 2, 3, 5, 1 ];
   }

   // compose table header:
   var myTableStr = '<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="0">\n<TR' +
      '>\n   <TH NOWRAP ALIGN="left"><SPAN STYLE="' + fontHdrSite + '">Siten' +
      'ame</SPAN>\n   <TH COLSPAN="3" NOWRAP ALIGN="center"><SPAN STYLE="' +
      fontHdrGGUS + '">GGUS</SPAN>\n   <TH NOWRAP ALIGN="center"><SPAN STYLE' +
      '="' + fontHdrOthr + '">Prev. Month</SPAN>\n   <TH NOWRAP ALIGN="cente' +
      'r"><SPAN STYLE="' + fontHdrOthr + '">Previous Week</SPAN>\n   <TH NOW' +
      'RAP ALIGN="center"><SPAN STYLE="' + fontHdrOthr + '">Yesterday</SPAN>' +
      '\n   <TH NOWRAP ALIGN="center"><SPAN STYLE="' + fontHdrOthr + '">UTC ' +
      'Today</SPAN>\n   <TH NOWRAP ALIGN="center"><SPAN STYLE="' +
      fontHdrOthr + '">Following Week</SPAN>\n';


   // loop over site summary data and write a table row for each site:
   for ( var sCnt=0; sCnt < siteStatusData.length; sCnt+=1 ) {
      var urlStr;
      var bgcStr, cntStr;

      var sName = siteStatusData[sCnt].site.toString();

      // compose URL for individual site status page:
      urlStr = siteStatusInfo['url'] + 'detail.html?site=' + sName;
      // write first, site name, column:
      myTableStr += '<TR>\n   <TD ALIGN=\"left\"><A HREF=\"' + urlStr +
         '\"><SPAN STYLE="' + fontSiteName + '">' + sName + '</SPAN></A>\n';

      // compose URL for GGUS site-tickets-of-CMS search:
      urlStr = 'https://ggus.eu/?mode=ticket_search&show_columns_check[]=TIC' +
         'KET_TYPE&show_columns_check[]=AFFECTED_SITE&show_columns_check[]=P' +
         'RIORITY&show_columns_check[]=RESPONSIBLE_UNIT&show_columns_check[]' +
         '=CMS_SU&show_columns_check[]=STATUS&show_columns_check[]=DATE_OF_C' +
         'HANGE&show_columns_check[]=SHORT_DESCRIPTION&supportunit=&su_hiera' +
         'rchy=0&vo=cms&cms_site=' + sName + '&specattrib=none&status=open&&' +
         'typeofproblem=all&ticket_category=all&date_type=creation+date&tf_r' +
         'adio=1&timeframe=any&orderticketsby=REQUEST_ID&orderhow=desc&searc' +
         'h_submit=GO!';
      // select background colour for GGUS ticket count of site:
      if ( siteStatusData[sCnt].ggus[0] < 0 ) {
         // grey background if no valid GGUS ticket information
         bgcStr = 'CLASS="tableCellRound" ALIGN="center" BGCOLOR="#F4F4F4"';
      } else if ( siteStatusData[sCnt].ggus[0] == 0 ) {
         bgcStr = 'ALIGN="center"';
      } else if ( siteStatusData[sCnt].ggus[1] <= 3600 ) {
         // dark-orange background if youngest ticket is less than one hour old
         bgcStr = 'CLASS="tableCellRound" ALIGN="center" BGCOLOR="#FFA500"';
      } else if ( siteStatusData[sCnt].ggus[1] <= 86400 ) {
         // light-orange background if youngest ticket is less than one day old
         bgcStr = 'CLASS="tableCellRound" ALIGN="center" BGCOLOR="#FFE866"';
      } else if ( siteStatusData[sCnt].ggus[2] > 3888000 ) {
         // brown background if oldest ticket is over 45 days old
         bgcStr = 'CLASS="tableCellRound" ALIGN="center" BGCOLOR="#B08032"';
      } else {
         bgcStr = 'ALIGN="center"';
      }
      // blank out zeros (but keep link so people can click):
      if ( siteStatusData[sCnt].ggus[0] > 0 ) {
         cntStr = siteStatusData[sCnt].ggus[0].toString();
      } else if ( siteStatusData[sCnt].ggus[0] == 0 ) {
         cntStr = '&nbsp';
      } else {
         cntStr = '?';
      }
      // write second, GGUS ticket count, column:
      myTableStr += '   <TD NOWRAP>&nbsp;\n   <TD ' + bgcStr + '><A HREF="' +
         urlStr + '"><B>' + cntStr + '</B></A>\n   <TD NOWRAP>&nbsp;\n';

      // compose URL for previous month's site status page:
      urlStr = siteStatusInfo['url'] + 'pmonth.html?site=' + sName;
      // write third, previous month , column:
      myTableStr += '   <TD><A CLASS="toolTip1" HREF="' + urlStr +
         '"><CANVAS ID="cnvs_' + sName + '_sec1" WIDTH="' + sizeCnvs[0] +
         '" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPA' +
         'DDING="0" CELLSPACING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Pr' +
         'evious Month of ' + sName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD' +
         ' COLSPAN="2"><CANVAS ID="cnvs_' + sName + '_mag1" WIDTH="' +
         sizeMagn[0] + '" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">' +
         dateString2( siteStatusInfo['time'] - 38 * 86400 ) +
         '<TD ALIGN="right">' +
         dateString2( siteStatusInfo['time'] - 9 * 86400 ) +
         '</TABLE></SPAN></A>\n';

      // compose URL for previous week's site status page:
      urlStr = siteStatusInfo['url'] + 'pweek.html?site=' + sName;
      // write fourth, previous week , column:
      myTableStr += '   <TD><A CLASS="toolTip2" HREF="' + urlStr +
         '"><CANVAS ID="cnvs_' + sName + '_sec2" WIDTH="' + sizeCnvs[1] +
         '" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPA' +
         'DDING="0" CELLSPACING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Pr' +
         'evious Week of ' + sName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD ' +
         'COLSPAN="2"><CANVAS ID="cnvs_' + sName + '_mag2" WIDTH="' +
         sizeMagn[1] + '" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">' +
         dateString2( siteStatusInfo['time'] - 8 * 86400 ) +
         '<TD ALIGN="right">' +
         dateString2( siteStatusInfo['time'] - 2 * 86400 ) +
         '</TABLE></SPAN></A>\n';

      // compose URL for yesterday's site status page:
      urlStr = siteStatusInfo['url'] + 'yesterday.html?site=' + sName;
      // write fifth, yesterday, column:
      myTableStr += '   <TD><A CLASS="toolTip3" HREF="' + urlStr +
         '"><CANVAS ID="cnvs_' + sName + '_sec3" WIDTH="' + sizeCnvs[2] +
         '" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPA' +
         'DDING="0" CELLSPACING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Ye' +
         'sterday (' + dateString2( siteStatusInfo['time'] - 86400 ) +
         ') of ' + sName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSPAN="2' +
         '"><CANVAS ID="cnvs_' + sName + '_mag3" WIDTH="' + sizeMagn[2] +
         '" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">00:00<TD ALIGN="right"' +
         '>24:00</TABLE></SPAN></A>\n';

      // compose URL for today's site status page:
      urlStr = siteStatusInfo['url'] + 'today.html?site=' + sName;
      // write sixth, today, column:
      myTableStr += '   <TD><A CLASS="toolTip4" HREF="' + urlStr +
         '"><CANVAS ID="cnvs_' + sName + '_sec4" WIDTH="' + sizeCnvs[3] +
         '" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPA' +
         'DDING="0" CELLSPACING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>To' +
         'day (' + dateString2( siteStatusInfo['time'] ) + ') of ' + sName +
         '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSPAN="2"><CANVAS ID="cnvs' +
         '_' + sName + '_mag4" WIDTH="' + sizeMagn[3] + '" HEIGHT="36"></CAN' +
         'VAS><TR><TD ALIGN="left">00:00<TD ALIGN="right">24:00</TABLE></SPA' +
         'N></A>\n';

      // compose URL for following week's site status page:
      urlStr = siteStatusInfo['url'] + 'fweek.html?site=' + sName;
      // write seventh, following week, column:
      myTableStr += '   <TD><A CLASS="toolTip5" HREF="' + urlStr +
         '"><CANVAS ID="cnvs_' + sName + '_sec5" WIDTH="' + sizeCnvs[4] +
         '" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPA' +
         'DDING="0" CELLSPACING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Fo' +
         'llowing Week of ' + sName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD' +
         ' COLSPAN="2"><CANVAS ID="cnvs_' + sName + '_mag5" WIDTH="' +
         sizeMagn[4] + '" HEIGHT="36"></CANVAS><TR>' + '<TD ALIGN="left">' +
         dateString2( siteStatusInfo['time'] + 1 * 86400 ) +
         '<TD ALIGN="right">' +
         dateString2( siteStatusInfo['time'] + 7 * 86400 ) +
         '</TABLE></SPAN></A>\n';
   }

   // add a row/line in case there is a message:
   if ( siteStatusInfo['msg'] != '' ) {
      myTableStr += '<TR>\n   <TD COLSPAN="9" ALIGN=\"left\"><SPAN STYLE="co' +
         'lor:blue; font-weight:bold;">' + siteStatusInfo['msg'] + '</SPAN>\n';
   }


   // compose table trailer:
   myTableStr += '</TABLE>\n';


   // update main DIV section with table:
   document.getElementById("mainDIV").innerHTML = myTableStr;
}

function updateTimestamps() {

   document.getElementById("titleSPAN").innerHTML = '(' +
      dateString1( siteStatusInfo['time'] ) + ' GMT)';

   var timeObj = new Date( siteStatusInfo['time'] * 1000 );
   document.getElementById("legendSPAN").innerHTML =
      timeObj.toLocaleString(window.navigator.language, {weekday: "short",
         year: "numeric", month: "long", day: "numeric", hour: "numeric",
         minute: "2-digit", timeZoneName: "short" });

}

function fillCanvases() {

   // for the tic length we need to know the weekday:
   var dataDay  = ( new Date(siteStatusInfo['time'] * 1000) ).getDay();

   // loop over site summary data and fill the six canvases:
   for ( var sCnt=0; sCnt < siteStatusData.length; sCnt+=1 ) {
      var cData;
      var cDom;
      var cCtxS;
      var cCtxM;
      var mData;
      var xleft;

      var sName = siteStatusData[sCnt].site.toString();

      // first canvas, previous month, 120 six-hour/quarter-day entries:
      cData = siteStatusData[sCnt].pmonth.split("");
      cDom = document.getElementById('cnvs_' + sName + '_sec1');
      cCtxS = cDom.getContext("2d");
      cDom = document.getElementById('cnvs_' + sName + '_mag1');
      cCtxM = cDom.getContext("2d");
      mData = Math.min(cData.length, 120 );
      for ( var qday=0; qday < mData; qday+=1) {
         xleft = ( qday * noBins[0] ) + Math.trunc(qday/4);
         if ( qday % 4 == 0 ) {
            if ( (dataDay - 38 + Math.trunc(qday/4)) % 7 == 0 ) {
               // full scale tick at the start of the week, Sunday-to-Monday
               cCtxS.fillStyle = "#000000";
               cCtxS.fillRect(xleft,0,1,18);
               cCtxM.fillStyle = "#000000";
               cCtxM.fillRect(qday*4+Math.trunc(qday/4)*2,0,2,36);
            } else {
               // 75% tick at the start of a day
               cCtxS.fillStyle = "#000000";
               cCtxS.fillRect(xleft,4,1,14);
               cCtxM.fillStyle = "#000000";
               cCtxM.fillRect(qday*4+Math.trunc(qday/4)*2,8,2,28);
            }
         }
         switch ( cData[ qday ] ) {
            case "o":
               cCtxS.fillStyle = "#80FF80";
               cCtxS.fillRect(1+xleft,0,noBins[0],18);
               cCtxM.fillStyle = "#80FF80";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,36);
               break;
            case "w":
               cCtxS.fillStyle = "#FFFF00";
               cCtxS.fillRect(1+xleft,0,noBins[0],18);
               cCtxM.fillStyle = "#FFFF00";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,36);
               break;
            case "e":
               cCtxS.fillStyle = "#FF0000";
               cCtxS.fillRect(1+xleft,0,noBins[0],18);
               cCtxM.fillStyle = "#FF0000";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,36);
               break;
            case "p":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[0],6);
               cCtxS.fillRect(1+xleft,12,noBins[0],6);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,12);
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,24,4,12);
               break;
            case "d":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[0],18);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,36);
               break;
            case "a":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[0],4);
               cCtxS.fillRect(1+xleft,6,noBins[0],2);
               cCtxS.fillRect(1+xleft,10,noBins[0],2);
               cCtxS.fillRect(1+xleft,14,noBins[0],4);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,8);
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,12,4,4);
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,20,4,4);
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,28,4,8);
               break;
            case "U":
            case "V":
            case "W":
            case "X":
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,0,noBins[0],18);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,36);
               break;
            case "K":
            case "L":
            case "M":
            case "N":
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,0,noBins[0],18);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,36);
               break;
            default:
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+xleft,0,noBins[0],18);
               cCtxM.fillStyle = "#F4F4F4";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,36);
         }
      }

      // second canvas, previous week, 7*24 one-hour entries:
      cData = siteStatusData[sCnt].pweek.split("");
      cDom = document.getElementById('cnvs_' + sName + '_sec2');
      cCtxS = cDom.getContext("2d");
      cDom = document.getElementById('cnvs_' + sName + '_mag2');
      cCtxM = cDom.getContext("2d");
      mData = Math.min(cData.length, 168 );
      for ( var hour=0; hour < mData; hour+=1) {
         xleft = ( hour * noBins[1] ) + Math.trunc(hour/6);
         if ( hour % 24 == 0 ) {
            if ( (dataDay - 8 + Math.trunc(hour/24)) % 7 == 0 ) {
               cCtxS.fillStyle = "#000000";
               cCtxS.fillRect(xleft,0,1,18);
               cCtxM.fillStyle = "#000000";
               cCtxM.fillRect(hour*4+Math.trunc(hour/6)*2,0,2,36);
            } else {
               cCtxS.fillStyle = "#000000";
               cCtxS.fillRect(xleft,4,1,14);
               cCtxM.fillStyle = "#000000";
               cCtxM.fillRect(hour*4+Math.trunc(hour/6)*2,8,2,28);
            }
         } else if ( hour % 6 == 0 ) {
            // 50% tick at the start of a six-hour/quarter-day period
            cCtxS.fillStyle = "#000000";
            cCtxS.fillRect(xleft,9,1,9);
            cCtxM.fillStyle = "#000000";
            cCtxM.fillRect(hour*4+Math.trunc(hour/6)*2,18,2,18);
         }
         switch ( cData[ hour ] ) {
            case "o":
               cCtxS.fillStyle = "#80FF80";
               cCtxS.fillRect(1+xleft,0,noBins[1],18);
               cCtxM.fillStyle = "#80FF80";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            case "w":
               cCtxS.fillStyle = "#FFFF00";
               cCtxS.fillRect(1+xleft,0,noBins[1],18);
               cCtxM.fillStyle = "#FFFF00";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            case "e":
               cCtxS.fillStyle = "#FF0000";
               cCtxS.fillRect(1+xleft,0,noBins[1],18);
               cCtxM.fillStyle = "#FF0000";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            case "p":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[1],6);
               cCtxS.fillRect(1+xleft,12,noBins[1],6);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,12);
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,24,4,12);
               break;
            case "d":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[1],18);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            case "a":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[1],4);
               cCtxS.fillRect(1+xleft,6,noBins[1],2);
               cCtxS.fillRect(1+xleft,10,noBins[1],2);
               cCtxS.fillRect(1+xleft,14,noBins[1],4);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,8);
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,12,4,4);
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,20,4,4);
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,28,4,8);
               break;
            case "U":
               cCtxS.fillStyle = "#80FF80";
               cCtxS.fillRect(1+xleft,0,noBins[1],4);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,4,noBins[1],14);
               cCtxM.fillStyle = "#80FF80";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,8);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,8,4,28);
               break;
            case "V":
               cCtxS.fillStyle = "#FFFF00";
               cCtxS.fillRect(1+xleft,0,noBins[1],4);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,4,noBins[1],14);
               cCtxM.fillStyle = "#FFFF00";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,8);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,8,4,28);
               break;
            case "W":
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,0,noBins[1],18);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            case "X":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[1],4);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,4,noBins[1],14);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,8);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,8,4,28);
               break;
            case "K":
               cCtxS.fillStyle = "#80FF80";
               cCtxS.fillRect(1+xleft,0,noBins[1],2);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,2,noBins[1],16);
               cCtxM.fillStyle = "#80FF80";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,4);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,4,4,32);
               break;
            case "L":
               cCtxS.fillStyle = "#FFFF00";
               cCtxS.fillRect(1+xleft,0,noBins[1],2);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,2,noBins[1],16);
               cCtxM.fillStyle = "#FFFF00";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,4);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,4,4,32);
               break;
            case "M":
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,0,noBins[1],18);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            case "N":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[1],2);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,2,noBins[1],16);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,4);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,4,4,32);
               break;
            default:
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+xleft,0,noBins[1],18);
               cCtxM.fillStyle = "#F4F4F4";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
         }
      }

      // third canvas, previous day, 24*4 quarter-hour entries:
      cData = siteStatusData[sCnt].yesterday.split("");
      cDom = document.getElementById('cnvs_' + sName + '_sec3');
      cCtxS = cDom.getContext("2d");
      cDom = document.getElementById('cnvs_' + sName + '_mag3');
      cCtxM = cDom.getContext("2d");
      mData = Math.min(cData.length, 96 );
      for ( var qhour=0; qhour < mData; qhour+=1) {
         xleft = ( qhour * noBins[2] ) + Math.trunc(qhour/4);
         if ( qhour == 0 ) {
            if ( (dataDay - 1) % 7 == 0 ) {
               cCtxS.fillStyle = "#000000";
               cCtxS.fillRect(xleft,0,1,18);
               cCtxM.fillStyle = "#000000";
               cCtxM.fillRect(qhour*4+Math.trunc(qhour/4)*2,0,2,36);
            } else {
               cCtxS.fillStyle = "#000000";
               cCtxS.fillRect(xleft,4,1,14);
               cCtxM.fillStyle = "#000000";
               cCtxM.fillRect(qhour*4+Math.trunc(qhour/4)*2,8,2,28);
            }
         } else if ( qhour % 24 == 0 ) {
            cCtxS.fillStyle = "#000000";
            cCtxS.fillRect(xleft,9,1,9);
            cCtxM.fillStyle = "#000000";
            cCtxM.fillRect(qhour*4+Math.trunc(qhour/4)*2,18,2,18);
         } else if ( qhour % 4 == 0 ) {
            // 25% tick at the start of an hour
            cCtxS.fillStyle = "#000000";
            cCtxS.fillRect(xleft,14,1,4);
            cCtxM.fillStyle = "#000000";
            cCtxM.fillRect(qhour*4+Math.trunc(qhour/4)*2,28,2,8);
         }
         switch ( cData[ qhour ] ) {
            case "o":
               cCtxS.fillStyle = "#80FF80";
               cCtxS.fillRect(1+xleft,0,noBins[2],18);
               cCtxM.fillStyle = "#80FF80";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
               break;
            case "w":
               cCtxS.fillStyle = "#FFFF00";
               cCtxS.fillRect(1+xleft,0,noBins[2],18);
               cCtxM.fillStyle = "#FFFF00";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
               break;
            case "e":
               cCtxS.fillStyle = "#FF0000";
               cCtxS.fillRect(1+xleft,0,noBins[2],18);
               cCtxM.fillStyle = "#FF0000";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
               break;
            case "p":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[2],6);
               cCtxS.fillRect(1+xleft,12,noBins[2],6);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,12);
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,24,4,12);
               break;
            case "d":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[2],18);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
               break;
            case "a":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[2],4);
               cCtxS.fillRect(1+xleft,6,noBins[2],2);
               cCtxS.fillRect(1+xleft,10,noBins[2],2);
               cCtxS.fillRect(1+xleft,14,noBins[2],4);
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,8);
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,12,4,4);
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,20,4,4);
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,28,4,8);
               break;
            case "U":
               cCtxS.fillStyle = "#80FF80";
               cCtxS.fillRect(1+xleft,0,noBins[2],4);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,4,noBins[2],14);
               cCtxM.fillStyle = "#80FF80";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,8);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,8,4,28);
               break;
            case "V":
               cCtxS.fillStyle = "#FFFF00";
               cCtxS.fillRect(1+xleft,0,noBins[2],4);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,4,noBins[2],14);
               cCtxM.fillStyle = "#FFFF00";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,8);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,8,4,28);
               break;
            case "W":
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,0,noBins[2],18);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
               break;
            case "X":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[2],4);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,4,noBins[2],14);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,8);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,8,4,28);
               break;
            case "K":
               cCtxS.fillStyle = "#80FF80";
               cCtxS.fillRect(1+xleft,0,noBins[2],2);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,2,noBins[2],16);
               cCtxM.fillStyle = "#80FF80";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,4);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,4,4,32);
               break;
            case "L":
               cCtxS.fillStyle = "#FFFF00";
               cCtxS.fillRect(1+xleft,0,noBins[2],2);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,2,noBins[2],16);
               cCtxM.fillStyle = "#FFFF00";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,4);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,4,4,32);
               break;
            case "M":
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,0,noBins[2],18);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
               break;
            case "N":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[2],2);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,2,noBins[2],16);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,4);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,4,4,32);
               break;
            default:
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+xleft,0,noBins[2],18);
               cCtxM.fillStyle = "#F4F4F4";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
         }
      }

      // fourth canvas, today, 24*4 quarter-hour entries:
      cData = siteStatusData[sCnt].today.split("");
      cDom = document.getElementById('cnvs_' + sName + '_sec4');
      cCtxS = cDom.getContext("2d");
      cDom = document.getElementById('cnvs_' + sName + '_mag4');
      cCtxM = cDom.getContext("2d");
      mData = Math.min(cData.length, 96 );
      for ( var qhour=0; qhour < mData; qhour+=1) {
         xleft = ( qhour * noBins[3] ) + Math.trunc(qhour/4);
         if ( qhour == 0 ) {
            if ( dataDay % 7 == 0 ) {
               cCtxS.fillStyle = "#000000";
               cCtxS.fillRect(xleft,0,1,18);
               cCtxM.fillStyle = "#000000";
               cCtxM.fillRect(qhour*5+Math.trunc(qhour/4)*2,0,2,36);
            } else {
               cCtxS.fillStyle = "#000000";
               cCtxS.fillRect(xleft,4,1,14);
               cCtxM.fillStyle = "#000000";
               cCtxM.fillRect(qhour*5+Math.trunc(qhour/4)*2,8,2,28);
            }
         } else if ( qhour % 24 == 0 ) {
            cCtxS.fillStyle = "#000000";
            cCtxS.fillRect(xleft,9,1,9);
            cCtxM.fillStyle = "#000000";
            cCtxM.fillRect(qhour*5+Math.trunc(qhour/4)*2,18,2,18);
         } else if ( qhour % 4 == 0 ) {
            cCtxS.fillStyle = "#000000";
            cCtxS.fillRect(xleft,14,1,4);
            cCtxM.fillStyle = "#000000";
            cCtxM.fillRect(qhour*5+Math.trunc(qhour/4)*2,28,2,8);
         }
         switch ( cData[ qhour ] ) {
            case "o":
               cCtxS.fillStyle = "#80FF80";
               cCtxS.fillRect(1+xleft,0,noBins[3],18);
               cCtxM.fillStyle = "#80FF80";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
               break;
            case "w":
               cCtxS.fillStyle = "#FFFF00";
               cCtxS.fillRect(1+xleft,0,noBins[3],18);
               cCtxM.fillStyle = "#FFFF00";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
               break;
            case "e":
               cCtxS.fillStyle = "#FF0000";
               cCtxS.fillRect(1+xleft,0,noBins[3],18);
               cCtxM.fillStyle = "#FF0000";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
               break;
            case "p":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[3],6);
               cCtxS.fillRect(1+xleft,12,noBins[3],6);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,12);
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,24,5,12);
               break;
            case "d":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[3],18);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
               break;
            case "a":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[3],4);
               cCtxS.fillRect(1+xleft,6,noBins[3],2);
               cCtxS.fillRect(1+xleft,10,noBins[3],2);
               cCtxS.fillRect(1+xleft,14,noBins[3],4);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,8);
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,12,5,4);
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,20,5,4);
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,28,5,8);
               break;
            case "U":
               cCtxS.fillStyle = "#80FF80";
               cCtxS.fillRect(1+xleft,0,noBins[3],4);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,4,noBins[3],14);
               cCtxM.fillStyle = "#80FF80";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,8);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,8,5,28);
               break;
            case "V":
               cCtxS.fillStyle = "#FFFF00";
               cCtxS.fillRect(1+xleft,0,noBins[3],4);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,4,noBins[3],14);
               cCtxM.fillStyle = "#FFFF00";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,8);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,8,5,28);
               break;
            case "W":
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,0,noBins[3],18);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
               break;
            case "X":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[3],4);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,4,noBins[3],14);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,8);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,8,5,28);
               break;
            case "K":
               cCtxS.fillStyle = "#80FF80";
               cCtxS.fillRect(1+xleft,0,noBins[3],2);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,2,noBins[3],16);
               cCtxM.fillStyle = "#80FF80";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,4);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,4,5,32);
               break;
            case "L":
               cCtxS.fillStyle = "#FFFF00";
               cCtxS.fillRect(1+xleft,0,noBins[3],2);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,2,noBins[3],16);
               cCtxM.fillStyle = "#FFFF00";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,4);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,4,5,32);
               break;
            case "M":
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,0,noBins[3],18);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
               break;
            case "N":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[3],2);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,2,noBins[3],16);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,4);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,4,5,32);
               break;
            default:
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+xleft,0,noBins[3],18);
               cCtxM.fillStyle = "#F4F4F4";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
         }
      }

      // fifth canvas, following week, 7*24 one-hour entries:
      cData = siteStatusData[sCnt].fweek.split("");
      cDom = document.getElementById('cnvs_' + sName + '_sec5');
      cCtxS = cDom.getContext("2d");
      cDom = document.getElementById('cnvs_' + sName + '_mag5');
      cCtxM = cDom.getContext("2d");
      mData = Math.min(cData.length, 168 );
      for ( var hour=0; hour < mData; hour+=1) {
         xleft = ( hour * noBins[4] ) + Math.trunc(hour/6);
         if ( hour % 24 == 0 ) {
            if ( (dataDay + 1 + Math.trunc(hour/24)) % 7 == 0 ) {
               cCtxS.fillStyle = "#000000";
               cCtxS.fillRect(xleft,0,1,18);
               cCtxM.fillStyle = "#000000";
               cCtxM.fillRect(hour*4+Math.trunc(hour/6)*2,0,2,36);
            } else {
               cCtxS.fillStyle = "#000000";
               cCtxS.fillRect(xleft,4,1,14);
               cCtxM.fillStyle = "#000000";
               cCtxM.fillRect(hour*4+Math.trunc(hour/6)*2,8,2,28);
            }
         } else if ( hour % 6 == 0 ) {
            // 50% tick at the start of a six-hour/quarter-day period
            cCtxS.fillStyle = "#000000";
            cCtxS.fillRect(xleft,9,1,9);
            cCtxM.fillStyle = "#000000";
            cCtxM.fillRect(hour*4+Math.trunc(hour/6)*2,18,2,18);
         }
         switch ( cData[ hour ] ) {
            case "o":
               cCtxS.fillStyle = "#80FF80";
               cCtxS.fillRect(1+xleft,0,noBins[4],18);
               cCtxM.fillStyle = "#80FF80";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,8,36);
               break;
            case "w":
               cCtxS.fillStyle = "#FFFF00";
               cCtxS.fillRect(1+xleft,0,noBins[4],18);
               cCtxM.fillStyle = "#FFFF00";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,8,36);
               break;
            case "e":
               cCtxS.fillStyle = "#FF0000";
               cCtxS.fillRect(1+xleft,0,noBins[4],18);
               cCtxM.fillStyle = "#FF0000";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,8,36);
               break;
            case "p":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[4],6);
               cCtxS.fillRect(1+xleft,12,noBins[4],6);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,8,12);
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,24,8,12);
               break;
            case "d":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[4],18);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,8,36);
               break;
            case "a":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[4],4);
               cCtxS.fillRect(1+xleft,6,noBins[4],2);
               cCtxS.fillRect(1+xleft,10,noBins[4],2);
               cCtxS.fillRect(1+xleft,14,noBins[4],4);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,8,8);
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,12,8,4);
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,20,8,4);
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,28,8,8);
               break;
            case "U":
            case "V":
            case "W":
            case "X":
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,0,noBins[4],18);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,8,36);
               break;
            case "K":
            case "L":
            case "M":
            case "N":
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,0,noBins[4],18);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,8,36);
               break;
            default:
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+xleft,0,noBins[4],18);
               cCtxM.fillStyle = "#F4F4F4";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,8,36);
         }
      }
   }
}

function fillLegend() {
   var cCtx;

   cCtx = document.getElementById('cnvs_lgn_Ok').getContext('2d');
   cCtx.fillStyle = "#80FF80";
   cCtx.fillRect(0,0,6,18);
   cCtx = document.getElementById('cnvs_lgn_PartDowntime').getContext('2d');
   cCtx.fillStyle = "#6080FF";
   cCtx.fillRect(0,0,6,6);
   cCtx.fillRect(0,12,6,6);
   cCtx = document.getElementById('cnvs_lgn_WaitingRoom').getContext('2d');
   cCtx.fillStyle = "#A000A0";
   cCtx.fillRect(0,0,6,14);
   cCtx = document.getElementById('cnvs_lgn_Warning').getContext('2d');
   cCtx.fillStyle = "#FFFF00";
   cCtx.fillRect(0,0,6,18);
   cCtx = document.getElementById('cnvs_lgn_FullDowntime').getContext('2d');
   cCtx.fillStyle = "#6080FF";
   cCtx.fillRect(0,0,6,18);
   cCtx = document.getElementById('cnvs_lgn_Morgue').getContext('2d');
   cCtx.fillStyle = "#663300";
   cCtx.fillRect(0,0,6,16);
   cCtx = document.getElementById('cnvs_lgn_Error').getContext('2d');
   cCtx.fillStyle = "#FF0000";
   cCtx.fillRect(0,0,6,18);
   cCtx = document.getElementById('cnvs_lgn_AdhocDowntime').getContext('2d');
   cCtx.fillStyle = "#6080FF";
   cCtx.fillRect(0,0,6,4);
   cCtx.fillRect(0,6,6,2);
   cCtx.fillRect(0,10,6,2);
   cCtx.fillRect(0,14,6,4);
   cCtx = document.getElementById('cnvs_lgn_Unknown').getContext('2d');
   cCtx.fillStyle = "#F4F4F4";
   cCtx.fillRect(0,0,6,18);
}
