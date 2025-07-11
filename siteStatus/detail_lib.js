/* JavaScript ************************************************************** */
"use strict";



/* ************************************************************************* */
/* data:                                                                     */
/* ************************************************************************* */
var siteMetricLabel = { Downtime:         "Downtime(s)",
                        SAMsite:          "SAM Status",
                        SAMservice:       "SAM Status",
                        HammerCloud:      "Hammer Cloud",
                        FTSsite:          "FTS Status",
                        FTSsource:        "FTS (from)",
                        FTSdestination:   "FTS (to)",
                        SiteReadiness:    "Site Readiness",
                        SAM1day:          "SAM (1day)",
                        HC1day:           "HC (1day)",
                        FTS1day:          "FTS (1day)",
                        SR1day:           "SiteReadiness (1day)",
                        LifeStatus:       "Life Status",
                        manLifeStatus:    " &nbsp; &nbsp; Life Override",
                        ProdStatus:       "Prod Status",
                        manProdStatus:    " &nbsp; &nbsp; Prod Override",
                        CrabStatus:       "Crab Status",
                        manCrabStatus:    " &nbsp; &nbsp; Crab Override",
                        RucioStatus:      "Rucio Status",
                        manRucioStatus:   " &nbsp; &nbsp; Rucio Override",
                        newSummary:       "<B>Summary:</B>" };
var siteMetricOrder = [ "Downtime", "SAM1day", "HC1day", "FTS1day",
                        "***LINE***",
                        "SR1day",
                        "***LINE***",
                        "LifeStatus", "manLifeStatus",
                        "ProdStatus", "manProdStatus",
                        "CrabStatus", "manCrabStatus",
                        "RucioStatus", "manRucioStatus",
                        "***LINE***",
                        "***GGUS***",
                        "***LINE***", "***LINE***",
                        "SAMsite", "HammerCloud", "FTSsite",
                        "***LINE***",
                        "SiteReadiness",
                        "***LINE***",
                        "***Othr***",
                        "***LINE***",
                        "Summary",
                        "***LINE***",
                        "**Elmnts**" ];
var srvcMetricLabel = { SAMservice:       "SAM Service Status",
                        FTSsource:        "FTS Endpoint (from)",
                        FTSdestination:   "FTS Endpoint (to)" };
var srvcMetricOrder = [ "Downtime",
                        "SAMservice",
                        "FTSsource", "FTSdestination",
                        "***LINE***",
                        "ETF_SRM-GetPFNFromTFC", "ETF_SRM-VOLsDir",
                           "ETF_SRM-VOPut", "ETF_SRM-VOLs",
                           "ETF_SRM-VOGetTURLs", "ETF_SRM-VOGet",
                           "ETF_SRM-VODel", "ETF_SRM-AllCMS",
                        "ETF_SE-GSIftp-1connection", "ETF_SE-GSIftp-2ssl",
                           "ETF_SE-GSIftp-4crt-read",
                           "ETF_SE-GSIftp-5open-access",
                           "ETF_SE-GSIftp-6crt-write",
                           "ETF_SE-GSIftp-9summary",
                        "ETF_SE-WebDAV-1connection", "ETF_SE-WebDAV-2ssl",
                           "ETF_SE-WebDAV-3crt_extension",
                           "ETF_SE-WebDAV-4crt-read",
                           "ETF_SE-WebDAV-6crt-access",
                           "ETF_SE-WebDAV-7crt-write",
                           "ETF_SE-WebDAV-8crt-directory",
                           "ETF_SE-WebDAV-10macaroon",
                           "ETF_SE-WebDAV-14tkn-read",
                           "ETF_SE-WebDAV-16tkn-access",
                           "ETF_SE-WebDAV-17tkn-write",
                           "ETF_SE-WebDAV-18tkn-directory",
                           "ETF_SE-WebDAV-99summary",
                           "ETF_SE-WebDAV-3extension",
                           "ETF_SE-WebDAV-5open-access",
                           "ETF_SE-WebDAV-6crt-write", 
                           "ETF_SE-WebDAV-7macaroon",
                           "ETF_SE-WebDAV-9summary",
                        "ETF_SE-XRootD-1connection", "ETF_SE-XRootD-3version",
                           "ETF_SE-XRootD-4crt-read",
                           "ETF_SE-XRootD-5crt-contain",
                           "ETF_SE-XRootD-6crt-access",
                           "ETF_SE-XRootD-7crt-write",
                           "ETF_SE-XRootD-8crt-directory",
                           "ETF_SE-XRootD-9federation",
                           "ETF_SE-XRootD-14tkn-read",
                           "ETF_SE-XRootD-15tkn-contain",
                           "ETF_SE-XRootD-16tkn-access",
                           "ETF_SE-XRootD-17tkn-write",
                           "ETF_SE-XRootD-18tkn-directory",
                           "ETF_SE-XRootD-99summary",
                        "ETF_SE-xrootd-version", "ETF_SE-xrootd-connection",
                           "ETF_SE-xrootd-read", "ETF_SE-xrootd-contain",
                        "ETF_CONDOR-JobSubmit/x509",
                           "ETF_WN-env", "ETF_WN-basic", "ETF_WN-cvmfs",
                           "ETF_WN-squid", "ETF_WN-frontier",
                           "ETF_WN-isolation",
                           "ETF_WN-xrootd-access", "ETF_WN-xrootd-fallback",
                           "ETF_WN-analysis", "ETF_WN-mc",
                           "ETF_WN-psst-test", "ETF_CONDOR-Ping",
                        "ETF_DNS-IPv6",
                        "ETF_CONDOR-JobSubmit/token",
                           "ETF_WN-01basic", "ETF_WN-02cvmfs",
                           "ETF_WN-03siteconf", "ETF_WN-05apptainer",
                           "ETF_WN-21squid", "ETF_WN-22frontier",
                           "ETF_WN-25dataaccess",
                           "ETF_WN-99summary",
                        "***Othr***" ];
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

