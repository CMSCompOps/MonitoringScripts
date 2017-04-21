/* JavaScript ************************************************************** */
"use strict";



/* ************************************************************************* */
/* data:                                                                     */
/* ************************************************************************* */
var siteMetricLabel = { LifeStatus:       "Life Status",
                        manualLifeStatus: " &nbsp; manual Life Status",
                        ProdStatus:       "Prod Status",
                        manualProdStatus: " &nbsp; manual Prod Status",
                        CrabStatus:       "CRAB Status",
                        manualCrabStatus: " &nbsp; manual CRAB Status",
                        downtime:         "Downtime(s)",
                        SiteReadiness:    "Site Readiness",
                        wlcgSAMsite:      "SAM Status",
                        wlcgSAMservice:   "SAM Status",
                        wlcgSAMdowntime:  "SAM Downtime(s)",
                        summary:          "<B>Summary</B>" };
var siteMetricOrder = [ "LifeStatus", "manualLifeStatus",
                        "ProdStatus", "manualProdStatus",
                        "CrabStatus", "manualCrabStatus",
                        "***LINE***",
                        "***GGUS***",
                        "downtime",
                        "***LINE***",
                        "SiteReadiness", "wlcgSAMsite", "HC15min",
                        "***Othr***",
                        "summary",
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

function dateString3(timeInSeconds) {
   // function to return an abbreviated date string like "2017/01/01"
   var timeStr = "";

   var timeObj = new Date( timeInSeconds * 1000 );

   timeStr = timeObj.getUTCFullYear() + '/' +
      ("0" + (timeObj.getUTCMonth() + 1)).slice(-2) + '/' +
      ("0" + timeObj.getUTCDate()).slice(-2);

   return timeStr;
}

function dateString4(timeInSeconds) {
   // function to return an abbreviated date string like "2017-01-01"
   var timeStr = "";

   var timeObj = new Date( timeInSeconds * 1000 );

   timeStr = timeObj.getUTCFullYear() + '-' +
      ("0" + (timeObj.getUTCMonth() + 1)).slice(-2) + '-' +
      ("0" + timeObj.getUTCDate()).slice(-2);

   return timeStr;
}

function dateMidnight(timeInSeconds) {
   // function to return the time in seconds at midnight of the timestamp
   var midnight = 0;

   var timeObj = new Date( timeInSeconds * 1000 );
   timeObj.setUTCHours(0);
   timeObj.setUTCMinutes(0);
   timeObj.setUTCSeconds(0);
   midnight = Math.trunc( timeObj.getTime() / 1000 );

   return midnight;
}

function writeTable() {

   // compose table header:
   var myTableStr = '<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="0">\n<TR' +
      '>\n   <TH NOWRAP ALIGN="left"><BIG><B>Metric</B></BIG>\n   <TH NOWR' +
      'AP><BIG>&nbsp;</BIG>\n   <TH NOWRAP ALIGN="center"><BIG><B>Previous M' +
      'onth</B></BIG>\n   <TH NOWRAP ALIGN="center"><BIG><B>Previous Week</B' +
      '></BIG>\n   <TH NOWRAP ALIGN="center"><BIG><B>Yesterday</B></BIG>\n  ' +
      ' <TH NOWRAP ALIGN="center"><BIG><B>UTC Today</B></BIG>\n   <TH NOWRAP' +
      ' ALIGN="center"><BIG><B>Following Week</B></BIG>\n';


   // loop over metrics in siteMetricOrder and write a table row for each:
   for ( var mCnt=0; mCnt < siteMetricOrder.length; mCnt+=1 ) {
      if ( siteMetricOrder[mCnt] == "***LINE***" ) {
         myTableStr += '<TR>\n   <TD COLSPAN="7" bgcolor="#000000" STYLE="li' +
            'ne-height:2px;">&nbsp;\n<TR>\n   <TD COLSPAN="7" bgcolor="#FFFF' +
            'FF" STYLE="line-height:2px;">&nbsp;\n';
      } else if ( siteMetricOrder[mCnt] == "***GGUS***" ) {
         myTableStr += '<TR>\n   <TD ALIGN="left">GGUS tickets:\n' +
            '   <TD NOWRAP>&nbsp;';
         var nidnight = dateMidnight( myData.time );
         myData.ggus.sort();
         var iTckt = 0;
         // GGUS tickets opened more than 38 days ago:
         myTableStr += '\n   <TD>';
         var fDiv = 0;
         while ( iTckt < myData.ggus.length ) {
            if ( myData.ggus[iTckt][1] < nidnight - 3283200 ) {
               if ( fDiv == 0 ) {
                  myTableStr += '<DIV STYLE="text-align: left">[<A HREF="htt' +
                     'ps://ggus.eu/?mode=ticket_info&ticket_id=' +
                     myData.ggus[iTckt][0] + '">' + myData.ggus[iTckt][0] +
                     '</A>]';
                  fDiv = 1;
               } else {
                  myTableStr += '&nbsp;[<A HREF="https://ggus.eu/?mode=ticke' +
                     't_info&ticket_id=' + myData.ggus[iTckt][0] + '">' +
                     myData.ggus[iTckt][0] + '</A>]';
               }
               iTckt += 1;
            } else {
               break;
            }
         }
         if ( fDiv != 0 ) {
            myTableStr += '</DIV> ';
         }
         // GGUS tickets opened during the previous month:
         fDiv = 0;
         while ( iTckt < myData.ggus.length ) {
            if ( myData.ggus[iTckt][1] < nidnight - 691200 ) {
               if ( fDiv == 0 ) {
                  myTableStr += '<DIV STYLE="text-align: center">[<A HREF="h' +
                     'ttps://ggus.eu/?mode=ticket_info&ticket_id=' +
                     myData.ggus[iTckt][0] + '">' + myData.ggus[iTckt][0] +
                     '</A>]';
                  fDiv = 1;
               } else {
                  myTableStr += '&nbsp;[<A HREF="https://ggus.eu/?mode=ticke' +
                     't_info&ticket_id=' + myData.ggus[iTckt][0] + '">' +
                     myData.ggus[iTckt][0] + '</A>]';
               }
               iTckt += 1;
            } else {
               break;
            }
         }
         if ( fDiv != 0 ) {
            myTableStr += '</DIV>';
         }
         // GGUS tickets opened during the previous week:
         myTableStr += '\n   <TD>';
         fDiv = 0;
         while ( iTckt < myData.ggus.length ) {
            if ( myData.ggus[iTckt][1] < nidnight - 86400 ) {
               if ( fDiv == 0 ) {
                  myTableStr += '<DIV STYLE="text-align: center">[<A HREF="h' +
                     'ttps://ggus.eu/?mode=ticket_info&ticket_id=' +
                     myData.ggus[iTckt][0] + '">' + myData.ggus[iTckt][0] +
                     '</A>]';
                  fDiv = 1;
               } else {
                  myTableStr += '&nbsp;[<A HREF="https://ggus.eu/?mode=ticke' +
                     't_info&ticket_id=' + myData.ggus[iTckt][0] + '">' +
                     myData.ggus[iTckt][0] + '</A>]';
               }
               iTckt += 1;
            } else {
               break;
            }
         }
         if ( fDiv != 0 ) {
            myTableStr += '</DIV>';
         }
         // GGUS tickets opened yesterday:
         myTableStr += '\n   <TD>';
         fDiv = 0;
         while ( iTckt < myData.ggus.length ) {
            if ( myData.ggus[iTckt][1] < nidnight ) {
               if ( fDiv == 0 ) {
                  myTableStr += '<DIV STYLE="text-align: center">[<A HREF="h' +
                     'ttps://ggus.eu/?mode=ticket_info&ticket_id=' +
                     myData.ggus[iTckt][0] + '">' + myData.ggus[iTckt][0] +
                     '</A>]';
                  fDiv = 1;
               } else {
                  myTableStr += '&nbsp;[<A HREF="https://ggus.eu/?mode=ticke' +
                     't_info&ticket_id=' + myData.ggus[iTckt][0] + '">' +
                     myData.ggus[iTckt][0] + '</A>]';
               }
               iTckt += 1;
            } else {
               break;
            }
         }
         if ( fDiv != 0 ) {
            myTableStr += '</DIV>';
         }
         // GGUS tickets opened today:
         myTableStr += '\n   <TD>';
         fDiv = 0;
         while ( iTckt < myData.ggus.length ) {
            if ( fDiv == 0 ) {
               myTableStr += '<DIV STYLE="text-align: center">[<A HREF="http' +
                  's://ggus.eu/?mode=ticket_info&ticket_id=' +
                  myData.ggus[iTckt][0] + '">' + myData.ggus[iTckt][0] +
                  '</A>]';
               fDiv = 1;
            } else {
               myTableStr += '&nbsp;[<A HREF="https://ggus.eu/?mode=ticket_i' +
                  'nfo&ticket_id=' + myData.ggus[iTckt][0] + '">' +
                  myData.ggus[iTckt][0] + '</A>]';
            }
            iTckt += 1;
         }
         if ( fDiv != 0 ) {
            myTableStr += '</DIV>';
         }
         // no future GGUS tickets:
         myTableStr += '\n   <TD>\n';
      } else if ( siteMetricOrder[mCnt] in myData.metrics ) {
         var nName = siteMetricOrder[mCnt];
         if ( siteMetricOrder[mCnt] in siteMetricLabel ) {
            nName = siteMetricLabel[siteMetricOrder[mCnt]];
         }
         myTableStr += '<TR>\n   <TD NOWRAP ALIGN="left">' + nName + '\n   <' +
            'TD NOWRAP>&nbsp;\n';
         var urlXstr = "";
         // second, previous month's, column:
         if ( siteMetricOrder[mCnt] == "wlcgSAMsite" ) {
            urlXstr = ' HREF="http://wlcg-sam-cms.cern.ch/templates/ember/#/' +
               'historicalsmry/heatMap?profile=CMS_CRITICAL_FULL&site=' +
               myData.site + '&start_time=' +
               dateString3(myData.time - 38 * 86400) + ' 00:00&end_time=' +
               dateString3(myData.time - 8 * 86400) + ' 00:00&time=manual&gr' +
               'anularity=Daily&view=Service Availability"';
         } else if ( siteMetricOrder[mCnt] == "HC15min" ) {
            urlXstr = ' HREF="http://dashb-ssb.cern.ch/dashboard/request.py/' +
               'siteviewhistory?columnid=217&debug=false#time=custom&start_d' +
               'ate=' + dateString4(myData.time - 38 * 86400) + '&end_date=' +
               dateString4(myData.time - 8 * 86400) + '&values=false&spline=' +
               'false&debug=false&resample=false&sites=one&clouds=all&site=' +
               myData.site + '"';
         } else {
            urlXstr = '';
         }
         myTableStr += '   <TD><A CLASS="toolTip1"' + urlXstr + '><CANVAS ID' +
            '="cnvs_' + siteMetricOrder[mCnt] + '_s1" WIDTH=' + '"272" HEIGH' +
            'T="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPADDIN' +
            'G="0" CELLSPACING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Pre' +
            'vious Month of ' + nName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><' +
            'TD COLSPAN="2"><CANVAS ID="cnvs_' + siteMetricOrder[mCnt] +
            '_m1" WIDTH="540" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">' +
            dateString2(myData.time - 38 * 86400) + '<TD ALIGN="right">' +
            dateString2(myData.time - 9 * 86400) + '</TABLE></SPAN></A>\n';
         // third, previous week's, column:
         if ( siteMetricOrder[mCnt] == "wlcgSAMsite" ) {
            urlXstr = ' HREF="http://wlcg-sam-cms.cern.ch/templates/ember/#/' +
               'historicalsmry/heatMap?profile=CMS_CRITICAL_FULL&site=' +
               myData.site + '&start_time=' +
               dateString3(myData.time - 8 * 86400 ) + ' 00:00&end_time=' +
               dateString3( myData.time - 86400 ) + ' 00:00&time=manual&gran' +
               'ularity=Daily&view=Service Availability"';
         } else if ( siteMetricOrder[mCnt] == "HC15min" ) {
            urlXstr = ' HREF="http://dashb-ssb.cern.ch/dashboard/request.py/' +
               'siteviewhistory?columnid=217&debug=false#time=custom&start_d' +
               'ate=' + dateString4(myData.time - 8 * 86400) + '&end_date=' +
               dateString4(myData.time - 86400) + '&values=false&spline=fals' +
               'e&debug=false&resample=false&sites=one&clouds=all&site=' +
               myData.site + '"';
         } else {
            urlXstr = '';
         }
         myTableStr += '   <TD><A CLASS="toolTip2"' + urlXstr + '><CANVAS ID' +
            '="cnvs_' + siteMetricOrder[mCnt] + '_s2" WIDTH=' + '"198" HEIGH' +
            'T="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPADDIN' +
            'G="0" CELLSPACING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Pre' +
            'vious Week of ' + nName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><T' +
            'D COLSPAN="2"><CANVAS ID="cnvs_' + siteMetricOrder[mCnt] +
            '_m2" WIDTH="728" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">' +
            dateString2(myData.time - 8 * 86400) + '<TD ALIGN="right">' +
            dateString2(myData.time - 2 * 86400) + '</TABLE></SPAN></A>\n';
         // fourth, yesterday's, column:
         if ( siteMetricOrder[mCnt] == "wlcgSAMsite" ) {
            urlXstr = ' HREF="http://wlcg-sam-cms.cern.ch/templates/ember/#/' +
               'historicalsmry/heatMap?profile=CMS_CRITICAL_FULL&site=' +
               myData.site + '&start_time=' +
               dateString3(myData.time - 86400) + ' 00:00&end_time=' +
               dateString3(myData.time) + ' 00:00&time=manual&view=Test Hist' +
               'ory"';
         } else if ( siteMetricOrder[mCnt] == "HC15min" ) {
            urlXstr = ' HREF="http://dashb-ssb.cern.ch/dashboard/request.py/' +
               'siteviewhistory?columnid=217&debug=false#time=custom&start_d' +
               'ate=' + dateString4(myData.time - 86400) + '&end_date=' +
               dateString4(myData.time) + '&values=false&spline=false&debug=' +
               'false&resample=false&sites=one&clouds=all&site=' +
               myData.site + '"';
         } else {
            urlXstr = '';
         }
         myTableStr += '   <TD><A CLASS="toolTip3"' + urlXstr + '><CANVAS ID' +
            '="cnvs_' + siteMetricOrder[mCnt] + '_s3" WIDTH="218" HEIGHT="18' +
            '"></CANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPADDING="0"' +
            ' CELLSPACING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Yesterda' +
            'y (' + dateString2( myData.time - 86400 ) + ') of ' + nName +
            '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSPAN="2"><CANVAS ID="c' +
            'nvs_' + siteMetricOrder[mCnt] + '_m3" WIDTH="432" HEIGHT="36"><' +
            '/CANVAS><TR><TD ALIGN="left">00:00<TD ALIGN="right">24:00</TABL' +
            'E></SPAN></A>\n';
         // fifth, today's, column:
         if ( siteMetricOrder[mCnt] == "manualLifeStatus" ) {
            urlXstr = ' HREF="https://cmssst.web.cern.ch/cmssst/man_override' +
               '/cgi/manualOverride.py/lifestatus"';
         } else if ( siteMetricOrder[mCnt] == "manualProdStatus" ) {
            urlXstr = ' HREF="https://cmssst.web.cern.ch/cmssst/man_override' +
               '/cgi/manualOverride.py/prodstatus"';
         } else if ( siteMetricOrder[mCnt] == "manualCrabStatus" ) {
            urlXstr = ' HREF="https://cmssst.web.cern.ch/cmssst/man_override' +
               '/cgi/manualOverride.py/crabstatus"';
         } else if ( siteMetricOrder[mCnt] == "wlcgSAMsite" ) {
            urlXstr = ' HREF="http://wlcg-sam-cms.cern.ch/templates/ember/#/' +
               'historicalsmry/heatMap?profile=CMS_CRITICAL_FULL&site=' +
               myData.site + '&start_time=' + dateString3(myData.time) +
               ' 00:00&end_time=' + dateString3(myData.time + 86400) +
               ' 00:00&time=manual&view=Test History"';
         } else if ( siteMetricOrder[mCnt] == "HC15min" ) {
            urlXstr = ' HREF="http://dashb-ssb.cern.ch/dashboard/request.py/' +
               'siteviewhistory?columnid=217&debug=false#time=custom&start_d' +
               'ate=' + dateString4(myData.time) + '&end_date=' +
               dateString4(myData.time + 86400) + '&values=false&spline=fals' +
               'e&debug=false&resample=false&sites=one&clouds=all&site=' +
               myData.site + '"';
         } else {
            urlXstr = '';
         }
         myTableStr += '   <TD><A CLASS="toolTip4"' + urlXstr + '><CANVAS ID' +
            '="cnvs_' + siteMetricOrder[mCnt] + '_s4" WIDTH="314" HEIGHT="18' +
            '"></CANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPADDING="0"' +
            ' CELLSPACING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Today (' +
            dateString2( myData.time ) + ') of ' + nName + '</B><TR><TD COLS' +
            'PAN="2">&nbsp;<TR><TD COLSPAN="2"><CANVAS ID="cnvs_' +
            siteMetricOrder[mCnt] + '_m4" WIDTH="528" HEIGHT="36"></CANVAS><' +
            'TR><TD ALIGN="left">00:00<TD ALIGN="right">24:00</TABLE></SPAN>' +
            '</A>\n';
         // sixth, following week's column:
         if ( siteMetricOrder[mCnt] == "wlcgSAMsite" ) {
            urlXstr = ' HREF="http://wlcg-sam-cms.cern.ch/templates/ember/#/' +
               'historicalsmry/heatMap?profile=CMS_CRITICAL_FULL&site=' +
               myData.site + '&start_time=' +
               dateString3(myData.time + 86400) + ' 00:00&end_time=' +
               dateString3(myData.time + 8 * 86400) + ' 00:59&time=manual&gr' +
               'anularity=Daily&view=Service Availability"';
         } else if ( siteMetricOrder[mCnt] == "HC15min" ) {
            urlXstr = ' HREF="http://dashb-ssb.cern.ch/dashboard/request.py/' +
               'siteviewhistory?columnid=217&debug=false#time=custom&start_d' +
               'ate=' + dateString4(myData.time + 86400) + '&end_date=' +
               dateString4(myData.time + 8 * 86400) + '&values=false&spline=' +
               'false&debug=false&resample=false&sites=one&clouds=all&site=' +
               myData.site + '"';
         } else {
            urlXstr = '';
         }
         myTableStr += '   <TD><A CLASS="toolTip5"' + urlXstr + '><CANVAS ID' +
            '="cnvs_' + siteMetricOrder[mCnt] + '_s5" WIDTH="198" HEIGHT="18' +
            '"></CANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPADDING="0"' +
            ' CELLSPACING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Followin' +
            'g Week of ' + nName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD CO' +
            'LSPAN="2"><CANVAS ID="cnvs_' + siteMetricOrder[mCnt] +
            '_m5" WIDTH="728" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">' +
            dateString2( myData.time + 1 * 86400 ) + '<TD ALIGN="right">' +
            dateString2( myData.time + 7 * 86400 ) + '</TABLE></SPAN></A>\n';
      } else if ( siteMetricOrder[mCnt] == "***Othr***" ) {
         // loop over site metrics and write any not in siteMetricOrder:
         for ( var mName in myData.metrics ) {
            if ( siteMetricOrder.indexOf(mName) >= 0 ) {
               continue;
            }
            myTableStr += '<TR>\n   <TD ALIGN="left">' + mName +
               '\n   <TD NOWRAP>&nbsp;\n';
            // second, previous month's, column:
            myTableStr += '   <TD><A CLASS="toolTip1"><CANVAS ID="cnvs_' +
               mName + '_s1" WIDTH="272" HEIGHT="18"></CANVAS><SPAN><TABLE' +
               ' WIDTH="100%" BORDER="0" CELLPADDING="0" CELLSPACING="0"><TR' +
               '><TD COLSPAN="2" ALIGN="center"><B>Previous Month of ' +
               mName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSPAN="2"><C' +
               'ANVAS ID="cnvs_' + mName + '_m1" WIDTH="540" HEIGHT="36"><' +
               '/CANVAS><TR><TD ALIGN="left">' +
               dateString2( myData.time - 38 * 86400 ) + '<TD ALIGN="right">' +
               dateString2( myData.time - 9 * 86400 ) +
               '</TABLE></SPAN></A>\n';
            // third, previous week's, column:
            myTableStr += '   <TD><A CLASS="toolTip2"><CANVAS ID="cnvs_' +
               mName + '_s2" WIDTH="198" HEIGHT="18"></CANVAS><SPAN><TABLE' +
               ' WIDTH="100%" BORDER="0" CELLPADDING="0" CELLSPACING="0"><TR' +
               '><TD COLSPAN="2" ALIGN="center"><B>Previous Week of ' + mName +
               '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSPAN="2"><CANVAS ID' +
               '="cnvs_' + mName + '_m2" WIDTH="728" HEIGHT="36"></CANVAS>' +
               '<TR><TD ALIGN="left">' +
               dateString2( myData.time - 8 * 86400 ) + '<TD ALIGN="right">' +
               dateString2( myData.time - 2 * 86400 ) +
               '</TABLE></SPAN></A>\n';
            // fourth, yesterday's, column:
            myTableStr += '   <TD><A CLASS="toolTip3"><CANVAS ID="cnvs_' +
               mName + '_s3" WIDTH="218" HEIGHT="18"></CANVAS><SPAN><TABLE' +
               ' WIDTH="100%" BORDER="0" CELLPADDING="0" CELLSPACING="0"><TR' +
               '><TD COLSPAN="2" ALIGN="center"><B>Yesterday (' +
               dateString2( myData.time - 86400 ) + ') of ' + mName +
               '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSPAN="2"><CANVAS ID' +
               '="cnvs_' + mName + '_m3" WIDTH="432" HEIGHT="36"></CANVAS>' +
               '<TR><TD ALIGN="left">00:00<TD ALIGN="right">24:00</TABLE></S' +
               'PAN></A>\n';
            // fifth, today's, column:
            myTableStr += '   <TD><A CLASS="toolTip4"><CANVAS ID="cnvs_' +
               mName + '_s4" WIDTH="314" HEIGHT="18"></CANVAS><SPAN><TABLE' +
               ' WIDTH="100%" BORDER="0" CELLPADDING="0" CELLSPACING="0"><TR' +
               '><TD COLSPAN="2" ALIGN="center"><B>Today (' +
               dateString2( myData.time ) + ') of ' + mName + '</B><TR><TD C' +
               'OLSPAN="2">&nbsp;<TR><TD COLSPAN="2"><CANVAS ID="cnvs_' +
               mName + '_m4" WIDTH="528" HEIGHT="36"></CANVAS><TR><TD ALIG' +
               'N="left">00:00<TD ALIGN="right">24:00</TABLE></SPAN></A>\n';
            // sixth, following week's column:
            myTableStr += '   <TD><A CLASS="toolTip5"><CANVAS ID="cnvs_' +
               mName + '_s5" WIDTH="198" HEIGHT="18"></CANVAS><SPAN><TABLE' +
               ' WIDTH="100%" BORDER="0" CELLPADDING="0" CELLSPACING="0"><TR' +
               '><TD COLSPAN="2" ALIGN="center"><B>Following Week of ' +
               mName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSPAN="2"><C' +
               'ANVAS ID="cnvs_' + mName + '_m5" WIDTH="728" HEIGHT="36"><' +
               '/CANVAS><TR><TD ALIGN="left">' +
               dateString2( myData.time + 1 * 86400 ) + '<TD ALIGN="right">' +
               dateString2( myData.time + 7 * 86400 ) +
               '</TABLE></SPAN></A>\n';
         }
      } else if ( siteMetricOrder[mCnt] == "**Elmnts**" ) {
         // loop over site elements and write the metrics of each:
         for ( var cnt=0; cnt < myData.elements.length; cnt+=1 ) {
            // concatenate host and type excluding domain
            var indx = myData.elements[cnt].host.indexOf('.');
            if ( indx <= 0 ) {
               indx = myData.elements[cnt].host.length;
            }
            var eName = myData.elements[cnt].host.substring(0,indx) + ' / ' +
               myData.elements[cnt].type;

            myTableStr += '<TR>\n   <TD COLSPAN="7" bgcolor="#000000" STYLE=' +
               '"line-height:2px;">&nbsp;\n<TR>\n   <TD COLSPAN="7" bgcolor=' +
               '"#FFFFFF" STYLE="line-height:8px;">&nbsp;\n<TR>\n   <TD COLS' +
               'PAN="7" bgcolor="#FFFFFF" ALIGN="left"><SPAN STYLE="font-siz' +
               'e:large;">' + eName + '</SPAN>\n';
            eName = myData.elements[cnt].host + '/' + myData.elements[cnt].type;
            eName = eName.replace(' ', '');
            // loop over metrics of element:
            for ( var mName in myData.elements[cnt].metrics ) {
               if ( mName in siteMetricLabel ) {
                  myTableStr += '<TR>\n   <TD NOWRAP ALIGN="left"> &nbsp &nb' +
                     'sp ' + siteMetricLabel[mName] +
                     '\n   <TD NOWRAP>&nbsp;\n';
               } else {
                  myTableStr += '<TR>\n   <TD NOWRAP ALIGN="left"> &nbsp &nb' +
                     'sp ' + mName + '\n   <TD NOWRAP>&nbsp;\n';
               }
               // second, previous month's, column:
               if ( mName =="wlcgSAMservice" ) {
                  urlXstr = ' HREF="http://wlcg-sam-cms.cern.ch/templates/em' +
                     'ber/#/historicalsmry/heatMap?profile=CMS_CRITICAL_FULL' +
                     '&site=' + myData.site + '&hostname=' +
                     myData.elements[cnt].host + '&start_time=' +
                     dateString3(myData.time - 38 * 86400) +
                     ' 00:00&end_time=' +
                     dateString3(myData.time - 8 * 86400) +
                     ' 00:00&time=manual&view=Test History"';
               } else {
                  urlXstr = '';
               }
               myTableStr += '   <TD><A CLASS="toolTip1"' + urlXstr + '><CAN' +
                  'VAS ID="cnvs_' + eName + '_' + mName + '_s1" WIDTH="272" ' +
                  'HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDER="0"' +
                  ' CELLPADDING="0" CELLSPACING="0"><TR><TD COLSPAN="2" ALIG' +
                  'N="center"><B>Previous Month of ' + mName + '</B><TR><TD ' +
                  'COLSPAN="2">&nbsp;<TR><TD COLSPAN="2"><CANVAS ID="cnvs_' +
                  eName + '_' + mName + '_m1" WIDTH="540" HEIGHT="36"></CANV' +
                  'AS><TR><TD ALIGN="left">' +
                  dateString2( myData.time - 38 * 86400 ) +
                  '<TD ALIGN="right">' +
                  dateString2( myData.time - 9 * 86400 ) +
                  '</TABLE></SPAN></A>\n';
               // third, previous week's, column:
               if ( mName =="wlcgSAMservice" ) {
                  urlXstr = ' HREF="http://wlcg-sam-cms.cern.ch/templates/em' +
                     'ber/#/historicalsmry/heatMap?profile=CMS_CRITICAL_FULL' +
                     '&site=' + myData.site + '&hostname=' +
                     myData.elements[cnt].host + '&start_time=' +
                     dateString3(myData.time - 8* 86400) + ' 00:00&end_time=' +
                     dateString3(myData.time - 86400) + ' 00:00&time=manual&' +
                     'view=Test History"';
               } else {
                  urlXstr = '';
               }
               myTableStr += '   <TD><A CLASS="toolTip2"' + urlXstr + '><CAN' +
                  'VAS ID="cnvs_' + eName + '_' + mName + '_s2" WIDTH="198" ' +
                  'HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDER="0"' +
                  ' CELLPADDING="0" CELLSPACING="0"><TR><TD COLSPAN="2" ALIG' +
                  'N="center"><B>Previous Week of ' + mName + '</B><TR><TD C' +
                  'OLSPAN="2">&nbsp;<TR><TD COLSPAN="2"><CANVAS ID="cnvs_' +
                  eName + '_' + mName + '_m2" WIDTH="728" HEIGHT="36"></CANV' +
                  'AS><TR><TD ALIGN="left">' +
                  dateString2(myData.time - 8 * 86400) + '<TD ALIGN="right">' +
                  dateString2(myData.time - 2 * 86400) +
                  '</TABLE></SPAN></A>\n';
               // fourth, yesterday's, column:
               if ( mName =="wlcgSAMservice" ) {
                  urlXstr = ' HREF="http://wlcg-sam-cms.cern.ch/templates/em' +
                     'ber/#/historicalsmry/heatMap?profile=CMS_CRITICAL_FULL' +
                     '&site=' + myData.site + '&hostname=' +
                     myData.elements[cnt].host + '&start_time=' +
                     dateString3(myData.time - 86400) + ' 00:00&end_time=' +
                     dateString3(myData.time) + ' 00:00&time=manual&view=Tes' +
                     't History"';
               } else {
                  urlXstr = '';
               }
               myTableStr += '   <TD><A CLASS="toolTip3"' + urlXstr + '><CAN' +
                  'VAS ID="cnvs_' + eName + '_' + mName + '_s3" WIDTH="218" ' +
                  'HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDER="0"' +
                  ' CELLPADDING="0" CELLSPACING="0"><TR><TD COLSPAN="2" ALIG' +
                  'N="center"><B>Yesterday (' +
                  dateString2( myData.time - 86400 ) + ') of ' + mName +
                  '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSPAN="2"><CANVAS' +
                  ' ID="cnvs_' + eName + '_' + mName + '_m3" WIDTH="432" HEI' +
                  'GHT="36"></CANVAS><TR><TD ALIGN="left">00:00<TD ALIGN="ri' +
                  'ght">24:00</TABLE></SPAN></A>\n';
               // fifth, today's, column:
               if ( mName =="wlcgSAMservice" ) {
                  urlXstr = ' HREF="http://wlcg-sam-cms.cern.ch/templates/em' +
                     'ber/#/historicalsmry/heatMap?profile=CMS_CRITICAL_FULL' +
                     '&site=' + myData.site + '&hostname=' +
                     myData.elements[cnt].host + '&start_time=' +
                     dateString3(myData.time) + ' 00:00&end_time=' +
                     dateString3( myData.time + 86400 ) + ' 00:00&time=manua' +
                     'l&view=Test History"';
               } else {
                  urlXstr = '';
               }
               myTableStr += '   <TD><A CLASS="toolTip4"' + urlXstr + '><CAN' +
                  'VAS ID="cnvs_' + eName + '_' + mName + '_s4" WIDTH="314" ' +
                  'HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDER="0"' +
                  ' CELLPADDING="0" CELLSPACING="0"><TR><TD COLSPAN="2" ALIG' +
                  'N="center"><B>Today (' + dateString2( myData.time ) +
                  ') of ' + mName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD C' +
                  'OLSPAN="2"><CANVAS ID="cnvs_' + eName + '_' + mName +
                  '_m4" WIDTH="528" HEIGHT="36"></CANVAS><TR><TD ALIGN="left' +
                  '">00:00<TD ALIGN="right">24:00</TABLE></SPAN></A>\n';
               // sixth, following week's column:
               myTableStr += '   <TD><A CLASS="toolTip5"><CANVAS ID="cnvs_' +
                  eName + '_' + mName + '_s5" WIDTH="198" HEIGHT="18"></CA' +
                  'NVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPADDING="0"' +
                  ' CELLSPACING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Fo' +
                  'llowing Week of ' + mName + '</B><TR><TD COLSPAN="2">&nbs' +
                  'p;<TR><TD COLSPAN="2"><CANVAS ID="cnvs_' + eName + '_' +
                  mName + '_m5" WIDTH="728" HEIGHT="36"></CANVAS><TR><TD A' +
                  'LIGN="left">' + dateString2( myData.time + 1 * 86400 ) +
                  '<TD ALIGN="right">' +
                  dateString2( myData.time + 7 * 86400 ) +
                  '</TABLE></SPAN></A>\n';
            }
         }
      }
   }

   // add a row/line in case there is a message:
   if ( myData.msg != '' ) {
      myTableStr += '<TR>\n   <TD COLSPAN="7" ALIGN="left"><SPAN STYLE="colo' +
         'r:blue; font-weight:bold;">' + siteStatusInfo['msg'] + '</SPAN>\n';
   }

   // compose table trailer:
   myTableStr += '</TABLE>\n';


   // update main DIV section with table:
   document.getElementById("mainDIV").innerHTML = myTableStr;
}

function updateTimestamps() {

   document.getElementById("titleSPAN").innerHTML = myData.site + ' Site Sta' +
      'tus Detail (' + dateString1( myData.time ) + ' GMT)';

   var timeObj = new Date( myData.time * 1000 );
   document.getElementById("legendSPAN").innerHTML =
      timeObj.toLocaleString(window.navigator.language, {weekday: "short",
         year: "numeric", month: "long", day: "numeric", hour: "numeric",
         minute: "2-digit", timeZoneName: "short" });

}

function fillCanvases() {

   // for the tic length we need to know the weekday:
   var dataDay  = ( new Date(myData.time * 1000) ).getDay();
   var cData;
   var cDom;
   var cCtx;
   var mData;

   // loop over site metrics and for each fill the five canvases:
   for ( var mName in myData.metrics ) {

      // first canvas, previous month, 120 six-hour/quarter-day entries:
      cData = myData.metrics[mName].pmonth.split("");
      cDom = document.getElementById('cnvs_' + mName + '_s1');
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
      cData = myData.metrics[mName].pweek.split("");
      cDom = document.getElementById('cnvs_' + mName + '_s2');
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
      cData = myData.metrics[mName].yesterday.split("");
      cDom = document.getElementById('cnvs_' + mName + '_s3');
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
      cData = myData.metrics[mName].today.split("");
      cDom = document.getElementById('cnvs_' + mName + '_s4');
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
      cData = myData.metrics[mName].fweek.split("");
      cDom = document.getElementById('cnvs_' + mName + '_s5');
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

   // loop over site elements and fill the five canvases of each metric:
   for ( var cnt=0; cnt < myData.elements.length; cnt+=1 ) {
      var eName = myData.elements[cnt].host + '/' + myData.elements[cnt].type;
      eName = eName.replace(' ', '');
      // loop over metrics of element:
      for ( var mName in myData.elements[cnt].metrics ) {
         // first canvas, previous month, 120 six-hour/quarter-day entries:
         cData = myData.elements[cnt].metrics[mName].pmonth.split("");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_s1');
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
         cData = myData.elements[cnt].metrics[mName].pweek.split("");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_s2');
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
         cData = myData.elements[cnt].metrics[mName].yesterday.split("");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_s3');
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
         cData = myData.elements[cnt].metrics[mName].today.split("");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_s4');
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
         cData = myData.elements[cnt].metrics[mName].fweek.split("");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_s5');
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
}

function fillMagCanvases() {

   // for the tic length we need to know the weekday:
   var dataDay  = ( new Date(myData.time * 1000) ).getDay();
   var cData;
   var cDom;
   var cCtx;
   var mData;

   // loop over site summary data and fill the five magnification canvases:
   for ( var mName in myData.metrics ) {

      // first canvas, previous month, 120 six-hour/quarter-day entries:
      cData = myData.metrics[mName].pmonth.split("");
      cDom = document.getElementById('cnvs_' + mName + '_m1');
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
      cData = myData.metrics[mName].pweek.split("");
      cDom = document.getElementById('cnvs_' + mName + '_m2');
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
      cData = myData.metrics[mName].yesterday.split("");
      cDom = document.getElementById('cnvs_' + mName + '_m3');
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
      cData = myData.metrics[mName].today.split("");
      cDom = document.getElementById('cnvs_' + mName + '_m4');
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
      cData = myData.metrics[mName].fweek.split("");
      cDom = document.getElementById('cnvs_' + mName + '_m5');
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

   // loop over site elements and fill the five canvases of each metric:
   for ( var cnt=0; cnt < myData.elements.length; cnt+=1 ) {
      var eName = myData.elements[cnt].host + '/' + myData.elements[cnt].type;
      eName = eName.replace(' ', '');
      // loop over metrics of element:
      for ( var mName in myData.elements[cnt].metrics ) {
         // first canvas, previous month, 120 six-hour/quarter-day entries:
         cData = myData.elements[cnt].metrics[mName].pmonth.split("");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_m1');
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
         cData = myData.elements[cnt].metrics[mName].pweek.split("");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_m2');
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
         cData = myData.elements[cnt].metrics[mName].yesterday.split("");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_m3');
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
         cData = myData.elements[cnt].metrics[mName].today.split("");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_m4');
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
         cData = myData.elements[cnt].metrics[mName].fweek.split("");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_m5');
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
