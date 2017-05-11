/* JavaScript ************************************************************** */
"use strict";



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

   // compose table header:
   var myTableStr = '<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="0">\n<TR' +
      '>\n   <TH NOWRAP ALIGN="left"><BIG><B>Sitename</B></BIG>\n   <TH COLS' +
      'PAN="3" NOWRAP ALIGN="center"><BIG><B>GGUS</B></BIG>\n   <TH NOWRAP A' +
      'LIGN="center"><BIG><B>Previous Month</B></BIG>\n   <TH NOWRAP ALIGN="' +
      'center"><BIG><B>Previous Week</B></BIG>\n   <TH NOWRAP ALIGN="center"' +
      '><BIG><B>Yesterday</B></BIG>\n   <TH NOWRAP ALIGN="center"><BIG><B>UT' +
      'C Today</B></BIG>\n   <TH NOWRAP ALIGN="center"><BIG><B>Following Wee' +
      'k</B></BIG>\n';


   // loop over site summary data and write a table row for each site:
   for ( var sCnt=0; sCnt < siteStatusData.length; sCnt+=1 ) {
      var urlStr;
      var bgcStr, cntStr;

      var sName = siteStatusData[sCnt].site.toString();

      // compose URL for individual site status page:
      urlStr = siteStatusInfo['url'] + 'detail.html?site=' + sName;
      // write first, site name, column:
      myTableStr += '<TR>\n   <TD ALIGN=\"left\"><A HREF=\"' + urlStr +
         '\"><BIG>' + sName + '</BIG></A>\n';

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
         '"><CANVAS ID="cnvs_' + sName + '_sec1" WIDTH="272" HEIGHT="18"></C' +
         'ANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPADDING="0" CELLSPA' +
         'CING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Previous Month of ' +
         sName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSPAN="2"><CANVAS ' +
         'ID="cnvs_' + sName + '_mag1" WIDTH="540" HEIGHT="36"></CANVAS><TR>' +
         '<TD ALIGN="left">' +
         dateString2( siteStatusInfo['time'] - 38 * 86400 ) +
         '<TD ALIGN="right">' +
         dateString2( siteStatusInfo['time'] - 9 * 86400 ) +
         '</TABLE></SPAN></A>\n';

      // compose URL for previous week's site status page:
      urlStr = siteStatusInfo['url'] + 'pweek.html?site=' + sName;
      // write fourth, previous week , column:
      myTableStr += '   <TD><A CLASS="toolTip2" HREF="' + urlStr +
         '"><CANVAS ID="cnvs_' + sName + '_sec2" WIDTH="198" HEIGHT="18"></C' +
         'ANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPADDING="0" CELLSPA' +
         'CING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Previous Week of ' +
         sName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSPAN="2"><CANVAS ' +
         'ID="cnvs_' + sName + '_mag2" WIDTH="728" HEIGHT="36"></CANVAS><TR>' +
         '<TD ALIGN="left">' +
         dateString2( siteStatusInfo['time'] - 8 * 86400 ) +
         '<TD ALIGN="right">' +
         dateString2( siteStatusInfo['time'] - 2 * 86400 ) +
         '</TABLE></SPAN></A>\n';

      // compose URL for yesterday's site status page:
      urlStr = siteStatusInfo['url'] + 'yesterday.html?site=' + sName;
      // write fifth, yesterday, column:
      myTableStr += '   <TD><A CLASS="toolTip3" HREF="' + urlStr +
         '"><CANVAS ID="cnvs_' + sName + '_sec3" WIDTH="218" HEIGHT="18"></C' +
         'ANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPADDING="0" CELLSPA' +
         'CING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Yesterday (' +
         dateString2( siteStatusInfo['time'] - 86400 ) +
         ') of ' + sName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSPAN="2' +
         '"><CANVAS ID="cnvs_' + sName + '_mag3" WIDTH="432" HEIGHT="36"></C' +
         'ANVAS><TR><TD ALIGN="left">00:00<TD ALIGN="right">24:00</TABLE></S' +
         'PAN></A>\n';

      // compose URL for today's site status page:
      urlStr = siteStatusInfo['url'] + 'today.html?site=' + sName;
      // write sixth, today, column:
      myTableStr += '   <TD><A CLASS="toolTip4" HREF="' + urlStr +
         '"><CANVAS ID="cnvs_' + sName + '_sec4" WIDTH="314" HEIGHT="18"></C' +
         'ANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPADDING="0" CELLSPA' +
         'CING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Today (' + 
         dateString2( siteStatusInfo['time'] ) +
         ') of ' + sName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSPAN="2' +
         '"><CANVAS ID="cnvs_' + sName + '_mag4" WIDTH="528" HEIGHT="36"></C' +
         'ANVAS><TR><TD ALIGN="left">00:00<TD ALIGN="right">24:00</TABLE></S' +
         'PAN></A>\n';

      // compose URL for following week's site status page:
      urlStr = siteStatusInfo['url'] + 'fweek.html?site=' + sName;
      // write seventh, following week, column:
      myTableStr += '   <TD><A CLASS="toolTip5" HREF="' + urlStr +
         '"><CANVAS ID="cnvs_' + sName + '_sec5" WIDTH="198" HEIGHT="18"></C' +
         'ANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPADDING="0" CELLSPA' +
         'CING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Following Week of ' +
         sName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSPAN="2"><CANVAS ' +
         'ID="cnvs_' + sName + '_mag5" WIDTH="728" HEIGHT="36"></CANVAS><TR>' +
         '<TD ALIGN="left">' +
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
      var cCtx;
      var mData;

      var sName = siteStatusData[sCnt].site.toString();

      // first canvas, previous month, 120 six-hour/quarter-day entries:
      cData = siteStatusData[sCnt].pmonth.split("");
      cDom = document.getElementById('cnvs_' + sName + '_sec1');
      cCtx = cDom.getContext("2d");
      mData = Math.min(cData.length, cDom.width / 2.25 );
      for ( var qday=0; qday < mData; qday+=1) {
         if ( qday % 4 == 0 ) {
            if ( (dataDay - 38 + Math.trunc(qday/4)) % 7 == 0 ) {
               // full scale tick at the start of the week, Sunday-to-Monday
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(qday*2+Math.trunc(qday/4),0,1,18);
            } else {
               // 75% tick at the start of a day
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(qday*2+Math.trunc(qday/4),4,1,14);
            }
         }
         switch ( cData[ qday ] ) {
            case "o":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(1+qday*2+Math.trunc(qday/4),0,2,18);
               break;
            case "w":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(1+qday*2+Math.trunc(qday/4),0,2,18);
               break;
            case "e":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(1+qday*2+Math.trunc(qday/4),0,2,18);
               break;
            case "p":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(1+qday*2+Math.trunc(qday/4),0,2,6);
               cCtx.fillRect(1+qday*2+Math.trunc(qday/4),12,2,6);
               break;
            case "d":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(1+qday*2+Math.trunc(qday/4),0,2,18);
               break;
            case "a":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(1+qday*2+Math.trunc(qday/4),0,2,4);
               cCtx.fillRect(1+qday*2+Math.trunc(qday/4),6,2,2);
               cCtx.fillRect(1+qday*2+Math.trunc(qday/4),10,2,2);
               cCtx.fillRect(1+qday*2+Math.trunc(qday/4),14,2,4);
               break;
            case "W":
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(1+qday*2+Math.trunc(qday/4),0,2,18);
               break;
            case "M":
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(1+qday*2+Math.trunc(qday/4),0,2,18);
               break;
            default:
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(1+qday*2+Math.trunc(qday/4),0,2,18);
         }
      }

      // second canvas, previous week, 7*24 one-hour entries:
      cData = siteStatusData[sCnt].pweek.split("");
      cDom = document.getElementById('cnvs_' + sName + '_sec2');
      cCtx = cDom.getContext("2d");
      mData = Math.min(cData.length, cDom.width / 1.166 );
      for ( var hour=0; hour < mData; hour+=1) {
         if ( hour % 24 == 0 ) {
            if ( (dataDay - 8 + Math.trunc(hour/24)) % 7 == 0 ) {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(hour+Math.trunc(hour/6),0,1,18);
            } else {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(hour+Math.trunc(hour/6),4,1,14);
            }
         } else if ( hour % 6 == 0 ) {
            // 50% tick at the start of a six-hour/quarter-day period
            cCtx.fillStyle = "#000000";
            cCtx.fillRect(hour+Math.trunc(hour/6),9,1,9);
         }
         switch ( cData[ hour ] ) {
            case "o":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(1+hour+Math.trunc(hour/6),0,1,18);
               break;
            case "w":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(1+hour+Math.trunc(hour/6),0,1,18);
               break;
            case "e":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(1+hour+Math.trunc(hour/6),0,1,18);
               break;
            case "p":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(1+hour+Math.trunc(hour/6),0,1,6);
               cCtx.fillRect(1+hour+Math.trunc(hour/6),12,1,6);
               break;
            case "d":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(1+hour+Math.trunc(hour/6),0,1,18);
               break;
            case "a":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(1+hour+Math.trunc(hour/6),0,1,4);
               cCtx.fillRect(1+hour+Math.trunc(hour/6),6,1,2);
               cCtx.fillRect(1+hour+Math.trunc(hour/6),10,1,2);
               cCtx.fillRect(1+hour+Math.trunc(hour/6),14,1,4);
               break;
            case "W":
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(1+hour+Math.trunc(hour/6),0,1,18);
               break;
            case "M":
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(1+hour+Math.trunc(hour/6),0,1,18);
               break;
            default:
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(1+hour+Math.trunc(hour/6),0,1,18);
         }
      }

      // third canvas, previous day, 24*4 quarter-hour entries:
      cData = siteStatusData[sCnt].yesterday.split("");
      cDom = document.getElementById('cnvs_' + sName + '_sec3');
      cCtx = cDom.getContext("2d");
      mData = Math.min(cData.length, cDom.width / 2.25 );
      for ( var qhour=0; qhour < mData; qhour+=1) {
         if ( qhour == 0 ) {
            if ( (dataDay - 1) % 7 == 0 ) {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(qhour*2+Math.trunc(qhour/4),0,1,18);
            } else {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(qhour*2+Math.trunc(qhour/4),4,1,14);
            }
         } else if ( qhour % 24 == 0 ) {
            cCtx.fillStyle = "#000000";
            cCtx.fillRect(qhour*2+Math.trunc(qhour/4),9,1,9);
         } else if ( qhour % 4 == 0 ) {
            // 25% tick at the start of an hour
            cCtx.fillStyle = "#000000";
            cCtx.fillRect(qhour*2+Math.trunc(qhour/4),14,1,4);
         }
         switch ( cData[ qhour ] ) {
            case "o":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(1+qhour*2+Math.trunc(qhour/4),0,2,18);
               break;
            case "w":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(1+qhour*2+Math.trunc(qhour/4),0,2,18);
               break;
            case "e":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(1+qhour*2+Math.trunc(qhour/4),0,2,18);
               break;
            case "p":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(1+qhour*2+Math.trunc(qhour/4),0,2,6);
               cCtx.fillRect(1+qhour*2+Math.trunc(qhour/4),12,2,6);
               break;
            case "d":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(1+qhour*2+Math.trunc(qhour/4),0,2,18);
               break;
            case "a":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(1+qhour*2+Math.trunc(qhour/4),0,2,4);
               cCtx.fillRect(1+qhour*2+Math.trunc(qhour/4),6,2,2);
               cCtx.fillRect(1+qhour*2+Math.trunc(qhour/4),10,2,2);
               cCtx.fillRect(1+qhour*2+Math.trunc(qhour/4),14,2,4);
               break;
            case "W":
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(1+qhour*2+Math.trunc(qhour/4),0,2,18);
               break;
            case "M":
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(1+qhour*2+Math.trunc(qhour/4),0,2,18);
               break;
            default:
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(1+qhour*2+Math.trunc(qhour/4),0,2,18);
         }
      }

      // fourth canvas, today, 24*4 quarter-hour entries:
      cData = siteStatusData[sCnt].today.split("");
      cDom = document.getElementById('cnvs_' + sName + '_sec4');
      cCtx = cDom.getContext("2d");
      mData = Math.min(cData.length, cDom.width / 3.25 );
      for ( var qhour=0; qhour < mData; qhour+=1) {
         if ( qhour == 0 ) {
            if ( dataDay % 7 == 0 ) {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(qhour*3+Math.trunc(qhour/4),0,1,18);
            } else {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(qhour*3+Math.trunc(qhour/4),4,1,14);
            }
         } else if ( qhour % 24 == 0 ) {
            cCtx.fillStyle = "#000000";
            cCtx.fillRect(qhour*3+Math.trunc(qhour/4),9,1,9);
         } else if ( qhour % 4 == 0 ) {
            cCtx.fillStyle = "#000000";
            cCtx.fillRect(qhour*3+Math.trunc(qhour/4),14,1,4);
         }
         switch ( cData[ qhour ] ) {
            case "o":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(1+qhour*3+Math.trunc(qhour/4),0,3,18);
               break;
            case "w":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(1+qhour*3+Math.trunc(qhour/4),0,3,18);
               break;
            case "e":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(1+qhour*3+Math.trunc(qhour/4),0,3,18);
               break;
            case "p":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(1+qhour*3+Math.trunc(qhour/4),0,3,6);
               cCtx.fillRect(1+qhour*3+Math.trunc(qhour/4),12,3,6);
               break;
            case "d":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(1+qhour*3+Math.trunc(qhour/4),0,3,18);
               break;
            case "a":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(1+qhour*3+Math.trunc(qhour/4),0,3,4);
               cCtx.fillRect(1+qhour*3+Math.trunc(qhour/4),6,3,2);
               cCtx.fillRect(1+qhour*3+Math.trunc(qhour/4),10,3,2);
               cCtx.fillRect(1+qhour*3+Math.trunc(qhour/4),14,3,4);
               break;
            case "W":
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(1+qhour*3+Math.trunc(qhour/4),0,3,18);
               break;
            case "M":
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(1+qhour*3+Math.trunc(qhour/4),0,3,18);
               break;
            default:
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(1+qhour*3+Math.trunc(qhour/4),0,3,18);
         }
      }

      // fifth canvas, following week, 7*24 one-hour entries:
      cData = siteStatusData[sCnt].fweek.split("");
      cDom = document.getElementById('cnvs_' + sName + '_sec5');
      cCtx = cDom.getContext("2d");
      mData = Math.min(cData.length, cDom.width / 1.166 );
      for ( var hour=0; hour < mData; hour+=1) {
         if ( hour % 24 == 0 ) {
            if ( (dataDay + 1 + Math.trunc(hour/24)) % 7 == 0 ) {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(hour+Math.trunc(hour/6),0,1,18);
            } else {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(hour+Math.trunc(hour/6),4,1,14);
            }
         } else if ( hour % 6 == 0 ) {
            // 50% tick at the start of a six-hour/quarter-day period
            cCtx.fillStyle = "#000000";
            cCtx.fillRect(hour+Math.trunc(hour/6),9,1,9);
         }
         switch ( cData[ hour ] ) {
            case "o":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(1+hour+Math.trunc(hour/6),0,4,18);
               break;
            case "w":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(1+hour+Math.trunc(hour/6),0,4,18);
               break;
            case "e":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(1+hour+Math.trunc(hour/6),0,4,18);
               break;
            case "p":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(1+hour+Math.trunc(hour/6),0,4,6);
               cCtx.fillRect(1+hour+Math.trunc(hour/6),12,4,6);
               break;
            case "d":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(1+hour+Math.trunc(hour/6),0,4,18);
               break;
            case "a":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(1+hour+Math.trunc(hour/6),0,4,4);
               cCtx.fillRect(1+hour+Math.trunc(hour/6),6,4,2);
               cCtx.fillRect(1+hour+Math.trunc(hour/6),10,4,2);
               cCtx.fillRect(1+hour+Math.trunc(hour/6),14,4,4);
               break;
            case "W":
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(1+hour+Math.trunc(hour/6),0,4,18);
               break;
            case "M":
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(1+hour+Math.trunc(hour/6),0,4,18);
               break;
            default:
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(1+hour+Math.trunc(hour/6),0,4,18);
         }
      }
   }
}