function dateString3(timeInSeconds) {
   // function to return an abbreviated date string like "2017/01/01 00:00"
   var timeStr = "";

   var timeObj = new Date( timeInSeconds * 1000 );

   timeStr = timeObj.getUTCFullYear() + '/' +
      ("0" + (timeObj.getUTCMonth() + 1)).slice(-2) + '/' +
      ("0" + timeObj.getUTCDate()).slice(-2) + ' ' +
      ("0" + timeObj.getUTCHours()).slice(-2) + ':' +
      ("0" + timeObj.getUTCMinutes()).slice(-2);

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

function canvas_clicked(id, event) {

   var myArray = id.id.split("/");
   if ( myArray.length >= 4 ) {
      var myMetric = myArray[0];
      var mySecton = myArray[1];
      var mySitHst = myArray[2];
      var mySitTyp = myArray[3];
   } else if ( myArray.length >= 3 ) {
      var myMetric = myArray[0];
      var mySecton = myArray[1];
      var mySitHst = myArray[2];
      var mySitTyp = "All";
   } else {
      return false;
   }

   var myTime = new Date( myData.time * 1000 );
   myTime.setUTCHours(0, 0, 0, 0);
   var myTIS = Math.trunc( myTime.valueOf() / 1000 );
   var boundingBox = id.getBoundingClientRect();
   var xcoord = event.clientX - boundingBox.left;
   var myOffset;
   var myTarget;
   var myPeriod;
   var myTrailr;
   if ( mySecton == "pmonth" ) {
      myOffset = myTIS - ( 38 * 86400 );
      myTarget = Math.min(119, Math.max(0, Math.trunc(
                    ( xcoord - 1 ) * 120 / ( sizeCnvs[0] - 1 ) ) ) );
      myPeriod = 6 * 60 * 60;
      myTrailr = "6hour";
   } else if ( mySecton == "pweek" ) {
      myOffset = myTIS - ( 8 * 86400 );
      myTarget = Math.min(165, Math.max(0, Math.trunc(
                    ( xcoord - 1 ) * 168 / ( sizeCnvs[1] - 1 ) ) ) );
      myPeriod = 60 * 60;
      myTrailr = "1hour";
   } else if ( mySecton == "yrday" ) {
      myOffset = myTIS - 86400;
      myTarget = Math.min(95, Math.max(0, Math.trunc(
                    ( xcoord - 1 ) * 96 / ( sizeCnvs[2] - 1 ) ) ) );
      myPeriod = 15 * 60;
      myTrailr = "15min";
   } else if ( mySecton == "today" ) {
      myOffset = myTIS;
      myTarget = Math.min(95, Math.max(0, Math.trunc(
                    ( xcoord - 1 ) * 96 / ( sizeCnvs[3] - 1 ) ) ) );
      myPeriod = 15 * 60;
      myTrailr = "15min";
   } else if ( mySecton == "fweek" ) {
      myOffset = myTIS + 86400;
      myTarget = Math.min(167, Math.max(0, Math.trunc(
                    ( xcoord - 1 ) * 168 / ( sizeCnvs[4] - 1 ) ) ) );
      myPeriod = 60 * 60;
      myTrailr = "1hour";
   } else {
      return false;
   }

   var myStart;
   var myEnd;
   var myBin;
   if ( myMetric == "Downtime" ) {
      myStart = myOffset + ((myTarget + 2) * myPeriod);
      myBin = Math.trunc( myStart / 900 );
      id.href = 'https://cmssst.web.cern.ch/cgi-bin' +
         '/log/down15min/' + myBin + '/' + mySitHst + '/*/day+0';
   } else if ( myMetric == "SAM1day" ) {
      myStart = myOffset + (myTarget * myPeriod) + (myPeriod/2);
      myBin = Math.trunc( myStart / 86400 );
      id.href = 'https://cmssst.web.cern.ch/cgi-bin' +
         '/log/sam1day/' + myBin + '/' + mySitHst + '/*/0+0';
   } else if ( myMetric == "HC1day" ) {
      myStart = myOffset + (myTarget * myPeriod) + (myPeriod/2);
      myBin = Math.trunc( myStart / 86400 );
      id.href = 'https://cmssst.web.cern.ch/cgi-bin' +
         '/log/hc1day/' + myBin + '/' + mySitHst + '/site/0+0';
   } else if ( myMetric == "FTS1day" ) {
      myStart = myOffset + (myTarget * myPeriod) + (myPeriod/2);
      myBin = Math.trunc( myStart / 86400 );
      id.href = 'https://cmssst.web.cern.ch/cgi-bin' +
         '/log/links1day/' + myBin + '/' + mySitHst + '/*/0+0';
   } else if ( myMetric == "SR1day" ) {
      myStart = myOffset + (myTarget * myPeriod) + (myPeriod/2);
      myBin = Math.trunc( myStart / 86400 );
      id.href = 'https://cmssst.web.cern.ch/cgi-bin' +
         '/log/sr1day/' + myBin + '/' + mySitHst + '/site/0+0';
   } else if ( myMetric.substring(4, 10) == "Status" ) {
      myStart = myOffset + ((myTarget + 2) * myPeriod);
      myBin = Math.trunc( myStart / 900 );
      id.href = 'https://cmssst.web.cern.ch/cgi-bin' +
         '/log/sts15min/' + myBin + '/' + mySitHst + '/*/day+0';
   } else if ( myMetric == "manLifeStatus" ) {
      if ( mySecton == "today" ) {
         id.href = 'https://cmssst.web.cern.ch/cgi-bin/set/LifeStatus/' +
            mySitHst;
      }
   } else if ( myMetric == "manProdStatus" ) {
      if ( mySecton == "today" ) {
         id.href = 'https://cmssst.web.cern.ch/cgi-bin/set/ProdStatus/' +
            mySitHst;
      }
   } else if ( myMetric == "manCrabStatus" ) {
      if ( mySecton == "today" ) {
         id.href = 'https://cmssst.web.cern.ch/cgi-bin/set/CrabStatus/' +
            mySitHst;
      }
   } else if ( myMetric == "manRucioStatus" ) {
      if ( mySecton == "today" ) {
         id.href = 'https://cmssst.web.cern.ch/cgi-bin/set/RucioStatus/' +
            mySitHst;
      }
   } else if ( myMetric == "SAMsite" ) {
      myStart = myOffset + (myTarget * myPeriod) + (myPeriod/2);
      myBin = Math.trunc( myStart / myPeriod );
      id.href = 'https://cmssst.web.cern.ch/cgi-bin' +
         '/log/sam' + myTrailr + '/' + myBin + '/' + mySitHst + '/*/1+2';
   } else if ( myMetric == "HammerCloud" ) {
      myStart = myOffset + (myTarget * myPeriod) + (myPeriod/2);
      myBin = Math.trunc( myStart / myPeriod );
      id.href = 'https://cmssst.web.cern.ch/cgi-bin' +
         '/log/hc' + myTrailr + '/' + myBin + '/' + mySitHst + '/*/1+2';
   } else if ( myMetric == "FTSsite" ) {
      myStart = myOffset + (myTarget * myPeriod) + (myPeriod/2);
      myBin = Math.trunc( myStart / myPeriod );
      id.href = 'https://cmssst.web.cern.ch/cgi-bin' +
         '/log/fts' + myTrailr + '/' + myBin + '/' + mySitHst + '/*/1+2';
   } else if ( myMetric =="FTSsource" ) {
      myStart = myOffset + ( ( myTarget - 1 ) * myPeriod );
      myEnd = myOffset + ( ( myTarget + 2 ) * myPeriod );
      id.href = 'https://monit-grafana.cern.ch/d/CIjJHKdGk/fts-transfers-es?' +
         'orgId=20&from=' + myStart + '000&to=' + myEnd + '000&var-group_by=' +
         'endpnt&var-vo=cms&var-src_country=All&var-dst_country=All&var-src_' +
         'site=All&var-dst_site=All&var-fts_server=All&var-bin=1h&var-includ' +
         'e=&var-filters=data.src_hostname|=|' + mySitHst;
   } else if ( myMetric =="FTSdestination" ) {
      myStart = myOffset + ( ( myTarget - 1 ) * myPeriod );
      myEnd = myOffset + ( ( myTarget + 2 ) * myPeriod );
      id.href = 'https://monit-grafana.cern.ch/d/CIjJHKdGk/fts-transfers-es?' +
         'orgId=20&from=' + myStart + '000&to=' + myEnd + '000&var-group_by=' +
         'endpnt&var-vo=cms&var-src_country=All&var-dst_country=All&var-src_' +
         'site=All&var-dst_site=All&var-fts_server=All&var-bin=1h&var-includ' +
         'e=&var-filters=data.dst_hostname|=|' + mySitHst;
   } else if ( myMetric =="SAMservice" ) {
      myStart = myOffset + ( ( myTarget - 1 ) * myPeriod );
      myEnd = myOffset + ( ( myTarget + 2 ) * myPeriod );
      id.href = 'https://monit-grafana.cern.ch/d/m7XtZsEZk4/wlcg-sitemon-his' +
         'torical-tests?orgId=20&var-vo=cms&var-dst_tier=All&var-dst_experim' +
         'ent_site=' + myData.site + '&var-dst_hostname=' + mySitHst + '&var' +
         '-service_flavour=' + mySitTyp + '&from=' + myStart.toString() +
         '000&to=' + myEnd.toString() + '000';
   }

   return false;
}

function writeTable() {

   var myWidth = 1600;
   if ( window.innerWidth ) {
      myWidth = window.innerWidth;
   }
   if ( myWidth < 1440 ) {
      // compact page/view:
      var fontHdrSite = 'font-size: 20px; font-weight: 700;';
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
      var fontHdrOthr = 'font-size: 20px; font-weight: 600;';
      var fontSiteName = 'font-size: 18px; font-weight: 500;';
      // Previous Month: 2*(4*30)+30+2   Magnified: 4*(4*30)+2*30
      // Previous Week:    (7*24)+28+2   Magnified: 4*(7*24)+2*28
      // Yesterday:      2*(24*4)+24+2   Magnified: 4*(24*4)+2*24
      // Today:          3*(24*4)+24+2   Magnified: 5*(24*4)+2*24
      // Following Week:   (7*24)+28+1   Magnified: 4*(7*24)+2*28
      sizeCnvs = [ "272", "198", "218", "314", "197" ];
      var sizeMagn = [ "540", "728", "432", "528", "728" ];
      noBins  = [ 2, 1, 2, 3, 1 ];
   } else {
      // 4k display (QSXGA and higher):
      var fontHdrSite = 'font-size: 26px; font-weight: 700;';
      var fontHdrOthr = 'font-size: 24px; font-weight: 700;';
      var fontSiteName = 'font-size: 20px; font-weight: 500;';
      // Previous Month: 3*(4*30)+30+2   Magnified: 4*(4*30)+2*30
      // Previous Week:  2*(7*24)+28+2   Magnified: 4*(7*24)+2*28
      // Yesterday:      3*(24*4)+24+2   Magnified: 4*(24*4)+2*24
      // Today:          5*(24*4)+24+2   Magnified: 5*(24*4)+2*24
      // Following Week:   (7*24)+28+1   Magnified: 4*(7*24)+2*28
      sizeCnvs = [ "392", "366", "314", "506", "197" ];
      var sizeMagn = [ "540", "728", "432", "528", "728" ];
      noBins  = [ 3, 2, 3, 5, 1 ];
   }

   // add a line in case there is a message:
   if ( myData.msg != '' ) {
      var myTableStr = '<SPAN STYLE="color:blue; font-weight:bold;">' +
                          myData.msg + '</SPAN>\n<BR>\n<BR>\n';
   } else {
      var myTableStr = ''
   }

   // compose table header:
   myTableStr += '<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="0">\n<TR>\n' +
      '   <TH NOWRAP ALIGN="left"><SPAN STYLE="' + fontHdrSite + '">Metric</' +
      'SPAN>\n   <TH NOWRAP><BIG>&nbsp;</BIG>\n   <TH NOWRAP ALIGN="center">' +
      '<SPAN STYLE="' + fontHdrOthr + '">Prev. Month</SPAN>\n   <TH NOWRAP A' +
      'LIGN="center"><SPAN STYLE="' + fontHdrOthr + '">Previous Week</SPAN>' +
      '\n   <TH NOWRAP ALIGN="center"><SPAN STYLE="' + fontHdrOthr +
      '">Yesterday</SPAN>\n   <TH NOWRAP ALIGN="center"><SPAN STYLE="' +
      fontHdrOthr + '">UTC Today</SPAN>\n   <TH NOWRAP ALIGN="center"><SPAN ' +
      'STYLE="' + fontHdrOthr + '">Following Week</SPAN>\n';


   // loop over metrics in siteMetricOrder and write a table row for each:
   for ( var mCnt=0; mCnt < siteMetricOrder.length; mCnt+=1 ) {
      if ( siteMetricOrder[mCnt] == "***LINE***" ) {
         myTableStr += '<TR>\n   <TD COLSPAN="7" bgcolor="#000000" STYLE="li' +
            'ne-height:2px;">&nbsp;\n<TR>\n   <TD COLSPAN="7" bgcolor="#FFFF' +
            'FF" STYLE="line-height:2px;">&nbsp;\n';
      } else if ( siteMetricOrder[mCnt] == "***GGUS***" ) {
         myTableStr += '<TR>\n   <TD ALIGN="left"><SPAN STYLE="' +
            fontSiteName + '">GGUS tickets:</SPAN>\n   <TD NOWRAP>&nbsp;';
         var myTime = new Date( myData.time * 1000 );
         myTime.setUTCHours(0, 0, 0, 0);
         var midnight = Math.trunc( myTime.valueOf() / 1000 );
         myData.ggus.sort(function(a,b){return a-b});
         var iTckt = 0;
         // GGUS tickets opened more than 38 days ago:
         myTableStr += '\n   <TD>';
         var fDiv = 0;
         while ( iTckt < myData.ggus.length ) {
            if ( myData.ggus[iTckt][1] < midnight - 3283200 ) {
               if ( fDiv == 0 ) {
                  myTableStr += '<DIV STYLE="text-align: left">[<A HREF="htt' +
                     'ps://helpdesk.ggus.eu/#ticket/zoom/' +
                     myData.ggus[iTckt][0] + '">' + myData.ggus[iTckt][0] +
                     '</A>]';
                  fDiv = 1;
               } else {
                  myTableStr += '&nbsp;[<A HREF="https://helpdesk.ggus.eu/#t' +
                     'icket/zoom/' + myData.ggus[iTckt][0] + '">' +
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
            if ( myData.ggus[iTckt][1] < midnight - 691200 ) {
               if ( fDiv == 0 ) {
                  myTableStr += '<DIV STYLE="text-align: center">[<A HREF="h' +
                     'ttps://helpdesk.ggus.eu/#ticket/zoom/' +
                     myData.ggus[iTckt][0] + '">' + myData.ggus[iTckt][0] +
                     '</A>]';
                  fDiv = 1;
               } else {
                  myTableStr += '&nbsp;[<A HREF="https://helpdesk.ggus.eu/#t' +
                     'icket/zoom/' + myData.ggus[iTckt][0] + '">' +
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
            if ( myData.ggus[iTckt][1] < midnight - 86400 ) {
               if ( fDiv == 0 ) {
                  myTableStr += '<DIV STYLE="text-align: center">[<A HREF="h' +
                     'ttps://helpdesk.ggus.eu/#ticket/zoom/' +
                     myData.ggus[iTckt][0] + '">' + myData.ggus[iTckt][0] +
                     '</A>]';
                  fDiv = 1;
               } else {
                  myTableStr += '&nbsp;[<A HREF="https://helpdesk.ggus.eu/#t' +
                     'icket/zoom/' + myData.ggus[iTckt][0] + '">' +
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
            if ( myData.ggus[iTckt][1] < midnight ) {
               if ( fDiv == 0 ) {
                  myTableStr += '<DIV STYLE="text-align: center">[<A HREF="h' +
                     'ttps://helpdesk.ggus.eu/#ticket/zoom/' +
                     myData.ggus[iTckt][0] + '">' + myData.ggus[iTckt][0] +
                     '</A>]';
                  fDiv = 1;
               } else {
                  myTableStr += '&nbsp;[<A HREF="https://helpdesk.ggus.eu/#t' +
                     'icket/zoom/' + myData.ggus[iTckt][0] + '">' +
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
                  's://helpdesk.ggus.eu/#ticket/zoom/' +
                  myData.ggus[iTckt][0] + '">' + myData.ggus[iTckt][0] +
                  '</A>]';
               fDiv = 1;
            } else {
               myTableStr += '&nbsp;[<A HREF="https://helpdesk.ggus.eu/#tick' +
                  'et/zoom/' + myData.ggus[iTckt][0] + '">' +
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
         myTableStr += '<TR>\n   <TD NOWRAP ALIGN="left"><SPAN STYLE="' +
            fontSiteName + '">' + nName + '</SPAN>\n   <TD NOWRAP>&nbsp;\n';
         // second, previous month's, column:
         myTableStr += '   <TD><A CLASS="toolTip1" HREF="javascript:void(0);' +
            '" ID="' + siteMetricOrder[mCnt] + '/pmonth/' + myData.site +
            '" ONMOUSEDOWN="canvas_clicked(this, event)"><CANVAS ID="cnvs_' +
            siteMetricOrder[mCnt] + '_s1" WIDTH="' + sizeCnvs[0] +
            '" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CEL' +
            'LPADDING="0" CELLSPACING="0"><TR><TD COLSPAN="2" ALIGN="center"' +
            '><B>Previous Month of ' + nName + '</B><TR><TD COLSPAN="2">&nbs' +
            'p;<TR><TD COLSPAN="2"><CANVAS ID="cnvs_' + siteMetricOrder[mCnt] +
            '_m1" WIDTH="' + sizeMagn[0] + '" HEIGHT="36"></CANVAS><TR><TD A' +
            'LIGN="left">' + dateString2(myData.time - 38 * 86400) + '<TD AL' +
            'IGN="right">' + dateString2(myData.time - 9 * 86400) + '</TABLE' +
            '></SPAN></A>\n';
         // third, previous week's, column:
         myTableStr += '   <TD><A CLASS="toolTip2" HREF="javascript:void(0);' +
            '" ID="' + siteMetricOrder[mCnt] + '/pweek/' + myData.site +
            '" ONMOUSEDOWN="canvas_clicked(this, event)"><CANVAS ID="cnvs_' +
            siteMetricOrder[mCnt] + '_s2" WIDTH="' + sizeCnvs[1] +
            '" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CEL' +
            'LPADDING="0" CELLSPACING="0"><TR><TD COLSPAN="2" ALIGN="center"' +
            '><B>Previous Week of ' + nName + '</B><TR><TD COLSPAN="2">&nbsp' +
            ';<TR><TD COLSPAN="2"><CANVAS ID="cnvs_' + siteMetricOrder[mCnt] +
            '_m2" WIDTH="' + sizeMagn[1] + '" HEIGHT="36"></CANVAS><TR><TD A' +
            'LIGN="left">' + dateString2(myData.time - 8 * 86400) + '<TD ALI' +
            'GN="right">' + dateString2(myData.time - 2 * 86400) + '</TABLE>' +
            '</SPAN></A>\n';
         // fourth, yesterday's, column:
         myTableStr += '   <TD><A CLASS="toolTip3" HREF="javascript:void(0);' +
            '" ID="' + siteMetricOrder[mCnt] + '/yrday/' + myData.site +
            '" ONMOUSEDOWN="canvas_clicked(this, event)"><CANVAS ID="cnvs_' +
            siteMetricOrder[mCnt] + '_s3" WIDTH="' + sizeCnvs[2] +
            '" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CEL' +
            'LPADDING="0" CELLSPACING="0"><TR><TD COLSPAN="2" ALIGN="center"' +
            '><B>Yesterday (' + dateString2( myData.time - 86400 ) + ') of ' +
            nName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSPAN="2"><CANV' +
            'AS ID="cnvs_' + siteMetricOrder[mCnt] + '_m3" WIDTH="' +
            sizeMagn[2] + '" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">00:00' +
            '<TD ALIGN="right">24:00</TABLE></SPAN></A>\n';
         // fifth, today's, column:
         myTableStr += '   <TD><A CLASS="toolTip4" HREF="javascript:void(0);' +
            '" ID="' + siteMetricOrder[mCnt] + '/today/' + myData.site +
            '" ONMOUSEDOWN="canvas_clicked(this, event)"><CANVAS ID="cnvs_' +
            siteMetricOrder[mCnt] + '_s4" WIDTH="' + sizeCnvs[3] +
            '" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CEL' +
            'LPADDING="0" CELLSPACING="0"><TR><TD COLSPAN="2" ALIGN="center"' +
            '><B>Today (' + dateString2( myData.time ) + ') of ' + nName +
            '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSPAN="2"><CANVAS ID="c' +
            'nvs_' + siteMetricOrder[mCnt] + '_m4" WIDTH="' + sizeMagn[3] +
            '" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">00:00<TD ALIGN="rig' +
            'ht">24:00</TABLE></SPAN></A>\n';
         // sixth, following week's column:
         myTableStr += '   <TD><A CLASS="toolTip5" HREF="javascript:void(0);' +
            '" ID="' + siteMetricOrder[mCnt] + '/fweek/' + myData.site +
            '" ONMOUSEDOWN="canvas_clicked(this, event)"><CANVAS ID="cnvs_' +
            siteMetricOrder[mCnt] + '_s5" WIDTH="' + sizeCnvs[4] +
            '" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDER="0" CEL' +
            'LPADDING="0" CELLSPACING="0"><TR><TD COLSPAN="2" ALIGN="center"' +
            '><B>Following Week of ' + nName + '</B><TR><TD COLSPAN="2">&nbs' +
            'p;<TR><TD COLSPAN="2"><CANVAS ID="cnvs_' + siteMetricOrder[mCnt] +
            '_m5" WIDTH="' + sizeMagn[4] + '" HEIGHT="36"></CANVAS><TR><TD A' +
            'LIGN="left">' + dateString2( myData.time + 1 * 86400 ) +
            '<TD ALIGN="right">' + dateString2( myData.time + 7 * 86400 ) +
            '</TABLE></SPAN></A>\n';
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
               mName + '_s1" WIDTH="' + sizeCnvs[0] + '" HEIGHT="18"></CANVA' +
               'S><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPADDING="0" CELLS' +
               'PACING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Previous Mo' +
               'nth of ' + mName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD CO' +
               'LSPAN="2"><CANVAS ID="cnvs_' + mName + '_m1" WIDTH="' +
               sizeMagn[0] + '" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">' +
               dateString2( myData.time - 38 * 86400 ) + '<TD ALIGN="right">' +
               dateString2( myData.time - 9 * 86400 ) +
               '</TABLE></SPAN></A>\n';
            // third, previous week's, column:
            myTableStr += '   <TD><A CLASS="toolTip2"><CANVAS ID="cnvs_' +
               mName + '_s2" WIDTH="' + sizeCnvs[1] + '" HEIGHT="18"></CANVA' +
               'S><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPADDING="0" CELLS' +
               'PACING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Previous We' +
               'ek of ' + mName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COL' +
               'SPAN="2"><CANVAS ID="cnvs_' + mName + '_m2" WIDTH="' +
               sizeMagn[1] + '" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">' +
               dateString2( myData.time - 8 * 86400 ) + '<TD ALIGN="right">' +
               dateString2( myData.time - 2 * 86400 ) +
               '</TABLE></SPAN></A>\n';
            // fourth, yesterday's, column:
            myTableStr += '   <TD><A CLASS="toolTip3"><CANVAS ID="cnvs_' +
               mName + '_s3" WIDTH="' + sizeCnvs[2] + '" HEIGHT="18"></CANVA' +
               'S><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPADDING="0" CELLS' +
               'PACING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Yesterday (' +
               dateString2( myData.time - 86400 ) + ') of ' + mName +
               '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSPAN="2"><CANVAS ID' +
               '="cnvs_' + mName + '_m3" WIDTH="' + sizeMagn[2] + '" HEIGHT=' +
               '"36"></CANVAS><TR><TD ALIGN="left">00:00<TD ALIGN="right">24' +
               ':00</TABLE></SPAN></A>\n';
            // fifth, today's, column:
            myTableStr += '   <TD><A CLASS="toolTip4"><CANVAS ID="cnvs_' +
               mName + '_s4" WIDTH="' + sizeCnvs[3] + '" HEIGHT="18"></CANVA' +
               'S><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPADDING="0" CELLS' +
               'PACING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Today (' +
               dateString2( myData.time ) + ') of ' + mName + '</B><TR><TD C' +
               'OLSPAN="2">&nbsp;<TR><TD COLSPAN="2"><CANVAS ID="cnvs_' +
               mName + '_m4" WIDTH="' + sizeMagn[3] + '" HEIGHT="36"></CANVA' +
               'S><TR><TD ALIGN="left">00:00<TD ALIGN="right">24:00</TABLE><' +
               '/SPAN></A>\n';
            // sixth, following week's column:
            myTableStr += '   <TD><A CLASS="toolTip5"><CANVAS ID="cnvs_' +
               mName + '_s5" WIDTH="' + sizeCnvs[4] + '" HEIGHT="18"></CANVA' +
               'S><SPAN><TABLE WIDTH="100%" BORDER="0" CELLPADDING="0" CELLS' +
               'PACING="0"><TR><TD COLSPAN="2" ALIGN="center"><B>Following W' +
               'eek of ' + mName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD CO' +
               'LSPAN="2"><CANVAS ID="cnvs_' + mName + '_m5" WIDTH="' +
               sizeMagn[4] + '" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">' +
               dateString2( myData.time + 1 * 86400 ) + '<TD ALIGN="right">' +
               dateString2( myData.time + 7 * 86400 ) +
               '</TABLE></SPAN></A>\n';
         }
      } else if ( siteMetricOrder[mCnt] == "**Elmnts**" ) {
         // loop over site elements and write the metrics of each:
         for ( var cnt=0; cnt < myData.elements.length; cnt+=1 ) {
            // concatenate host and type
            var eName = myData.elements[cnt].host + ' / ' +
               myData.elements[cnt].type;

            myTableStr += '<TR>\n   <TD COLSPAN="7" bgcolor="#000000" STYLE=' +
               '"line-height:2px;">&nbsp;\n<TR>\n   <TD COLSPAN="7" bgcolor=' +
               '"#FFFFFF" STYLE="line-height:8px;">&nbsp;\n<TR>\n   <TD COLS' +
               'PAN="7" bgcolor="#FFFFFF" ALIGN="left"><SPAN STYLE="' +
               fontSiteName + '">' + eName + '</SPAN>\n';
            eName = myData.elements[cnt].host + '/' + myData.elements[cnt].type;
            eName = eName.replace(' ', '');
            // loop over metrics of element:
            for ( var iCnt=0; iCnt < srvcMetricOrder.length; iCnt+=1 ) {
               if ( srvcMetricOrder[iCnt] == "***LINE***" ) {
                  myTableStr += '<TR>\n   <TD COLSPAN="7" bgcolor="#000000" ' +
                     'STYLE="border-left:24px solid white; line-height:2px;"' +
                     '>&nbsp;</DIV>\n<TR>\n   <TD COLSPAN="7" bgcolor="#FFFF' +
                     'FF" STYLE="line-height:2px;">&nbsp;\n';
               } else if ( srvcMetricOrder[iCnt] in
                                               myData.elements[cnt].metrics ) {
                  if ( srvcMetricOrder[iCnt] in srvcMetricLabel ) {
                     myTableStr += '<TR>\n   <TD NOWRAP ALIGN="left"> &nbsp ' +
                        '&nbsp ' + srvcMetricLabel[ srvcMetricOrder[iCnt] ] +
                        '\n   <TD NOWRAP>&nbsp;\n';
                  } else {
                     myTableStr += '<TR>\n   <TD NOWRAP ALIGN="left"> &nbsp ' +
                        '&nbsp ' + srvcMetricOrder[iCnt] + '\n   <TD NOWRAP>' +
                        '&nbsp;\n';
                  }
                  // second, previous month's, column:
                  myTableStr += '   <TD><A CLASS="toolTip1" ' + 'HREF="javas' +
                     'cript:void(0);" ID="' + srvcMetricOrder[iCnt] +
                     '/pmonth/' + myData.elements[cnt].host + '/' +
                     myData.elements[cnt].type + '" ONMOUSEDOWN="canvas_clic' +
                     'ked(this, event)"><CANVAS ID="cnvs_' + eName + '_' +
                     srvcMetricOrder[iCnt] + '_s1" WIDTH="' + sizeCnvs[0] +
                     '" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDE' +
                     'R="0" CELLPADDING="0" CELLSPACING="0"><TR><TD COLSPAN=' +
                     '"2" ALIGN="center"><B>Previous Month of ' +
                     srvcMetricOrder[iCnt] + '</B><TR><TD COLSPAN="2">&nbsp;' +
                     '<TR><TD COLSPAN="2"><CANVAS ID="cnvs_' + eName + '_' +
                     srvcMetricOrder[iCnt] + '_m1" WIDTH="' + sizeMagn[0] +
                     '" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">' +
                     dateString2(myData.time - 38 * 86400) + '<TD ALIGN="rig' +
                     'ht">' + dateString2(myData.time - 9 * 86400) +
                     '</TABLE></SPAN></A>\n';
                  // third, previous week's, column:
                  myTableStr += '   <TD><A CLASS="toolTip2" ' + 'HREF="javas' +
                     'cript:void(0);" ID="' + srvcMetricOrder[iCnt] +
                     '/pweek/' + myData.elements[cnt].host + '/' +
                     myData.elements[cnt].type + '" ONMOUSEDOWN="canvas_clic' +
                     'ked(this, event)"><CANVAS ID="cnvs_' + eName + '_' +
                     srvcMetricOrder[iCnt] + '_s2" WIDTH="' + sizeCnvs[1] +
                     '" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDE' +
                     'R="0" CELLPADDING="0" CELLSPACING="0"><TR><TD COLSPAN=' +
                     '"2" ALIGN="center"><B>Previous Week of ' +
                     srvcMetricOrder[iCnt] + '</B><TR><TD COLSPAN="2">&nbsp;' +
                     '<TR><TD COLSPAN="2"><CANVAS ID="cnvs_' + eName + '_' +
                     srvcMetricOrder[iCnt] + '_m2" WIDTH="' + sizeMagn[1] +
                     '" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">' +
                     dateString2(myData.time - 8 * 86400) + '<TD ALIGN="righ' +
                     't">' + dateString2(myData.time - 2 * 86400) +
                     '</TABLE></SPAN></A>\n';
                  // fourth, yesterday's, column:
                  myTableStr += '   <TD><A CLASS="toolTip3" ' + 'HREF="javas' +
                     'cript:void(0);" ID="' + srvcMetricOrder[iCnt] +
                     '/yrday/' + myData.elements[cnt].host + '/' +
                     myData.elements[cnt].type + '" ONMOUSEDOWN="canvas_clic' +
                     'ked(this, event)"><CANVAS ID="cnvs_' + eName + '_' +
                     srvcMetricOrder[iCnt] + '_s3" WIDTH="' + sizeCnvs[2] +
                     '" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDE' +
                     'R="0" CELLPADDING="0" CELLSPACING="0"><TR><TD COLSPAN=' +
                     '"2" ALIGN="center"><B>Yesterday (' +
                     dateString2(myData.time - 86400) + ') of ' +
                     srvcMetricOrder[iCnt] + '</B><TR><TD COLSPAN="2">&nbsp;' +
                     '<TR><TD COLSPAN="2"><CANVAS ID="cnvs_' + eName + '_' +
                     srvcMetricOrder[iCnt] + '_m3" WIDTH="' + sizeMagn[2] +
                     '" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">00:00<TD A' +
                     'LIGN="right">24:00</TABLE></SPAN></A>\n';
                  // fifth, today's, column:
                  myTableStr += '   <TD><A CLASS="toolTip4" ' + 'HREF="javas' +
                     'cript:void(0);" ID="' + srvcMetricOrder[iCnt] +
                     '/today/' + myData.elements[cnt].host + '/' +
                     myData.elements[cnt].type + '" ONMOUSEDOWN="canvas_clic' +
                     'ked(this, event)"><CANVAS ID="cnvs_' + eName + '_' +
                     srvcMetricOrder[iCnt] + '_s4" WIDTH="' + sizeCnvs[3] +
                     '" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDE' +
                     'R="0" CELLPADDING="0" CELLSPACING="0"><TR><TD COLSPAN=' +
                     '"2" ALIGN="center"><B>Today (' +
                     dateString2( myData.time ) + ') of ' +
                     srvcMetricOrder[iCnt] + '</B><TR><TD COLSPAN="2">&nbsp;' +
                     '<TR><TD COLSPAN="2"><CANVAS ID="cnvs_' + eName + '_' +
                     srvcMetricOrder[iCnt] + '_m4" WIDTH="' + sizeMagn[3] +
                     '" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">00:00<TD A' +
                     'LIGN="right">24:00</TABLE></SPAN></A>\n';
                  // sixth, following week's column:
                  myTableStr += '   <TD><A CLASS="toolTip5" ' + 'HREF="javas' +
                     'cript:void(0);" ID="' + srvcMetricOrder[iCnt] +
                     '/fweek/' + myData.elements[cnt].host + '/' +
                     myData.elements[cnt].type + '" ONMOUSEDOWN="canvas_clic' +
                     'ked(this, event)"><CANVAS ID="cnvs_' + eName + '_' +
                     srvcMetricOrder[iCnt] + '_s5" WIDTH="' + sizeCnvs[4] +
                     '" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BORDE' +
                     'R="0" CELLPADDING="0" CELLSPACING="0"><TR><TD COLSPAN=' +
                     '"2" ALIGN="center"><B>Following Week of ' +
                     srvcMetricOrder[iCnt] + '</B><TR><TD COLSPAN="2">&nbsp;' +
                     '<TR><TD COLSPAN="2"><CANVAS ID="cnvs_' + eName + '_' +
                     srvcMetricOrder[iCnt] + '_m5" WIDTH="' + sizeMagn[4] +
                     '" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">' +
                     dateString2( myData.time + 1 * 86400 ) + '<TD ALIGN="ri' +
                     'ght">' + dateString2( myData.time + 7 * 86400 ) +
                     '</TABLE></SPAN></A>\n';
               } else if ( srvcMetricOrder[iCnt] == "***Othr***" ) {
                  // loop over element metrics not in srvcMetricOrder:
                  for ( var mName in myData.elements[cnt].metrics ) {
                     if ( srvcMetricOrder.indexOf(mName) >= 0 ) {
                        continue;
                     }
                     if ( mName in srvcMetricLabel ) {
                        myTableStr += '<TR>\n   <TD NOWRAP ALIGN="left"> &nb' +
                           'sp &nbsp ' + srvcMetricLabel[mName] +
                           '\n   <TD NOWRAP>&nbsp;\n';
                     } else {
                        myTableStr += '<TR>\n   <TD NOWRAP ALIGN="left"> &nb' +
                           'sp &nbsp ' + mName + '\n   <TD NOWRAP>&nbsp;\n';
                     }
                     // second, previous month's, column:
                     myTableStr += '   <TD><A CLASS="toolTip1" ' +
                        'HREF="javascript:void(0);" ID="' + mName +
                        '/pmonth/' + myData.elements[cnt].host + '/' +
                        myData.elements[cnt].type + '" ONMOUSEDOWN="canvas_c' +
                        'licked(this, event)"><CANVAS ID="cnvs_' + eName +
                        '_' + mName + '_s1" WIDTH="' + sizeCnvs[0] +
                        '" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BO' +
                        'RDER="0" CELLPADDING="0" CELLSPACING="0"><TR><TD CO' +
                        'LSPAN="2" ALIGN="center"><B>Previous Month of ' +
                        mName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSP' +
                        'AN="2"><CANVAS ID="cnvs_' + eName + '_' + mName +
                        '_m1" WIDTH="' + sizeMagn[0] +
                        '" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">' +
                        dateString2(myData.time - 38 * 86400) +
                        '<TD ALIGN="right">' +
                        dateString2(myData.time - 9 * 86400) +
                        '</TABLE></SPAN></A>\n';
                     // third, previous week's, column:
                     myTableStr += '   <TD><A CLASS="toolTip2" ' +
                        'HREF="javascript:void(0);" ID="' + mName + '/pweek/' +
                        myData.elements[cnt].host + '/' +
                        myData.elements[cnt].type + '" ONMOUSEDOWN="canvas_c' +
                        'licked(this, event)"><CANVAS ID="cnvs_' + eName +
                        '_' + mName + '_s2" WIDTH="' + sizeCnvs[1] +
                        '" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BO' +
                        'RDER="0" CELLPADDING="0" CELLSPACING="0"><TR><TD CO' +
                        'LSPAN="2" ALIGN="center"><B>Previous Week of ' +
                        mName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSP' +
                        'AN="2"><CANVAS ID="cnvs_' + eName + '_' + mName +
                        '_m2" WIDTH="' + sizeMagn[1] +
                        '" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">' +
                        dateString2(myData.time - 8 * 86400) +
                        '<TD ALIGN="right">' +
                        dateString2(myData.time - 2 * 86400) +
                        '</TABLE></SPAN></A>\n';
                     // fourth, yesterday's, column:
                     myTableStr += '   <TD><A CLASS="toolTip3" ' +
                        'HREF="javascript:void(0);" ID="' + mName + '/yrday/' +
                        myData.elements[cnt].host + '/' +
                        myData.elements[cnt].type + '" ONMOUSEDOWN="canvas_c' +
                        'licked(this, event)"><CANVAS ID="cnvs_' + eName +
                        '_' + mName + '_s3" WIDTH="' + sizeCnvs[2] +
                        '" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BO' +
                        'RDER="0" CELLPADDING="0" CELLSPACING="0"><TR><TD CO' +
                        'LSPAN="2" ALIGN="center"><B>Yesterday (' +
                        dateString2(myData.time - 86400) + ') of ' + mName +
                        '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSPAN="2"><' +
                        'CANVAS ID="cnvs_' + eName + '_' + mName +
                        '_m3" WIDTH="' + sizeMagn[2] +
                        '" HEIGHT="36"></CANVAS><TR><TD ALIGN="left">00:00<T' +
                        'D ALIGN="right">24:00</TABLE></SPAN></A>\n';
                     // fifth, today's, column:
                     myTableStr += '   <TD><A CLASS="toolTip4" ' +
                        'HREF="javascript:void(0);" ID="' + mName + '/today/' +
                        myData.elements[cnt].host + '/' +
                        myData.elements[cnt].type + '" ONMOUSEDOWN="canvas_c' +
                        'licked(this, event)"><CANVAS ID="cnvs_' + eName +
                        '_' + mName + '_s4" WIDTH="' + sizeCnvs[3] +
                        '" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BO' +
                        'RDER="0" CELLPADDING="0" CELLSPACING="0"><TR><TD CO' +
                        'LSPAN="2" ALIGN="center"><B>Today (' +
                        dateString2( myData.time ) + ') of ' + mName +
                        '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSPAN="2"><' +
                        'CANVAS ID="cnvs_' + eName + '_' + mName +
                        '_m4" WIDTH="' + sizeMagn[3] + '" HEIGHT="36"></CANV' +
                        'AS><TR><TD ALIGN="left">00:00<TD ALIGN="right">24:0' +
                        '0</TABLE></SPAN></A>\n';
                     // sixth, following week's column:
                     myTableStr += '   <TD><A CLASS="toolTip5" ' +
                        'HREF="javascript:void(0);" ID="' + mName + '/fweek/' +
                        myData.elements[cnt].host + '/' +
                        myData.elements[cnt].type + '" ONMOUSEDOWN="canvas_c' +
                        'licked(this, event)"><CANVAS ID="cnvs_' + eName +
                        '_' + mName + '_s5" WIDTH="' + sizeCnvs[4] +
                        '" HEIGHT="18"></CANVAS><SPAN><TABLE WIDTH="100%" BO' +
                        'RDER="0" CELLPADDING="0" CELLSPACING="0"><TR><TD CO' +
                        'LSPAN="2" ALIGN="center"><B>Following Week of ' +
                        mName + '</B><TR><TD COLSPAN="2">&nbsp;<TR><TD COLSP' +
                        'AN="2"><CANVAS ID="cnvs_' + eName + '_' + mName +
                        '_m5" WIDTH="' + sizeMagn[4] + '" HEIGHT="36"></CANV' +
                        'AS><TR><TD ALIGN="left">' +
                        dateString2( myData.time + 1 * 86400 ) +
                        '<TD ALIGN="right">' +
                        dateString2( myData.time + 7 * 86400 ) +
                        '</TABLE></SPAN></A>\n';
                  }
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
   var cCtxS;
   var cCtxM;
   var mData;
   var xleft;

   // loop over site metrics and for each fill the five canvases:
   for ( var mName in myData.metrics ) {

      // first canvas, previous month, 120 six-hour/quarter-day entries:
      cData = myData.metrics[mName].pmonth.split("");
      cDom = document.getElementById('cnvs_' + mName + '_s1');
      cCtxS = cDom.getContext("2d");
      cDom = document.getElementById('cnvs_' + mName + '_m1');
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
            case "r":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,7,noBins[0],4);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,14,4,8);
               break;
            case "R":
               cCtxS.fillStyle = "#80FF80";
               cCtxS.fillRect(1+xleft,0,noBins[0],6);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,6,noBins[0],12);
               cCtxM.fillStyle = "#80FF80";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,12);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,12,4,24);
               break;
            case "S":
               cCtxS.fillStyle = "#FFFF00";
               cCtxS.fillRect(1+xleft,0,noBins[0],6);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,6,noBins[0],12);
               cCtxM.fillStyle = "#FFFF00";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,12);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,12,4,24);
               break;
            case "T":
               cCtxS.fillStyle = "#FF0000";
               cCtxS.fillRect(1+xleft,0,noBins[0],6);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,6,noBins[0],12);
               cCtxM.fillStyle = "#FF0000";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,12);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,12,4,24);
               break;
            case "U":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[0],6);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,6,noBins[0],12);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,12);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,12,4,24);
               break;
            case "V":
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+xleft,0,noBins[0],6);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,6,noBins[0],12);
               cCtxM.fillStyle = "#F4F4F4";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,12);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,12,4,24);
               break;
            case "W":
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,0,noBins[0],18);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,36);
               break;
            case "H":
               cCtxS.fillStyle = "#80FF80";
               cCtxS.fillRect(1+xleft,0,noBins[0],4);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,4,noBins[0],14);
               cCtxM.fillStyle = "#80FF80";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,8);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,8,4,28);
               break;
            case "I":
               cCtxS.fillStyle = "#FFFF00";
               cCtxS.fillRect(1+xleft,0,noBins[0],4);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,4,noBins[0],14);
               cCtxM.fillStyle = "#FFFF00";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,8);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,8,4,28);
            case "J":
               cCtxS.fillStyle = "#FF0000";
               cCtxS.fillRect(1+xleft,0,noBins[0],4);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,4,noBins[0],14);
               cCtxM.fillStyle = "#FF0000";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,8);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,8,4,28);
            case "K":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[0],4);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,4,noBins[0],14);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,8);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,8,4,28);
            case "L":
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+xleft,0,noBins[0],4);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,4,noBins[0],14);
               cCtxM.fillStyle = "#F4F4F4";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,8);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,8,4,28);
            case "M":
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
      cData = myData.metrics[mName].pweek.split("");
      cDom = document.getElementById('cnvs_' + mName + '_s2');
      cCtxS = cDom.getContext("2d");
      cDom = document.getElementById('cnvs_' + mName + '_m2');
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
            case "r":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,7,noBins[1],4);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,14,4,8);
               break;
            case "R":
               cCtxS.fillStyle = "#80FF80";
               cCtxS.fillRect(1+xleft,0,noBins[1],6);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,6,noBins[1],12);
               cCtxM.fillStyle = "#80FF80";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,12);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,12,4,24);
               break;
            case "S":
               cCtxS.fillStyle = "#FFFF00";
               cCtxS.fillRect(1+xleft,0,noBins[1],6);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,6,noBins[1],12);
               cCtxM.fillStyle = "#FFFF00";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,12);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,12,4,24);
               break;
            case "T":
               cCtxS.fillStyle = "#FF0000";
               cCtxS.fillRect(1+xleft,0,noBins[1],6);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,6,noBins[1],12);
               cCtxM.fillStyle = "#FF0000";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,12);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,12,4,24);
               break;
            case "U":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[1],6);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,6,noBins[1],12);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,12);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,12,4,24);
               break;
            case "V":
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+xleft,0,noBins[1],6);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,6,noBins[1],12);
               cCtxM.fillStyle = "#F4F4F4";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,12);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,12,4,24);
               break;
            case "W":
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,0,noBins[1],18);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            case "H":
               cCtxS.fillStyle = "#80FF80";
               cCtxS.fillRect(1+xleft,0,noBins[1],4);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,4,noBins[1],14);
               cCtxM.fillStyle = "#80FF80";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,8);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,8,4,28);
               break;
            case "I":
               cCtxS.fillStyle = "#FFFF00";
               cCtxS.fillRect(1+xleft,0,noBins[1],4);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,4,noBins[1],14);
               cCtxM.fillStyle = "#FFFF00";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,8);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,8,4,28);
               break;
            case "J":
               cCtxS.fillStyle = "#FF0000";
               cCtxS.fillRect(1+xleft,0,noBins[1],4);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,4,noBins[1],14);
               cCtxM.fillStyle = "#FF0000";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,8);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,8,4,28);
               break;
            case "K":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[1],4);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,4,noBins[1],14);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,8);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,8,4,28);
               break;
            case "L":
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+xleft,0,noBins[1],4);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,4,noBins[1],14);
               cCtxM.fillStyle = "#F4F4F4";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,8);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,8,4,28);
               break;
            case "M":
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,0,noBins[1],18);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            default:
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+xleft,0,noBins[1],18);
               cCtxM.fillStyle = "#F4F4F4";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
         }
      }

      // third canvas, previous day, 24*4 quarter-hour entries:
      cData = myData.metrics[mName].yesterday.split("");
      cDom = document.getElementById('cnvs_' + mName + '_s3');
      cCtxS = cDom.getContext("2d");
      cDom = document.getElementById('cnvs_' + mName + '_m3');
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
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,8);
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,12,4,4);
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,20,4,4);
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,28,4,8);
               break;
            case "r":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,7,noBins[2],4);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,14,4,8);
               break;
            case "R":
               cCtxS.fillStyle = "#80FF80";
               cCtxS.fillRect(1+xleft,0,noBins[2],6);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,6,noBins[2],12);
               cCtxM.fillStyle = "#80FF80";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,12);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,12,4,24);
               break;
            case "S":
               cCtxS.fillStyle = "#FFFF00";
               cCtxS.fillRect(1+xleft,0,noBins[2],6);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,6,noBins[2],12);
               cCtxM.fillStyle = "#FFFF00";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,12);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,12,4,24);
               break;
            case "T":
               cCtxS.fillStyle = "#FF0000";
               cCtxS.fillRect(1+xleft,0,noBins[2],6);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,6,noBins[2],12);
               cCtxM.fillStyle = "#FF0000";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,12);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,12,4,24);
               break;
            case "U":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[2],6);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,6,noBins[2],12);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,12);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,12,4,24);
               break;
            case "V":
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+xleft,0,noBins[2],6);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,6,noBins[2],12);
               cCtxM.fillStyle = "#F4F4F4";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,12);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,12,4,24);
               break;
            case "W":
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,0,noBins[2],18);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
               break;
            case "H":
               cCtxS.fillStyle = "#80FF80";
               cCtxS.fillRect(1+xleft,0,noBins[2],4);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,4,noBins[2],14);
               cCtxM.fillStyle = "#80FF80";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,8);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,8,4,28);
               break;
            case "I":
               cCtxS.fillStyle = "#FFFF00";
               cCtxS.fillRect(1+xleft,0,noBins[2],4);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,4,noBins[2],14);
               cCtxM.fillStyle = "#FFFF00";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,8);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,8,4,28);
               break;
            case "J":
               cCtxS.fillStyle = "#FF0000";
               cCtxS.fillRect(1+xleft,0,noBins[2],4);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,4,noBins[2],14);
               cCtxM.fillStyle = "#FF0000";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,8);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,8,4,28);
               break;
            case "K":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[2],4);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,4,noBins[2],14);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,8);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,8,4,28);
               break;
            case "L":
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+xleft,0,noBins[2],4);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,4,noBins[2],14);
               cCtxM.fillStyle = "#F4F4F4";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,8);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,8,4,28);
               break;
            case "M":
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,0,noBins[2],18);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
               break;
            default:
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+xleft,0,noBins[2],18);
               cCtxM.fillStyle = "#F4F4F4";
               cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
         }
      }

      // fourth canvas, today, 24*4 quarter-hour entries:
      cData = myData.metrics[mName].today.split("");
      cDom = document.getElementById('cnvs_' + mName + '_s4');
      cCtxS = cDom.getContext("2d");
      cDom = document.getElementById('cnvs_' + mName + '_m4');
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
            case "r":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,7,noBins[3],4);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,14,5,8);
               break;
            case "R":
               cCtxS.fillStyle = "#80FF80";
               cCtxS.fillRect(1+xleft,0,noBins[3],6);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,6,noBins[3],12);
               cCtxM.fillStyle = "#80FF80";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,12);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,12,5,24);
               break;
            case "S":
               cCtxS.fillStyle = "#FFFF00";
               cCtxS.fillRect(1+xleft,0,noBins[3],6);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,6,noBins[3],12);
               cCtxM.fillStyle = "#FFFF00";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,12);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,12,5,24);
               break;
            case "T":
               cCtxS.fillStyle = "#FF0000";
               cCtxS.fillRect(1+xleft,0,noBins[3],6);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,6,noBins[3],12);
               cCtxM.fillStyle = "#FF0000";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,12);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,12,5,24);
               break;
            case "U":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[3],6);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,6,noBins[3],12);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,12);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,12,5,24);
               break;
            case "V":
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+xleft,0,noBins[3],6);
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,6,noBins[3],12);
               cCtxM.fillStyle = "#F4F4F4";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,12);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,12,5,24);
               break;
            case "W":
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,0,noBins[3],18);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
               break;
            case "H":
               cCtxS.fillStyle = "#80FF80";
               cCtxS.fillRect(1+xleft,0,noBins[3],4);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,4,noBins[3],14);
               cCtxM.fillStyle = "#80FF80";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,8);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,8,5,28);
               break;
            case "I":
               cCtxS.fillStyle = "#FFFF00";
               cCtxS.fillRect(1+xleft,0,noBins[3],4);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,4,noBins[3],14);
               cCtxM.fillStyle = "#FFFF00";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,8);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,8,5,28);
               break;
            case "J":
               cCtxS.fillStyle = "#FF0000";
               cCtxS.fillRect(1+xleft,0,noBins[3],4);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,4,noBins[3],14);
               cCtxM.fillStyle = "#FF0000";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,8);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,8,5,28);
               break;
            case "K":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[3],4);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,4,noBins[3],14);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,8);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,8,5,28);
               break;
            case "L":
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+xleft,0,noBins[3],4);
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,4,noBins[3],14);
               cCtxM.fillStyle = "#F4F4F4";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,8);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,8,5,28);
               break;
            case "M":
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,0,noBins[3],18);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
               break;
            default:
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+xleft,0,noBins[3],18);
               cCtxM.fillStyle = "#F4F4F4";
               cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
         }
      }

      // fifth canvas, following week, 7*24 one-hour entries:
      cData = myData.metrics[mName].fweek.split("");
      cDom = document.getElementById('cnvs_' + mName + '_s5');
      cCtxS = cDom.getContext("2d");
      cDom = document.getElementById('cnvs_' + mName + '_m5');
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
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            case "w":
               cCtxS.fillStyle = "#FFFF00";
               cCtxS.fillRect(1+xleft,0,noBins[4],18);
               cCtxM.fillStyle = "#FFFF00";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            case "e":
               cCtxS.fillStyle = "#FF0000";
               cCtxS.fillRect(1+xleft,0,noBins[4],18);
               cCtxM.fillStyle = "#FF0000";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            case "p":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[4],6);
               cCtxS.fillRect(1+xleft,12,noBins[4],6);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,12);
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,24,4,12);
               break;
            case "d":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[4],18);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            case "a":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,0,noBins[4],4);
               cCtxS.fillRect(1+xleft,6,noBins[4],2);
               cCtxS.fillRect(1+xleft,10,noBins[4],2);
               cCtxS.fillRect(1+xleft,14,noBins[4],4);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,8);
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,12,4,4);
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,20,4,4);
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,28,4,8);
               break;
            case "r":
               cCtxS.fillStyle = "#6080FF";
               cCtxS.fillRect(1+xleft,7,noBins[4],4);
               cCtxM.fillStyle = "#6080FF";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,14,4,8);
               break;
            case "R":
            case "S":
            case "T":
            case "U":
            case "V":
            case "W":
               cCtxS.fillStyle = "#A000A0";
               cCtxS.fillRect(1+xleft,0,noBins[4],18);
               cCtxM.fillStyle = "#A000A0";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            case "H":
            case "I":
            case "J":
            case "K":
            case "L":
            case "M":
               cCtxS.fillStyle = "#663300";
               cCtxS.fillRect(1+xleft,0,noBins[4],18);
               cCtxM.fillStyle = "#663300";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
               break;
            default:
               cCtxS.fillStyle = "#F4F4F4";
               cCtxS.fillRect(1+xleft,0,noBins[4],18);
               cCtxM.fillStyle = "#F4F4F4";
               cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
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
         cCtxS = cDom.getContext("2d");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_m1');
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
               case "r":
                  cCtxS.fillStyle = "#6080FF";
                  cCtxS.fillRect(1+xleft,7,noBins[0],4);
                  cCtxM.fillStyle = "#6080FF";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,14,4,8);
                  break;
               case "R":
                  cCtxS.fillStyle = "#80FF80";
                  cCtxS.fillRect(1+xleft,0,noBins[0],6);
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,6,noBins[0],12);
                  cCtxM.fillStyle = "#80FF80";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,12,4,24);
               case "S":
                  cCtxS.fillStyle = "#FFFF00";
                  cCtxS.fillRect(1+xleft,0,noBins[0],6);
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,6,noBins[0],12);
                  cCtxM.fillStyle = "#FFFF00";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,12,4,24);
               case "T":
                  cCtxS.fillStyle = "#FF0000";
                  cCtxS.fillRect(1+xleft,0,noBins[0],6);
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,6,noBins[0],12);
                  cCtxM.fillStyle = "#FF0000";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,12,4,24);
               case "U":
                  cCtxS.fillStyle = "#6080FF";
                  cCtxS.fillRect(1+xleft,0,noBins[0],6);
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,6,noBins[0],12);
                  cCtxM.fillStyle = "#6080FF";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,12,4,24);
               case "V":
                  cCtxS.fillStyle = "#F4F4F4";
                  cCtxS.fillRect(1+xleft,0,noBins[0],6);
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,6,noBins[0],12);
                  cCtxM.fillStyle = "#F4F4F4";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,12,4,24);
               case "W":
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,0,noBins[0],18);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,36);
                  break;
               case "H":
                  cCtxS.fillStyle = "#80FF80";
                  cCtxS.fillRect(1+xleft,0,noBins[0],4);
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,4,noBins[0],14);
                  cCtxM.fillStyle = "#80FF80";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,8);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,8,4,28);
               case "I":
                  cCtxS.fillStyle = "#FFFF00";
                  cCtxS.fillRect(1+xleft,0,noBins[0],4);
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,4,noBins[0],14);
                  cCtxM.fillStyle = "#FFFF00";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,8);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,8,4,28);
               case "J":
                  cCtxS.fillStyle = "#FF0000";
                  cCtxS.fillRect(1+xleft,0,noBins[0],4);
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,4,noBins[0],14);
                  cCtxM.fillStyle = "#FF0000";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,8);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,8,4,28);
               case "K":
                  cCtxS.fillStyle = "#6080FF";
                  cCtxS.fillRect(1+xleft,0,noBins[0],4);
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,4,noBins[0],14);
                  cCtxM.fillStyle = "#6080FF";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,8);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,8,4,28);
               case "L":
                  cCtxS.fillStyle = "#F4F4F4";
                  cCtxS.fillRect(1+xleft,0,noBins[0],4);
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,4,noBins[0],14);
                  cCtxM.fillStyle = "#F4F4F4";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,8);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,8,4,28);
               case "M":
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,0,noBins[0],18);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,36);
                  break;
               default:
                  cCtxS.fillStyle = "#F4F4F4";
                  cCtxS.fillRect(1+xleft,noBins[0],2,18);
                  cCtxM.fillStyle = "#F4F4F4";
                  cCtxM.fillRect(2+qday*4+Math.trunc(qday/4)*2,0,4,36);
            }
         }

         // second canvas, previous week, 7*24 one-hour entries:
         cData = myData.elements[cnt].metrics[mName].pweek.split("");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_s2');
         cCtxS = cDom.getContext("2d");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_m2');
         cCtxM = cDom.getContext("2d");
         mData = Math.min(cData.length, cDom.width / 1.166 );
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
               case "r":
                  cCtxS.fillStyle = "#6080FF";
                  cCtxS.fillRect(1+xleft,7,noBins[1],4);
                  cCtxM.fillStyle = "#6080FF";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,14,4,8);
                  break;
               case "R":
                  cCtxS.fillStyle = "#80FF80";
                  cCtxS.fillRect(1+xleft,0,noBins[1],6);
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,6,noBins[1],12);
                  cCtxM.fillStyle = "#80FF80";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,12,4,24);
                  break;
               case "S":
                  cCtxS.fillStyle = "#FFFF00";
                  cCtxS.fillRect(1+xleft,0,noBins[1],6);
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,6,noBins[1],12);
                  cCtxM.fillStyle = "#FFFF00";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,12,4,24);
                  break;
               case "T":
                  cCtxS.fillStyle = "#FF0000";
                  cCtxS.fillRect(1+xleft,0,noBins[1],6);
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,6,noBins[1],12);
                  cCtxM.fillStyle = "#FF0000";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,12,4,24);
                  break;
               case "U":
                  cCtxS.fillStyle = "#6080FF";
                  cCtxS.fillRect(1+xleft,0,noBins[1],6);
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,6,noBins[1],12);
                  cCtxM.fillStyle = "#6080FF";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,12,4,24);
                  break;
               case "V":
                  cCtxS.fillStyle = "#F4F4F4";
                  cCtxS.fillRect(1+xleft,0,noBins[1],6);
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,6,noBins[1],12);
                  cCtxM.fillStyle = "#F4F4F4";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,12,4,24);
                  break;
               case "W":
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,0,noBins[1],18);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
                  break;
               case "H":
                  cCtxS.fillStyle = "#80FF80";
                  cCtxS.fillRect(1+xleft,0,noBins[1],4);
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,4,noBins[1],14);
                  cCtxM.fillStyle = "#80FF80";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,8);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,8,4,28);
                  break;
               case "I":
                  cCtxS.fillStyle = "#FFFF00";
                  cCtxS.fillRect(1+xleft,0,noBins[1],4);
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,4,noBins[1],14);
                  cCtxM.fillStyle = "#FFFF00";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,8);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,8,4,28);
                  break;
               case "J":
                  cCtxS.fillStyle = "#FF0000";
                  cCtxS.fillRect(1+xleft,0,noBins[1],4);
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,4,noBins[1],14);
                  cCtxM.fillStyle = "#FF0000";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,8);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,8,4,28);
                  break;
               case "K":
                  cCtxS.fillStyle = "#6080FF";
                  cCtxS.fillRect(1+xleft,0,noBins[1],4);
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,4,noBins[1],14);
                  cCtxM.fillStyle = "#6080FF";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,8);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,8,4,28);
                  break;
               case "L":
                  cCtxS.fillStyle = "#F4F4F4";
                  cCtxS.fillRect(1+xleft,0,noBins[1],4);
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,4,noBins[1],14);
                  cCtxM.fillStyle = "#F4F4F4";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,8);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,8,4,28);
                  break;
               case "M":
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,0,noBins[1],18);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
                  break;
               default:
                  cCtxS.fillStyle = "#F4F4F4";
                  cCtxS.fillRect(1+xleft,0,noBins[1],18);
                  cCtxM.fillStyle = "#F4F4F4";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
            }
         }

         // third canvas, previous day, 24*4 quarter-hour entries:
         cData = myData.elements[cnt].metrics[mName].yesterday.split("");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_s3');
         cCtxS = cDom.getContext("2d");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_m3');
         cCtxM = cDom.getContext("2d");
         mData = Math.min(cData.length, cDom.width / 2.25 );
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
                  cCtxM.fillStyle = "#6080FF";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,8);
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,12,4,4);
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,20,4,4);
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,28,4,8);
                  break;
               case "r":
                  cCtxS.fillStyle = "#6080FF";
                  cCtxS.fillRect(1+xleft,7,noBins[2],4);
                  cCtxM.fillStyle = "#6080FF";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,14,4,8);
                  break;
               case "R":
                  cCtxS.fillStyle = "#80FF80";
                  cCtxS.fillRect(1+xleft,0,noBins[2],6);
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,6,noBins[2],12);
                  cCtxM.fillStyle = "#80FF80";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,12,4,24);
                  break;
               case "S":
                  cCtxS.fillStyle = "#FFFF00";
                  cCtxS.fillRect(1+xleft,0,noBins[2],6);
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,6,noBins[2],12);
                  cCtxM.fillStyle = "#FFFF00";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,12,4,24);
                  break;
               case "T":
                  cCtxS.fillStyle = "#FF0000";
                  cCtxS.fillRect(1+xleft,0,noBins[2],6);
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,6,noBins[2],12);
                  cCtxM.fillStyle = "#FF0000";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,12,4,24);
                  break;
               case "U":
                  cCtxS.fillStyle = "#6080FF";
                  cCtxS.fillRect(1+xleft,0,noBins[2],6);
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,6,noBins[2],12);
                  cCtxM.fillStyle = "#6080FF";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,12,4,24);
                  break;
               case "V":
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,0,noBins[2],6);
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,6,noBins[2],12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,12,4,24);
                  break;
               case "W":
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,0,noBins[2],18);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
                  break;
               case "H":
                  cCtxS.fillStyle = "#80FF80";
                  cCtxS.fillRect(1+xleft,0,noBins[2],4);
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,4,noBins[2],14);
                  cCtxM.fillStyle = "#80FF80";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,8);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,8,4,28);
                  break;
               case "I":
                  cCtxS.fillStyle = "#FFFF00";
                  cCtxS.fillRect(1+xleft,0,noBins[2],4);
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,4,noBins[2],14);
                  cCtxM.fillStyle = "#FFFF00";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,8);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,8,4,28);
                  break;
               case "J":
                  cCtxS.fillStyle = "#FF0000";
                  cCtxS.fillRect(1+xleft,0,noBins[2],4);
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,4,noBins[2],14);
                  cCtxM.fillStyle = "#FF0000";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,8);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,8,4,28);
                  break;
               case "K":
                  cCtxS.fillStyle = "#6080FF";
                  cCtxS.fillRect(1+xleft,0,noBins[2],4);
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,4,noBins[2],14);
                  cCtxM.fillStyle = "#6080FF";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,8);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,8,4,28);
                  break;
               case "L":
                  cCtxS.fillStyle = "#F4F4F4";
                  cCtxS.fillRect(1+xleft,0,noBins[2],4);
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,4,noBins[2],14);
                  cCtxM.fillStyle = "#F4F4F4";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,8);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,8,4,28);
                  break;
               case "M":
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,0,noBins[2],18);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
                  break;
               default:
                  cCtxS.fillStyle = "#F4F4F4";
                  cCtxS.fillRect(1+xleft,0,noBins[2],18);
                  cCtxM.fillStyle = "#F4F4F4";
                  cCtxM.fillRect(2+qhour*4+Math.trunc(qhour/4)*2,0,4,36);
            }
         }

         // fourth canvas, today, 24*4 quarter-hour entries:
         cData = myData.elements[cnt].metrics[mName].today.split("");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_s4');
         cCtxS = cDom.getContext("2d");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_m4');
         cCtxM = cDom.getContext("2d");
         mData = Math.min(cData.length, cDom.width / 3.25 );
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
               case "r":
                  cCtxS.fillStyle = "#6080FF";
                  cCtxS.fillRect(1+xleft,7,noBins[3],4);
                  cCtxM.fillStyle = "#6080FF";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,14,5,8);
                  break;
               case "R":
                  cCtxS.fillStyle = "#80FF80";
                  cCtxS.fillRect(1+xleft,0,noBins[3],6);
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,6,noBins[3],12);
                  cCtxM.fillStyle = "#80FF80";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,12,5,24);
                  break;
               case "S":
                  cCtxS.fillStyle = "#FFFF00";
                  cCtxS.fillRect(1+xleft,0,noBins[3],6);
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,6,noBins[3],12);
                  cCtxM.fillStyle = "#FFFF00";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,12,5,24);
                  break;
               case "T":
                  cCtxS.fillStyle = "#FF0000";
                  cCtxS.fillRect(1+xleft,0,noBins[3],6);
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,6,noBins[3],12);
                  cCtxM.fillStyle = "#FF0000";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,12,5,24);
                  break;
               case "U":
                  cCtxS.fillStyle = "#6080FF";
                  cCtxS.fillRect(1+xleft,0,noBins[3],6);
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,6,noBins[3],12);
                  cCtxM.fillStyle = "#6080FF";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,12,5,24);
                  break;
               case "V":
                  cCtxS.fillStyle = "#F4F4F4";
                  cCtxS.fillRect(1+xleft,0,noBins[3],6);
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,6,noBins[3],12);
                  cCtxM.fillStyle = "#F4F4F4";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,12);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,12,5,24);
                  break;
               case "W":
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,0,noBins[3],18);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
                  break;
               case "H":
                  cCtxS.fillStyle = "#80FF80";
                  cCtxS.fillRect(1+xleft,0,noBins[3],4);
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,4,noBins[3],14);
                  cCtxM.fillStyle = "#80FF80";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,8);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,8,5,28);
                  break;
               case "I":
                  cCtxS.fillStyle = "#FFFF00";
                  cCtxS.fillRect(1+xleft,0,noBins[3],4);
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,4,noBins[3],14);
                  cCtxM.fillStyle = "#FFFF00";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,8);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,8,5,28);
                  break;
               case "J":
                  cCtxS.fillStyle = "#FF0000";
                  cCtxS.fillRect(1+xleft,0,noBins[3],4);
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,4,noBins[3],14);
                  cCtxM.fillStyle = "#FF0000";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,8);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,8,5,28);
                  break;
               case "K":
                  cCtxS.fillStyle = "#6080FF";
                  cCtxS.fillRect(1+xleft,0,noBins[3],4);
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,4,noBins[3],14);
                  cCtxM.fillStyle = "#6080FF";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,8);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,8,5,28);
                  break;
               case "L":
                  cCtxS.fillStyle = "#F4F4F4";
                  cCtxS.fillRect(1+xleft,0,noBins[3],4);
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,4,noBins[3],14);
                  cCtxM.fillStyle = "#F4F4F4";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,8);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,8,5,28);
                  break;
               case "M":
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,0,noBins[3],18);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
                  break;
               default:
                  cCtxS.fillStyle = "#F4F4F4";
                  cCtxS.fillRect(1+xleft,0,noBins[3],18);
                  cCtxM.fillStyle = "#F4F4F4";
                  cCtxM.fillRect(2+qhour*5+Math.trunc(qhour/4)*2,0,5,36);
            }
         }

         // fifth canvas, following week, 7*24 one-hour entries:
         cData = myData.elements[cnt].metrics[mName].fweek.split("");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_s5');
         cCtxS = cDom.getContext("2d");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_m5');
         cCtxM = cDom.getContext("2d");
         mData = Math.min(cData.length, cDom.width / 1.166 );
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
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
                  break;
               case "w":
                  cCtxS.fillStyle = "#FFFF00";
                  cCtxS.fillRect(1+xleft,0,noBins[4],18);
                  cCtxM.fillStyle = "#FFFF00";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
                  break;
               case "e":
                  cCtxS.fillStyle = "#FF0000";
                  cCtxS.fillRect(1+xleft,0,noBins[4],18);
                  cCtxM.fillStyle = "#FF0000";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
                  break;
               case "p":
                  cCtxS.fillStyle = "#6080FF";
                  cCtxS.fillRect(1+xleft,0,noBins[4],6);
                  cCtxS.fillRect(1+xleft,12,noBins[4],6);
                  cCtxM.fillStyle = "#6080FF";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,12);
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,24,4,12);
                  break;
               case "d":
                  cCtxS.fillStyle = "#6080FF";
                  cCtxS.fillRect(1+xleft,0,noBins[4],18);
                  cCtxM.fillStyle = "#6080FF";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
                  break;
               case "a":
                  cCtxS.fillStyle = "#6080FF";
                  cCtxS.fillRect(1+xleft,0,noBins[4],4);
                  cCtxS.fillRect(1+xleft,6,noBins[4],2);
                  cCtxS.fillRect(1+xleft,10,noBins[4],2);
                  cCtxS.fillRect(1+xleft,14,noBins[4],4);
                  cCtxM.fillStyle = "#6080FF";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,8);
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,12,4,4);
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,20,4,4);
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,28,4,8);
                  break;
               case "r":
                  cCtxS.fillStyle = "#6080FF";
                  cCtxS.fillRect(1+xleft,7,noBins[4],4);
                  cCtxM.fillStyle = "#6080FF";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,14,4,8);
                  break;
               case "R":
               case "S":
               case "T":
               case "U":
               case "V":
               case "W":
                  cCtxS.fillStyle = "#A000A0";
                  cCtxS.fillRect(1+xleft,0,noBins[4],18);
                  cCtxM.fillStyle = "#A000A0";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
                  break;
               case "H":
               case "I":
               case "J":
               case "K":
               case "L":
               case "M":
                  cCtxS.fillStyle = "#663300";
                  cCtxS.fillRect(1+xleft,0,noBins[4],18);
                  cCtxM.fillStyle = "#663300";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
                  break;
               default:
                  cCtxS.fillStyle = "#F4F4F4";
                  cCtxS.fillRect(1+xleft,0,noBins[4],18);
                  cCtxM.fillStyle = "#F4F4F4";
                  cCtxM.fillRect(2+hour*4+Math.trunc(hour/6)*2,0,4,36);
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
   cCtx = document.getElementById('cnvs_lgn_AtriskDowntime').getContext('2d');
   cCtx.fillStyle = "#6080FF";
   cCtx.fillRect(0,7,6,4);
   cCtx = document.getElementById('cnvs_lgn_Unknown').getContext('2d');
   cCtx.fillStyle = "#F4F4F4";
   cCtx.fillRect(0,0,6,18);
}
