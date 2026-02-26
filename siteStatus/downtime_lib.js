/* JavaScript ************************************************************** */
"use strict";



/* ************************************************************************* */
/* data:                                                                     */
/* ************************************************************************* */
var siteMetricLabel = { Downtime:         "Downtime(s)",
                        wlcgSAMdowntime:  "SAM Downtime(s)" };
var siteMetricOrder = [ "Downtime",
                        "***LINE***",
                        "**Elmnts**" ];



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

   // add a line in case there is a message:
   if ( siteStatusInfo['msg'] != '' ) {
      var myTableStr = '<SPAN STYLE="color:blue; font-weight:bold;">' +
                          siteStatusInfo['msg'] + '</SPAN>\n<BR>\n<BR>\n';
   } else {
      var myTableStr = ''
   }

   // compose table header:
   myTableStr += '<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="0">\n<TR>\n' +
      '   <TH NOWRAP ALIGN="left"><BIG><B>Sitename</B></BIG>\n   <TH COLSPAN' +
      '="3" NOWRAP ALIGN="center"><BIG><B>GGUS</B></BIG>\n   <TH NOWRAP ALIG' +
      'N="center"><BIG><B>Previous Week</B></BIG>\n   <TH NOWRAP ALIGN="cent' +
      'er"><BIG><B>Yesterday</B></BIG>\n   <TH NOWRAP ALIGN="center" BGCOLOR' +
      '="#FFFF50"><BIG><B>UTC Today</B></BIG>\n   <TH NOWRAP ALIGN="center">' +
      '<BIG><B>Following Week</B></BIG>\n';


   // loop over site summary data and write a table row for each site:
   for ( var sCnt=0; sCnt < siteStatusData.length; sCnt+=1 ) {
      var urlStr;
      var bgcStr, cntStr;

      var sName = siteStatusData[sCnt].site.toString();

      // compose URL for individual site status page:
      // write first, site name, column:
      myTableStr += '<TR>\n   <TD ALIGN=\"left\"><BIG>' + sName + '</BIG>\n';

      // compose URL for GGUS site-tickets-of-CMS search:
      urlStr = 'https://helpdesk.ggus.eu/#search/cms_site_names%3A' + sName +
         '%20AND%20!((state.name%3Asolved)%20OR%20(state.name%3Aunsolved)%20' +
         'OR%20(state.name%3Aclosed)%20OR%20(state.name%3Averified))';
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

      // write fourth, previous week , column:
      myTableStr += '   <TD><A CLASS="toolTip2"><CANVAS ID="cnvs_' + sName +
         '_sec2" WIDTH="198" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" ' +
         'BORDER="0" CELLPADDING="0" CELLSPACING="0"><TR><TD COLSPAN="2" ALI' +
         'GN="center"><B>Previous Week of ' + sName + '</B><TR><TD COLSPAN="' +
         '2">&nbsp;<TR><TD COLSPAN="2"><CANVAS ID="cnvs_' + sName +
         '_mag2" WIDTH="728" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">' +
         dateString2( siteStatusInfo['time'] - 8 * 86400 ) +
         '<TD ALIGN="right">' +
         dateString2( siteStatusInfo['time'] - 2 * 86400 ) +
         '</TABLE></SPAN></A>\n';

      // compose URL for yesterday's site status page:
      // write fifth, yesterday, column:
      myTableStr += '   <TD><A CLASS="toolTip3"><CANVAS ID="cnvs_' + sName +
         '_sec3" WIDTH="218" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" ' +
         'BORDER="0" CELLPADDING="0" CELLSPACING="0"><TR><TD COLSPAN="2" ALI' +
         'GN="center"><B>Yesterday (' +
         dateString2( siteStatusInfo['time'] - 86400 ) +
         ') of ' + sName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSPAN="2' +
         '"><CANVAS ID="cnvs_' + sName + '_mag3" WIDTH="432" HEIGHT="36"></C' +
         'ANVAS><TR><TD ALIGN="left">00:00<TD ALIGN="right">24:00</TABLE></S' +
         'PAN></A>\n';

      // compose URL for today's site status page:
      urlStr = siteStatusInfo['url'] + 'downtoday.html?site=' + sName;
      // write sixth, today, column:
      myTableStr += '   <TD BGCOLOR="#FFFF50"><A CLASS="toolTip4" HREF="' +
         urlStr + '"><CANVAS ID="cnvs_' + sName + '_sec4" WIDTH="314" HEIGHT' +
         '="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPADDING="0' +
         '" CELLSPACING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Today (' + 
         dateString2( siteStatusInfo['time'] ) +
         ') of ' + sName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSPAN="2' +
         '"><CANVAS ID="cnvs_' + sName + '_mag4" WIDTH="528" HEIGHT="36"></C' +
         'ANVAS><TR><TD ALIGN="left">00:00<TD ALIGN="right">24:00</TABLE></S' +
         'PAN></A>\n';

      // compose URL for following week's site status page:
      // write seventh, following week, column:
      myTableStr += '   <TD><A CLASS="toolTip5"><CANVAS ID="cnvs_' + sName +
         '_sec5" WIDTH="198" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" ' +
         'BORDER="0" CELLPADDING="0" CELLSPACING="0"><TR><TD COLSPAN="2" ALI' +
         'GN="center"><B>Following Week of ' + sName + '</B><TR><TD COLSPAN=' +
         '"2">&nbsp;<TR><TD COLSPAN="2"><CANVAS ID="cnvs_' + sName +
         '_mag5" WIDTH="728" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">' +
         dateString2( siteStatusInfo['time'] + 1 * 86400 ) +
         '<TD ALIGN="right">' +
         dateString2( siteStatusInfo['time'] + 7 * 86400 ) +
         '</TABLE></SPAN></A>\n';
   }


   // compose table trailer:
   myTableStr += '</TABLE>\n';


   // update main DIV section with table:
   document.getElementById("mainDIV").innerHTML = myTableStr;
}