function fillMagCanvases() {

   // for the tic length we need to know the weekday:
   var dataDay  = ( new Date(siteStatusInfo['time'] * 1000) ).getDay();

   // loop over site summary data and fill the six magnification canvases:
   for ( var sCnt=0; sCnt < siteStatusData.length; sCnt+=1 ) {
      var cData;
      var cDom;
      var cCtx;
      var mData;

      var sName = siteStatusData[sCnt].site.toString();

      // first canvas, previous month, 120 six-hour/quarter-day entries:
      cData = siteStatusData[sCnt].pmonth.split("");
      cDom = document.getElementById('cnvs_' + sName + '_mag1');
      cCtx = cDom.getContext("2d");
      mData = Math.min(cData.length, cDom.width / 4.5 );
      for ( var qday=0; qday < mData; qday+=1) {
         if ( qday % 4 == 0 ) {
            if ( (dataDay - 38 + Math.trunc(qday/4)) % 7 == 0 ) {
               // full scale tick at the start of the week, Sunday-to-Monday
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(qday*4+Math.trunc(qday/4)*2,0,2,36);
            } else {
               // 75% tick at the start of a day
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(qday*4+Math.trunc(qday/4)*2,8,2,28);
            }
         }
         switch ( cData[ qday ] ) {
            case "o":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,36);
               break;
            case "w":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,36);
               break;
            case "e":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,36);
               break;
            case "p":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,12);
               cCtx.fillRect(2+qday*4+Math.trunc(qday/4)*2,24,4,12);
               break;
            case "d":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,36);
               break;
            case "a":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,8);
               cCtx.fillRect(2+qday*4+Math.trunc(qday/4)*2,12,4,4);
               cCtx.fillRect(2+qday*4+Math.trunc(qday/4)*2,20,4,4);
               cCtx.fillRect(2+qday*4+Math.trunc(qday/4)*2,28,4,8);
               break;
            case "W":
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,36);
               break;
            case "M":
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,36);
               break;
            default:
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,36);
         }
      }

      // second canvas, previous week, 7*24 one-hour entries:
      cData = siteStatusData[sCnt].pweek.split("");
      cDom = document.getElementById('cnvs_' + sName + '_mag2');
      cCtx = cDom.getContext("2d");
      mData = Math.min(cData.length, cDom.width / 4.333 );
      for ( var hour=0; hour < mData; hour+=1) {
         if ( hour % 24 == 0 ) {
            if ( (dataDay - 8 + Math.trunc(hour/24)) % 7 == 0 ) {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(hour*4+Math.trunc(hour/6)*2,0,2,36);
            } else {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(hour*4+Math.trunc(hour/6)*2,8,2,28);
            }
         } else if ( hour % 6 == 0 ) {
            // 50% tick at the start of a six-hour/quarter-day period
            cCtx.fillStyle = "#000000";
            cCtx.fillRect(hour*4+Math.trunc(hour/6)*2,18,2,18);
         }
         switch ( cData[ hour ] ) {
            case "o":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            case "w":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            case "e":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            case "p":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,12);
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,24,4,12);
               break;
            case "d":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            case "a":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,8);
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,12,4,4);
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,20,4,4);
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,28,4,8);
               break;
            case "W":
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            case "M":
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            default:
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
         }
      }

      // third canvas, previous day, 24*4 quarter-hour entries:
      cData = siteStatusData[sCnt].yesterday.split("");
      cDom = document.getElementById('cnvs_' + sName + '_mag3');
      cCtx = cDom.getContext("2d");
      mData = Math.min(cData.length, cDom.width / 4.5 );
      for ( var qhour=0; qhour < mData; qhour+=1) {
         if ( qhour == 0 ) {
            if ( (dataDay - 1) % 7 == 0 ) {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(qhour*4+Math.trunc(qhour/4)*2,0,2,36);
            } else {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(qhour*4+Math.trunc(qhour/4)*2,8,2,28);
            }
         } else if ( qhour % 24 == 0 ) {
            cCtx.fillStyle = "#000000";
            cCtx.fillRect(qhour*4+Math.trunc(qhour/4)*2,18,2,18);
         } else if ( qhour % 4 == 0 ) {
            // 25% tick at the start of an hour
            cCtx.fillStyle = "#000000";
            cCtx.fillRect(qhour*4+Math.trunc(qhour/4)*2,28,2,8);
         }
         switch ( cData[ qhour ] ) {
            case "o":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
               break;
            case "w":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
               break;
            case "e":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
               break;
            case "p":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,12);
               cCtx.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,24,4,12);
               break;
            case "d":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
               break;
            case "a":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,8);
               cCtx.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,12,4,4);
               cCtx.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,20,4,4);
               cCtx.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,28,4,8);
               break;
            case "W":
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
               break;
            case "M":
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
               break;
            default:
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
         }
      }

      // fourth canvas, today, 24*4 quarter-hour entries:
      cData = siteStatusData[sCnt].today.split("");
      cDom = document.getElementById('cnvs_' + sName + '_mag4');
      cCtx = cDom.getContext("2d");
      mData = Math.min(cData.length, cDom.width / 5.5 );
      for ( var qhour=0; qhour < mData; qhour+=1) {
         if ( qhour == 0 ) {
            if ( dataDay % 7 == 0 ) {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(qhour*5+Math.trunc(qhour/4)*2,0,2,36);
            } else {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(qhour*5+Math.trunc(qhour/4)*2,8,2,28);
            }
         } else if ( qhour % 24 == 0 ) {
            cCtx.fillStyle = "#000000";
            cCtx.fillRect(qhour*5+Math.trunc(qhour/4)*2,18,2,18);
         } else if ( qhour % 4 == 0 ) {
            cCtx.fillStyle = "#000000";
            cCtx.fillRect(qhour*5+Math.trunc(qhour/4)*2,28,2,8);
         }
         switch ( cData[ qhour ] ) {
            case "o":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
               break;
            case "w":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
               break;
            case "e":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
               break;
            case "p":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,12);
               cCtx.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,24,5,12);
               break;
            case "d":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
               break;
            case "a":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,8);
               cCtx.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,12,5,4);
               cCtx.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,20,5,4);
               cCtx.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,28,5,8);
               break;
            case "W":
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
               break;
            case "M":
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
               break;
            default:
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
         }
      }

      // fifth canvas, following week, 7*24 one-hour entries:
      cData = siteStatusData[sCnt].fweek.split("");
      cDom = document.getElementById('cnvs_' + sName + '_mag5');
      cCtx = cDom.getContext("2d");
      mData = Math.min(cData.length, cDom.width / 4.333 );
      for ( var hour=0; hour < mData; hour+=1) {
         if ( hour % 24 == 0 ) {
            if ( (dataDay + 1 + Math.trunc(hour/24)) % 7 == 0 ) {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(hour*4+Math.trunc(hour/6)*2,0,2,36);
            } else {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(hour*4+Math.trunc(hour/6)*2,8,2,28);
            }
         } else if ( hour % 6 == 0 ) {
            // 50% tick at the start of a six-hour/quarter-day period
            cCtx.fillStyle = "#000000";
            cCtx.fillRect(hour*4+Math.trunc(hour/6)*2,18,2,18);
         }
         switch ( cData[ hour ] ) {
            case "o":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,8,36);
               break;
            case "w":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,8,36);
               break;
            case "e":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,8,36);
               break;
            case "p":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,8,12);
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,24,8,12);
               break;
            case "d":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,8,36);
               break;
            case "a":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,8,8);
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,12,8,4);
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,20,8,4);
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,28,8,8);
               break;
            case "W":
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,8,36);
               break;
            case "M":
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,8,36);
               break;
            default:
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,8,36);
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
   cCtx.fillRect(0,0,6,18);
   cCtx = document.getElementById('cnvs_lgn_Warning').getContext('2d');
   cCtx.fillStyle = "#FFFF00";
   cCtx.fillRect(0,0,6,18);
   cCtx = document.getElementById('cnvs_lgn_FullDowntime').getContext('2d');
   cCtx.fillStyle = "#6080FF";
   cCtx.fillRect(0,0,6,18);
   cCtx = document.getElementById('cnvs_lgn_Morgue').getContext('2d');
   cCtx.fillStyle = "#663300";
   cCtx.fillRect(0,0,6,18);
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

function fillDowntimeLegend() {
   var cCtx;

   cCtx = document.getElementById('cnvs_lgn_FullDowntime').getContext('2d');
   cCtx.fillStyle = "#6080FF";
   cCtx.fillRect(0,0,6,18);
   cCtx = document.getElementById('cnvs_lgn_PartDowntime').getContext('2d');
   cCtx.fillStyle = "#6080FF";
   cCtx.fillRect(0,0,6,6);
   cCtx.fillRect(0,12,6,6);
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
