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

function writeTable() {

   var myWidth = 1600;
   if ( window.innerWidth ) {
      myWidth = window.innerWidth;
   }
   if ( myWidth < 1440 ) {
      var fontHdrSite = 'font-size: 20px; font-weight: 700;';
      var fontHdrOthr = 'font-size: 18px; font-weight: 600;';
   } else if ( myWidth < 2048 ) {
      // standard page/view:
      var fontHdrSite = 'font-size: 22px; font-weight: 700;';
      var fontHdrOthr = 'font-size: 20px; font-weight: 600;';
   } else {
      // 4k display (QSXGA and higher):
      var fontHdrSite = 'font-size: 26px; font-weight: 700;';
      var fontHdrOthr = 'font-size: 24px; font-weight: 700;';
   }

   // add a line in case there is a message:
   if ( siteStatusInfo['msg'] != '' ) {
      var myTableStr = '<SPAN STYLE="color:blue; font-weight:bold;">' +
                          siteStatusInfo['msg'] + '</SPAN>\n<BR>\n<BR>\n';
   } else {
      var myTableStr = ''
   }

   // compose table header:
   myTableStr += '<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="0">\n<TR>\n' +
      '   <TH NOWRAP ALIGN="left"><SPAN STYLE="' + fontHdrSite + '">Sitename' +
      '</SPAN>\n   <TH NOWRAP ALIGN="center' + '"><SPAN STYLE="' +
      fontHdrOthr + '">&nbsp;Over Eight Days Old&nbsp;</SPAN>\n ' + '  <TH N' +
      'OWRAP ALIGN="center"><SPAN STYLE="' + fontHdrOthr + '">&nbsp;Previous' +
      ' Week&nbsp;</SPAN>\n   <TH NOWRAP ALIGN="center"><SPAN STYLE="' +
      fontHdrOthr + '">&nbsp;Yesterday&nbsp;</SPAN>\n   <TH NOWRAP ALIGN="ce' +
      'nter"><SPAN STYLE="' + fontHdrOthr + '">&nbsp;UTC Today</SPAN>\n';


   // loop over site GGUS data and write a table row for each site:
   for ( var sCnt=0; sCnt < siteGGUSData.length; sCnt+=1 ) {
      var sName = siteGGUSData[sCnt].site.toString();

      // compose URL for individual site status page:
      // write first, site name, column:
      if ( sCnt == 0 ) {
         myTableStr += '<TR>\n   <TD ALIGN=\"left\"><SPAN STYLE="font-size: ' +
            'larger; font-weight: 500;">' + sName + '</SPAN>\n   ';
      } else {
         myTableStr += '<TR>\n   <TD STYLE="border-top: 1px solid #DCDCDC;" ' +
            'ALIGN=\"left\"><SPAN STYLE="border-top: 1px solid #DCDCDC; font' +
            '-size: larger; font-weight: 500;">' + sName + '</SPAN>\n   ';
      }

      var myTime = new Date( siteStatusInfo.time * 1000 );
      myTime.setUTCHours(0, 0, 0, 0);
      var midnight = Math.trunc( myTime.valueOf() / 1000 );
      siteGGUSData[sCnt].ggus.sort(function(a,b){return a-b});
      var iTckt = 0;
      // GGUS tickets opened over eight days ago:
      if ( sCnt == 0 ) {
         myTableStr += '\n   <TD>';
      } else {
         myTableStr += '\n   <TD STYLE="border-top: 1px solid #DCDCDC;">';
      }
      var fDiv = 0;
      while ( iTckt < siteGGUSData[sCnt].ggus.length ) {
         if ( siteGGUSData[sCnt].ggus[iTckt][1] < midnight - 691200 ) {
            if ( fDiv == 0 ) {
               myTableStr += '<DIV STYLE="text-align: center">[<A HREF="http' +
                  's://helpdesk.ggus.eu/#ticket/zoom/' +
                  siteGGUSData[sCnt].ggus[iTckt][0] + '">' +
                  siteGGUSData[sCnt].ggus[iTckt][0] + '</A>]';
               fDiv = 1;
            } else {
               myTableStr += '&nbsp;[<A HREF="https://helpdesk.ggus.eu/#tick' +
                  'et/zoom/' + siteGGUSData[sCnt].ggus[iTckt][0] + '">' +
                  siteGGUSData[sCnt].ggus[iTckt][0] + '</A>]';
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
      if ( sCnt == 0 ) {
         myTableStr += '\n   <TD>';
      } else {
         myTableStr += '\n   <TD STYLE="border-top: 1px solid #DCDCDC;">';
      }
      fDiv = 0;
      while ( iTckt < siteGGUSData[sCnt].ggus.length ) {
         if ( siteGGUSData[sCnt].ggus[iTckt][1] < midnight - 86400 ) {
            if ( fDiv == 0 ) {
               myTableStr += '<DIV STYLE="text-align: center">[<A HREF="http' +
                  's://helpdesk.ggus.eu/#ticket/zoom/' +
                  siteGGUSData[sCnt].ggus[iTckt][0] + '">' +
                  siteGGUSData[sCnt].ggus[iTckt][0] + '</A>]';
               fDiv = 1;
            } else {
               myTableStr += '&nbsp;[<A HREF="https://helpdesk.ggus.eu/#tick' +
                  'et/zoom/' + siteGGUSData[sCnt].ggus[iTckt][0] + '">' +
                  siteGGUSData[sCnt].ggus[iTckt][0] + '</A>]';
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
      if ( sCnt == 0 ) {
         myTableStr += '\n   <TD>';
      } else {
         myTableStr += '\n   <TD STYLE="border-top: 1px solid #DCDCDC;">';
      }
      fDiv = 0;
      while ( iTckt < siteGGUSData[sCnt].ggus.length ) {
         if ( siteGGUSData[sCnt].ggus[iTckt][1] < midnight ) {
            if ( fDiv == 0 ) {
               myTableStr += '<DIV STYLE="text-align: center">[<A HREF="http' +
                  's://helpdesk.ggus.eu/#ticket/zoom/' +
                  siteGGUSData[sCnt].ggus[iTckt][0] + '">' +
                  siteGGUSData[sCnt].ggus[iTckt][0] + '</A>]';
               fDiv = 1;
            } else {
               myTableStr += '&nbsp;[<A HREF="https://helpdesk.ggus.eu/#tick' +
                  'et/zoom/' + siteGGUSData[sCnt].ggus[iTckt][0] + '">' +
                  siteGGUSData[sCnt].ggus[iTckt][0] + '</A>]';
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
      if ( sCnt == 0 ) {
         myTableStr += '\n   <TD>';
      } else {
         myTableStr += '\n   <TD STYLE="border-top: 1px solid #DCDCDC;">';
      }
      fDiv = 0;
      while ( iTckt < siteGGUSData[sCnt].ggus.length ) {
         if ( fDiv == 0 ) {
            myTableStr += '<DIV STYLE="text-align: center">[<A HREF="https:/' +
               '/helpdesk.ggus.eu/#ticket/zoom/' +
               siteGGUSData[sCnt].ggus[iTckt][0] + '">' +
               siteGGUSData[sCnt].ggus[iTckt][0] + '</A>]';
            fDiv = 1;
         } else {
            myTableStr += '&nbsp;[<A HREF="https://helpdesk.ggus.eu/#ticket/' +
               'zoom/' + siteGGUSData[sCnt].ggus[iTckt][0] + '">' +
               siteGGUSData[sCnt].ggus[iTckt][0] + '</A>]';
         }
         iTckt += 1;
      }
      if ( fDiv != 0 ) {
         myTableStr += '</DIV>';
      }
      // no future GGUS tickets:
      myTableStr += '\n';
   }

   // compose table trailer:
   myTableStr += '</TABLE>\n';


   // update main DIV section with table:
   document.getElementById("mainDIV").innerHTML = myTableStr;
}

function updateTimestamps() {

   document.getElementById("titleSPAN").innerHTML = 'CMS Site GGUS Tickets (' +
      dateString1( siteStatusInfo.time ) + ' GMT)';

   var timeObj = new Date( siteStatusInfo.time * 1000 );
   document.getElementById("legendSPAN").innerHTML =
      timeObj.toLocaleString(window.navigator.language, {weekday: "short",
         year: "numeric", month: "long", day: "numeric", hour: "numeric",
         minute: "2-digit", timeZoneName: "short" });

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
   cCtx = document.getElementById('cnvs_lgn_AtriskDowntime').getContext('2d');
   cCtx.fillStyle = "#6080FF";
   cCtx.fillRect(0,7,6,4);
   cCtx = document.getElementById('cnvs_lgn_Unknown').getContext('2d');
   cCtx.fillStyle = "#F4F4F4";
   cCtx.fillRect(0,0,6,18);
}