function writeTodayTable() {

   // add a line in case there is a message:
   if ( myData.msg != '' ) {
      var myTableStr = '<SPAN STYLE="color:blue; font-weight:bold;">' +
                          myData.msg + '</SPAN>\n<BR>\n<BR>\n';
   } else {
      var myTableStr = ''
   }

   // compose table header:
   myTableStr += '<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="0">\n<TR>\n' +
      '   <TH NOWRAP ALIGN="left"><BIG><B>Metric</B></BIG>\n   <TH NOWRAP><B' +
      'IG>&nbsp;</BIG>\n   <TH NOWRAP ALIGN="left"><BIG><B>00:00</B></BIG>\n' +
      '   <TH NOWRAP ALIGN="center"><BIG><B>UTC Today</B></BIG>\n   <TH NOWR' +
      'AP ALIGN="right"><BIG><B>24:00</B></BIG>\n';


   // loop over metrics in siteMetricOrder and write a table row for each:
   for ( var mCnt=0; mCnt < siteMetricOrder.length; mCnt+=1 ) {
      if ( siteMetricOrder[mCnt] == "***LINE***" ) {
         myTableStr += '<TR>\n   <TD COLSPAN="5" bgcolor="#000000" STYLE="li' +
            'ne-height:2px;">&nbsp;\n<TR>\n   <TD COLSPAN="5" bgcolor="#FFFF' +
            'FF" STYLE="line-height:2px;">&nbsp;\n';
      } else if ( siteMetricOrder[mCnt] in myData.metrics ) {
         var nName = siteMetricOrder[mCnt];
         if ( siteMetricOrder[mCnt] in siteMetricLabel ) {
            nName = siteMetricLabel[siteMetricOrder[mCnt]];
         }
         myTableStr += '<TR>\n   <TD NOWRAP ALIGN="left">' + nName + '\n   <' +
            'TD NOWRAP>&nbsp;\n';
         var urlStr = "";
         myTableStr += '   <TD COLSPAN="3"><CANVAS ID="cnvs_' +
            siteMetricOrder[mCnt] + '_s4" WIDTH="626" HEIGHT="18">' +
            '</CANVAS>\n';
      } else if ( siteMetricOrder[mCnt] == "**Elmnts**" ) {
         // loop over site elements and write the metrics of each:
         for ( var cnt=0; cnt < myData.elements.length; cnt+=1 ) {
            // concatenate host and type excluding domain
            var indx = myData.elements[cnt].host.indexOf('.');
            if ( indx <= 0 ) {
               indx = myData.elements[cnt].host.length;
            }
            var lName = myData.elements[cnt].host.substring(0,indx) + ' / ' +
               myData.elements[cnt].type;

            myTableStr += '<TR>\n   <TD COLSPAN="5" bgcolor="#000000" STYLE=' +
               '"line-height:2px;">&nbsp;\n<TR>\n   <TD COLSPAN="5" bgcolor=' +
               '"#FFFFFF" STYLE="line-height:8px;">&nbsp;\n<TR>\n';
            var eName = myData.elements[cnt].host + '/' +
               myData.elements[cnt].type;
            eName = eName.replace(' ', '');
            // loop over metrics of element:
            for ( var mName in myData.elements[cnt].metrics ) {
               if ( mName =="Downtime" ) {
                  myTableStr += '<TR>\n   <TD NOWRAP ALIGN="left"> &nbsp &nb' +
                     'sp ' + lName + '\n   <TD NOWRAP>&nbsp;\n';
                  myTableStr += '   <TD COLSPAN="3"><CANVAS ID="cnvs_' +
                     eName + '_' + mName + '_s4" WIDTH="626" HEIGHT="18">' +
                     '</CANVAS>\n';
               }
            }
         }
      }
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

function updateTodayTimestamps() {

   document.getElementById("titleSPAN").innerHTML = myData.site + ' Site Dow' +
      'ntime Detail<BR>(' + dateString1( myData.time ) + ' GMT)';

   var timeObj = new Date( myData.time * 1000 );
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

      var sName = siteStatusData[sCnt].site.toString();

      // second canvas, previous week, 7*24 one-hour entries:
      cData = siteStatusData[sCnt].pweek.split("");
      cDom = document.getElementById('cnvs_' + sName + '_sec2');
      cCtxS = cDom.getContext("2d");
      cDom = document.getElementById('cnvs_' + sName + '_mag2');
      cCtxM = cDom.getContext("2d");
      mData = Math.min(cData.length, 168 );
      for ( var hour=0; hour < mData; hour+=1) {
         if ( hour % 24 == 0 ) {
            if ( (dataDay - 8 + Math.trunc(hour/24)) % 7 == 0 ) {
               cCtxS.fillStyle = "#000000";
               cCtxS.fillRect(hour+Math.trunc(hour/6),0,1,18);
               cCtxM.fillStyle = "#000000";
               cCtxM.fillRect(hour*4+Math.trunc(hour/6)*2,0,2,36);
            } else {
               cCtxS.fillStyle = "#000000";
               cCtxS.fillRect(hour+Math.trunc(hour/6),4,1,14);
               cCtxM.fillStyle = "#000000";
               cCtxM.fillRect(hour*4+Math.trunc(hour/6)*2,8,2,28);
            }
         } else if ( hour % 6 == 0 ) {
            // 50% tick at the start of a six-hour/quarter-day period
            cCtxS.fillStyle = "#000000";
            cCtxS.fillRect(hour+Math.trunc(hour/6),9,1,9);
            cCtxM.fillStyle = "#000000";
            cCtxM.fillRect(hour*4+Math.trunc(hour/6)*2,18,2,18);
         }
         switch ( cData[ hour ] ) {
            case "p":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+hour+Math.trunc(hour/6),0,1,6);
               cCtxS.fillRect(1+hour+Math.trunc(hour/6),12,1,6);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,12);
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,24,4,12);
               break;
            case "d":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+hour+Math.trunc(hour/6),0,1,18);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            case "a":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+hour+Math.trunc(hour/6),0,1,4);
               cCtxS.fillRect(1+hour+Math.trunc(hour/6),6,1,2);
               cCtxS.fillRect(1+hour+Math.trunc(hour/6),10,1,2);
               cCtxS.fillRect(1+hour+Math.trunc(hour/6),14,1,4);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,8);
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,12,4,4);
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,20,4,4);
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,28,4,8);
               break;
            case "r":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+hour+Math.trunc(hour/6),7,1,4);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,14,4,8);
               break;
            default:
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+hour+Math.trunc(hour/6),0,1,18);
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
         if ( qhour == 0 ) {
            if ( (dataDay - 1) % 7 == 0 ) {
               cCtxS.fillStyle = "#000000";
               cCtxS.fillRect(qhour*2+Math.trunc(qhour/4),0,1,18);
               cCtxM.fillStyle = "#000000";
               cCtxM.fillRect(qhour*4+Math.trunc(qhour/4)*2,0,2,36);
            } else {
               cCtxS.fillStyle = "#000000";
               cCtxS.fillRect(qhour*2+Math.trunc(qhour/4),4,1,14);
               cCtxM.fillStyle = "#000000";
               cCtxM.fillRect(qhour*4+Math.trunc(qhour/4)*2,8,2,28);
            }
         } else if ( qhour % 24 == 0 ) {
            cCtxS.fillStyle = "#000000";
            cCtxS.fillRect(qhour*2+Math.trunc(qhour/4),9,1,9);
            cCtxM.fillStyle = "#000000";
            cCtxM.fillRect(qhour*4+Math.trunc(qhour/4)*2,18,2,18);
         } else if ( qhour % 4 == 0 ) {
            // 25% tick at the start of an hour
            cCtxS.fillStyle = "#000000";
            cCtxS.fillRect(qhour*2+Math.trunc(qhour/4),14,1,4);
            cCtxM.fillStyle = "#000000";
            cCtxM.fillRect(qhour*4+Math.trunc(qhour/4)*2,28,2,8);
         }
         switch ( cData[ qhour ] ) {
            case "p":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+qhour*2+Math.trunc(qhour/4),0,2,6);
               cCtxS.fillRect(1+qhour*2+Math.trunc(qhour/4),12,2,6);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,12);
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,24,4,12);
               break;
            case "d":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+qhour*2+Math.trunc(qhour/4),0,2,18);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
               break;
            case "a":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+qhour*2+Math.trunc(qhour/4),0,2,4);
               cCtxS.fillRect(1+qhour*2+Math.trunc(qhour/4),6,2,2);
               cCtxS.fillRect(1+qhour*2+Math.trunc(qhour/4),10,2,2);
               cCtxS.fillRect(1+qhour*2+Math.trunc(qhour/4),14,2,4);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,8);
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,12,4,4);
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,20,4,4);
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,28,4,8);
               break;
            case "r":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+qhour*2+Math.trunc(qhour/4),7,2,4);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,14,4,8);
               break;
            default:
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+qhour*2+Math.trunc(qhour/4),0,2,18);
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
         if ( qhour == 0 ) {
            if ( dataDay % 7 == 0 ) {
               cCtxS.fillStyle = "#000000";
               cCtxS.fillRect(qhour*3+Math.trunc(qhour/4),0,1,18);
               cCtxM.fillStyle = "#000000";
               cCtxM.fillRect(qhour*5+Math.trunc(qhour/4)*2,0,2,36);
            } else {
               cCtxS.fillStyle = "#000000";
               cCtxS.fillRect(qhour*3+Math.trunc(qhour/4),4,1,14);
               cCtxM.fillStyle = "#000000";
               cCtxM.fillRect(qhour*5+Math.trunc(qhour/4)*2,8,2,28);
            }
         } else if ( qhour % 24 == 0 ) {
            cCtxS.fillStyle = "#000000";
            cCtxS.fillRect(qhour*3+Math.trunc(qhour/4),9,1,9);
            cCtxM.fillStyle = "#000000";
            cCtxM.fillRect(qhour*5+Math.trunc(qhour/4)*2,18,2,18);
         } else if ( qhour % 4 == 0 ) {
            cCtxS.fillStyle = "#000000";
            cCtxS.fillRect(qhour*3+Math.trunc(qhour/4),14,1,4);
            cCtxM.fillStyle = "#000000";
            cCtxM.fillRect(qhour*5+Math.trunc(qhour/4)*2,28,2,8);
         }
         switch ( cData[ qhour ] ) {
            case "p":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+qhour*3+Math.trunc(qhour/4),0,3,6);
               cCtxS.fillRect(1+qhour*3+Math.trunc(qhour/4),12,3,6);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,12);
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,24,5,12);
               break;
            case "d":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+qhour*3+Math.trunc(qhour/4),0,3,18);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
               break;
            case "a":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+qhour*3+Math.trunc(qhour/4),0,3,4);
               cCtxS.fillRect(1+qhour*3+Math.trunc(qhour/4),6,3,2);
               cCtxS.fillRect(1+qhour*3+Math.trunc(qhour/4),10,3,2);
               cCtxS.fillRect(1+qhour*3+Math.trunc(qhour/4),14,3,4);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,8);
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,12,5,4);
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,20,5,4);
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,28,5,8);
               break;
            case "r":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+qhour*3+Math.trunc(qhour/4),7,3,4);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,14,5,8);
               break;
            default:
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+qhour*3+Math.trunc(qhour/4),0,3,18);
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
         if ( hour % 24 == 0 ) {
            if ( (dataDay + 1 + Math.trunc(hour/24)) % 7 == 0 ) {
               cCtxS.fillStyle = "#000000";
               cCtxS.fillRect(hour+Math.trunc(hour/6),0,1,18);
               cCtxM.fillStyle = "#000000";
               cCtxM.fillRect(hour*4+Math.trunc(hour/6)*2,0,2,36);
            } else {
               cCtxS.fillStyle = "#000000";
               cCtxS.fillRect(hour+Math.trunc(hour/6),4,1,14);
               cCtxM.fillStyle = "#000000";
               cCtxM.fillRect(hour*4+Math.trunc(hour/6)*2,8,2,28);
            }
         } else if ( hour % 6 == 0 ) {
            // 50% tick at the start of a six-hour/quarter-day period
            cCtxS.fillStyle = "#000000";
            cCtxS.fillRect(hour+Math.trunc(hour/6),9,1,9);
            cCtxM.fillStyle = "#000000";
            cCtxM.fillRect(hour*4+Math.trunc(hour/6)*2,18,2,18);
         }
         switch ( cData[ hour ] ) {
            case "p":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+hour+Math.trunc(hour/6),0,1,6);
               cCtxS.fillRect(1+hour+Math.trunc(hour/6),12,1,6);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,12);
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,24,4,12);
               break;
            case "d":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+hour+Math.trunc(hour/6),0,1,18);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            case "a":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+hour+Math.trunc(hour/6),0,1,4);
               cCtxS.fillRect(1+hour+Math.trunc(hour/6),6,1,2);
               cCtxS.fillRect(1+hour+Math.trunc(hour/6),10,1,2);
               cCtxS.fillRect(1+hour+Math.trunc(hour/6),14,1,4);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,8);
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,12,4,4);
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,20,4,4);
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,28,4,8);
               break;
            case "r":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+hour+Math.trunc(hour/6),7,1,4);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,14,4,8);
               break;
            default:
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+hour+Math.trunc(hour/6),0,1,18);
               cCtxM.fillStyle = "#F4F4F4";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
         }
      }
   }
}

function fillTodayCanvases() {

   // for the tic length we need to know the weekday:
   var dataDay  = ( new Date(myData.time * 1000) ).getDay();
   var cData;
   var cDom;
   var cCtx;
   var mData;

   // loop over site metrics and for each fill the s4 canvases:
   var mName = "Downtime";

      // s4 canvas, today, 24*4 quarter-hour entries:
      cData = myData.metrics[mName].today.split("");
      cDom = document.getElementById('cnvs_' + mName + '_s4');
      cCtx = cDom.getContext("2d");
      mData = Math.min(cData.length, 96 );
      for ( var qhour=0; qhour < mData; qhour+=1) {
         if ( qhour == 0 ) {
            if ( dataDay % 7 == 0 ) {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(6*qhour+2*Math.trunc(qhour/4),0,2,18);
            } else {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(6*qhour+2*Math.trunc(qhour/4),4,2,14);
            }
         } else if ( qhour % 24 == 0 ) {
            cCtx.fillStyle = "#000000";
            cCtx.fillRect(6*qhour+2*Math.trunc(qhour/4),9,2,9);
         } else if ( qhour % 4 == 0 ) {
            cCtx.fillStyle = "#000000";
            cCtx.fillRect(6*qhour+2*Math.trunc(qhour/4),14,2,4);
         }
         switch ( cData[ qhour ] ) {
            case "p":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),12,6,6);
               break;
            case "d":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
               break;
            case "a":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,2);
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),10,6,2);
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),14,6,4);
               break;
            case "r":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),7,6,4);
               break;
            default:
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
         }
      }

   // loop over site elements and fill the s4 canvases of each metric:
   for ( var cnt=0; cnt < myData.elements.length; cnt+=1 ) {
      var eName = myData.elements[cnt].host + '/' + myData.elements[cnt].type;
      eName = eName.replace(' ', '');
      // loop over metrics of element:
      mName = "Downtime";
         // s4 canvas, today, 24*4 quarter-hour entries:
         cData = myData.elements[cnt].metrics[mName].today.split("");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_s4');
         cCtx = cDom.getContext("2d");
         mData = Math.min(cData.length, 96 );
         for ( var qhour=0; qhour < mData; qhour+=1) {
            if ( qhour == 0 ) {
               if ( dataDay % 7 == 0 ) {
                  cCtx.fillStyle = "#000000";
                  cCtx.fillRect(6*qhour+2*Math.trunc(qhour/4),0,2,18);
               } else {
                  cCtx.fillStyle = "#000000";
                  cCtx.fillRect(6*qhour+2*Math.trunc(qhour/4),4,2,14);
               }
            } else if ( qhour % 24 == 0 ) {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(6*qhour+2*Math.trunc(qhour/4),9,2,9);
            } else if ( qhour % 4 == 0 ) {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(6*qhour+2*Math.trunc(qhour/4),14,2,4);
            }
            switch ( cData[ qhour ] ) {
               case "p":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),12,6,6);
                  break;
               case "d":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
                  break;
               case "a":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,2);
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),10,6,2);
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),14,6,4);
                  break;
               case "r":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),7,6,4);
                  break;
               default:
                  cCtx.fillStyle = "#F4F4F4";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
            }
         }
   }
}

function fillLegend() {
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
   cCtx = document.getElementById('cnvs_lgn_AtriskDowntime').getContext('2d');
   cCtx.fillStyle = "#6080FF";
   cCtx.fillRect(0,7,6,4);
   cCtx = document.getElementById('cnvs_lgn_Unknown').getContext('2d');
   cCtx.fillStyle = "#F4F4F4";
   cCtx.fillRect(0,0,6,18);
}
