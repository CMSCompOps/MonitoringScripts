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
                        newSummary:       "<B>Summary:</B>" };
var siteMetricOrder = [ "Downtime", "SAM1day", "HC1day", "FTS1day",
                        "***LINE***",
                        "SR1day",
                        "***LINE***",
                        "LifeStatus", "manLifeStatus",
                        "ProdStatus", "manProdStatus",
                        "CrabStatus", "manCrabStatus",
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
                    ( xcoord - 2 ) * 120 / 780 ) ) );
      myPeriod = 6 * 60 * 60;
      myTrailr = "6hour";
   } else if ( mySecton == "pweek" ) {
      myOffset = myTIS - ( 8 * 86400 );
      myTarget = Math.min(167, Math.max(0, Math.trunc(
                    ( xcoord - 2 ) * 168 / 730 ) ) );
      myPeriod = 60 * 60;
      myTrailr = "1hour";
   } else if ( mySecton == "yrday" ) {
      myOffset = myTIS - 86400;
      myTarget = Math.min(95, Math.max(0, Math.trunc(
                    ( xcoord - 2 ) * 96 / 626 ) ) );
      myPeriod = 15 * 60;
      myTrailr = "15min";
   } else if ( mySecton == "today" ) {
      myOffset = myTIS;
      myTarget = Math.min(95, Math.max(0, Math.trunc(
                    ( xcoord - 2 ) * 96 / 626 ) ) );
      myPeriod = 15 * 60;
      myTrailr = "15min";
   } else if ( mySecton == "fweek" ) {
      myOffset = myTIS + 86400;
      myTarget = Math.min(167, Math.max(0, Math.trunc(
                    ( xcoord - 2 ) * 168 / 730 ) ) );
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
      myEnd = myOffset + ( ( myTarget + 1 ) * myPeriod );
      id.href = 'https://monit-grafana.cern.ch/d/m7XtZsEZk4/wlcg-sitemon-his' +
         'torical-tests?orgId=20&var-vo=cms&var-dst_tier=All&var-dst_experim' +
         'ent_site=' + myData.site + '&var-dst_hostname=' + mySitHst + '&var' +
         '-service_flavour=' + mySitTyp + '&from=' + myStart.toString() +
         '000&to=' + myEnd.toString() + '000';
   }

   return false;
}

function writePmonthTable() {

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
      'IG>&nbsp;</BIG>\n   <TH NOWRAP ALIGN="left"><BIG><B>' +
      dateString2(myData.time - 38 * 86400) + '</B></BIG>\n   <TH NOWRAP ALI' +
      'GN="center"><BIG><B>Previous Month</B></BIG>\n   <TH NOWRAP ALIGN="ri' +
      'ght"><BIG><B>' + dateString2(myData.time - 9 * 86400) + '</B></BIG>\n';


   // loop over metrics in siteMetricOrder and write a table row for each:
   for ( var mCnt=0; mCnt < siteMetricOrder.length; mCnt+=1 ) {
      if ( siteMetricOrder[mCnt] == "***LINE***" ) {
         myTableStr += '<TR>\n   <TD COLSPAN="5" bgcolor="#000000" STYLE="li' +
            'ne-height:2px;">&nbsp;\n<TR>\n   <TD COLSPAN="5" bgcolor="#FFFF' +
            'FF" STYLE="line-height:2px;">&nbsp;\n';
      } else if ( siteMetricOrder[mCnt] == "***GGUS***" ) {
         myTableStr += '<TR>\n   <TD ALIGN="left">GGUS tickets:\n' +
            '   <TD NOWRAP>&nbsp;';
         var myTime = new Date( myData.time * 1000 );
         myTime.setUTCHours(0, 0, 0, 0);
         var midnight = Math.trunc( myTime.valueOf() / 1000 );
         myData.ggus.sort(function(a,b){return a-b});
         // GGUS tickets opened the previous month:
         myTableStr += '\n   <TD COLSPAN="3"><DIV STYLE="text-align: center"' +
            '>&nbsp;';
         for ( var iTckt = 0; iTckt < myData.ggus.length; iTckt += 1 ) {
            if (( myData.ggus[iTckt][1] >= midnight - 3283200 ) &&
                ( myData.ggus[iTckt][1] <= midnight - 691200 )) {
               myTableStr += '[<A HREF="https://helpdesk.ggus.eu/#ticket/zoo' +
                  'm/' + myData.ggus[iTckt][0] + '">' +
                  myData.ggus[iTckt][0] + '</A>]&nbsp;';
            }
         }
         myTableStr += '</DIV>\n';
      } else if ( siteMetricOrder[mCnt] in myData.metrics ) {
         var nName = siteMetricOrder[mCnt];
         if ( siteMetricOrder[mCnt] in siteMetricLabel ) {
            nName = siteMetricLabel[siteMetricOrder[mCnt]];
         }
         myTableStr += '<TR>\n   <TD NOWRAP ALIGN="left">' + nName + '\n   <' +
            'TD NOWRAP>&nbsp;\n';
         myTableStr += '   <TD COLSPAN="3"><A HREF="javascript:void(0);" ID=' +
            '"' + siteMetricOrder[mCnt] + '/pmonth/' + myData.site +
            '" ONMOUSEDOWN="canvas_clicked(this, event)"><CANVAS ID="cnvs_' +
            siteMetricOrder[mCnt] + '_s1" WIDTH="782" HEIGHT="18"></CANVAS><' +
            '\A>\n';
      } else if ( siteMetricOrder[mCnt] == "***Othr***" ) {
         // loop over site metrics and write any not in siteMetricOrder:
         for ( var mName in myData.metrics ) {
            if ( siteMetricOrder.indexOf(mName) >= 0 ) {
               continue;
            }
            myTableStr += '<TR>\n   <TD ALIGN="left">' + mName +
               '\n   <TD NOWRAP>&nbsp;\n';
            // previous month's, column:
            myTableStr += '   <TD COLSPAN="3"><CANVAS ID="cnvs_' + mName +
               '_s1" WIDTH="782" HEIGHT="18"></CANVAS>\n';
         }
      } else if ( siteMetricOrder[mCnt] == "**Elmnts**" ) {
         // loop over site elements and write the metrics of each:
         for ( var cnt=0; cnt < myData.elements.length; cnt+=1 ) {
            // concatenate host and type excluding domain
            var eName = myData.elements[cnt].host + ' / ' +
               myData.elements[cnt].type;

            myTableStr += '<TR>\n   <TD COLSPAN="5" bgcolor="#000000" STYLE=' +
               '"line-height:2px;">&nbsp;\n<TR>\n   <TD COLSPAN="5" bgcolor=' +
               '"#FFFFFF" STYLE="line-height:8px;">&nbsp;\n<TR>\n   <TD COLS' +
               'PAN="5" bgcolor="#FFFFFF" ALIGN="left"><SPAN STYLE="font-siz' +
               'e:large;">' + eName + '</SPAN>\n';
            eName = myData.elements[cnt].host + '/' + myData.elements[cnt].type;
            eName = eName.replace(' ', '');
            // loop over metrics of element:
            for ( var iCnt=0; iCnt < srvcMetricOrder.length; iCnt+=1 ) {
               if ( srvcMetricOrder[iCnt] == "***LINE***" ) {
                  myTableStr += '<TR>\n   <TD COLSPAN="5" bgcolor="#000000" ' +
                     'STYLE="border-left:24px solid white; line-height:2px;"' +
                     '>&nbsp;</DIV>\n<TR>\n   <TD COLSPAN="5" bgcolor="#FFFF' +
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
                  myTableStr += '   <TD COLSPAN="3"><A HREF="javascript:void' +
                     '(0);" ID="' + srvcMetricOrder[iCnt] + '/pmonth/' +
                     myData.elements[cnt].host + '/' +
                     myData.elements[cnt].type +
                     '" ONMOUSEDOWN="canvas_clicked(this, event)"><CANVAS ID' +
                     '="c' + 'nvs_' + eName + '_' + srvcMetricOrder[iCnt] +
                     '_s1" WIDTH="782" HEIGHT="18"></CANVAS><\A>\n';
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
                     myTableStr += '   <TD COLSPAN="3"><A HREF="javascript:v' +
                        'oid(0);" ID="' + mName + '/pmonth/' +
                        myData.elements[cnt].host + '/' +
                        myData.elements[cnt].type +
                        '" ONMOUSEDOWN="canvas_clicked(this, event)"><CANVAS' +
                        ' ID="cnvs_' + eName + '_' + mName + '_s1" WIDTH="78' +
                        '2" HEIGHT="18"></CANVAS><\A>\n';
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

function writePweekTable() {

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
      'IG>&nbsp;</BIG>\n   <TH NOWRAP ALIGN="left"><BIG><B>' +
      dateString2(myData.time - 8 * 86400) + '</B></BIG>\n   <TH NOWRAP ALIG' +
      'N="center"><BIG><B>Previous Week</B></BIG>\n   <TH NOWRAP ALIGN="righ' +
      't"><BIG><B>' + dateString2(myData.time - 2 * 86400) + '</B></BIG>\n';


   // loop over metrics in siteMetricOrder and write a table row for each:
   for ( var mCnt=0; mCnt < siteMetricOrder.length; mCnt+=1 ) {
      if ( siteMetricOrder[mCnt] == "***LINE***" ) {
         myTableStr += '<TR>\n   <TD COLSPAN="5" bgcolor="#000000" STYLE="li' +
            'ne-height:2px;">&nbsp;\n<TR>\n   <TD COLSPAN="5" bgcolor="#FFFF' +
            'FF" STYLE="line-height:2px;">&nbsp;\n';
      } else if ( siteMetricOrder[mCnt] == "***GGUS***" ) {
         myTableStr += '<TR>\n   <TD ALIGN="left">GGUS tickets:\n' +
            '   <TD NOWRAP>&nbsp;';
         var myTime = new Date( myData.time * 1000 );
         myTime.setUTCHours(0, 0, 0, 0);
         var midnight = Math.trunc( myTime.valueOf() / 1000 );
         myData.ggus.sort();
         // GGUS tickets opened the previous week:
         myTableStr += '\n   <TD COLSPAN="3"><DIV STYLE="text-align: center"' +
            '>&nbsp;';
         for ( var iTckt = 0; iTckt < myData.ggus.length; iTckt += 1 ) {
            if (( myData.ggus[iTckt][1] >= midnight - 691200 ) &&
                ( myData.ggus[iTckt][1] <= midnight - 86400 )) {
               myTableStr += '[<A HREF="https://helpdesk.ggus.eu/#ticket/zoo' +
                  'm/' + myData.ggus[iTckt][0] + '">' +
                  myData.ggus[iTckt][0] + '</A>]&nbsp;';
            }
         }
         myTableStr += '</DIV>\n';
      } else if ( siteMetricOrder[mCnt] in myData.metrics ) {
         var nName = siteMetricOrder[mCnt];
         if ( siteMetricOrder[mCnt] in siteMetricLabel ) {
            nName = siteMetricLabel[siteMetricOrder[mCnt]];
         }
         myTableStr += '<TR>\n   <TD NOWRAP ALIGN="left">' + nName + '\n   <' +
            'TD NOWRAP>&nbsp;\n';
         myTableStr += '   <TD COLSPAN="3"><A HREF="javascript:void(0);" ID=' +
            '"' + siteMetricOrder[mCnt] + '/pweek/' + myData.site +
            '" ONMOUSEDOWN="canvas_clicked(this, event)"><CANVAS ID="cnvs_' +
            siteMetricOrder[mCnt] + '_s2" WIDTH="730" HEIGHT="18"></CANVAS><' +
            '/A>\n';
      } else if ( siteMetricOrder[mCnt] == "***Othr***" ) {
         // loop over site metrics and write any not in siteMetricOrder:
         for ( var mName in myData.metrics ) {
            if ( siteMetricOrder.indexOf(mName) >= 0 ) {
               continue;
            }
            myTableStr += '<TR>\n   <TD ALIGN="left">' + mName +
               '\n   <TD NOWRAP>&nbsp;\n';
            // previous week's, column:
            myTableStr += '   <TD COLSPAN="3"><CANVAS ID="cnvs_' + mName +
               '_s2" WIDTH="730" HEIGHT="18"></CANVAS>\n';
         }
      } else if ( siteMetricOrder[mCnt] == "**Elmnts**" ) {
         // loop over site elements and write the metrics of each:
         for ( var cnt=0; cnt < myData.elements.length; cnt+=1 ) {
            // concatenate host and type excluding domain
            var eName = myData.elements[cnt].host + ' / ' +
               myData.elements[cnt].type;

            myTableStr += '<TR>\n   <TD COLSPAN="5" bgcolor="#000000" STYLE=' +
               '"line-height:2px;">&nbsp;\n<TR>\n   <TD COLSPAN="5" bgcolor=' +
               '"#FFFFFF" STYLE="line-height:8px;">&nbsp;\n<TR>\n   <TD COLS' +
               'PAN="5" bgcolor="#FFFFFF" ALIGN="left"><SPAN STYLE="font-siz' +
               'e:large;">' + eName + '</SPAN>\n';
            eName = myData.elements[cnt].host + '/' + myData.elements[cnt].type;
            eName = eName.replace(' ', '');
            // loop over metrics of element:
            for ( var iCnt=0; iCnt < srvcMetricOrder.length; iCnt+=1 ) {
               if ( srvcMetricOrder[iCnt] == "***LINE***" ) {
                  myTableStr += '<TR>\n   <TD COLSPAN="5" bgcolor="#000000" ' +
                     'STYLE="border-left:24px solid white; line-height:2px;"' +
                     '>&nbsp;</DIV>\n<TR>\n   <TD COLSPAN="5" bgcolor="#FFFF' +
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
                  myTableStr += '   <TD COLSPAN="3"><A HREF="javascript:void' +
                     '(0);" ID="' + srvcMetricOrder[iCnt] + '/pweek/' +
                     myData.elements[cnt].host + '/' +
                     myData.elements[cnt].type +
                     '" ONMOUSEDOWN="canvas_clicked(this, event)"><CANVAS ID' +
                     '="cnvs_' + eName + '_' + srvcMetricOrder[iCnt] +
                     '_s2" WIDTH="730" HEIGHT="18"></CANVAS></A>\n';
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
                     myTableStr += '   <TD COLSPAN="3"><A HREF="javascript:v' +
                        'oid(0);" ID="' + mName + '/pweek/' +
                        myData.elements[cnt].host + '/' +
                        myData.elements[cnt].type +
                        '" ONMOUSEDOWN="canvas_clicked(this, event)"><CANVAS' +
                        ' ID="cnvs_' + eName + '_' + mName +
                        '_s2" WIDTH="730" HEIGHT="18"></CANVAS></A>\n';
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

function writeYesterdayTable() {

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
      'IG>&nbsp;</BIG>\n   <TH NOWRAP ALIGN="left"><BIG><B>00:00</B></BIG' +
      '>\n   <TH NOWRAP ALIGN="center"><BIG><B>Yesterday, ' +
      dateString2( myData.time - 86400 ) + '</B></BIG>\n   <TH NOWRAP ALIGN=' +
      '"right"><BIG><B>24:00</B></BIG>\n';


   // loop over metrics in siteMetricOrder and write a table row for each:
   for ( var mCnt=0; mCnt < siteMetricOrder.length; mCnt+=1 ) {
      if ( siteMetricOrder[mCnt] == "***LINE***" ) {
         myTableStr += '<TR>\n   <TD COLSPAN="5" bgcolor="#000000" STYLE="li' +
            'ne-height:2px;">&nbsp;\n<TR>\n   <TD COLSPAN="5" bgcolor="#FFFF' +
            'FF" STYLE="line-height:2px;">&nbsp;\n';
      } else if ( siteMetricOrder[mCnt] == "***GGUS***" ) {
         myTableStr += '<TR>\n   <TD ALIGN="left">GGUS tickets:\n' +
            '   <TD NOWRAP>&nbsp;';
         var myTime = new Date( myData.time * 1000 );
         myTime.setUTCHours(0, 0, 0, 0);
         var midnight = Math.trunc( myTime.valueOf() / 1000 );
         myData.ggus.sort();
         // GGUS tickets opened yesterday:
         myTableStr += '\n   <TD COLSPAN="3"><DIV STYLE="text-align: center"' +
            '>&nbsp;';
         for ( var iTckt = 0; iTckt < myData.ggus.length; iTckt += 1 ) {
            if (( myData.ggus[iTckt][1] >= midnight - 86400 ) &&
                ( myData.ggus[iTckt][1] <= midnight )) {
               myTableStr += '[<A HREF="https://helpdesk.ggus.eu/#ticket/zoo' +
                  'm/' + myData.ggus[iTckt][0] + '">' +
                  myData.ggus[iTckt][0] + '</A>]&nbsp;';
            }
         }
         myTableStr += '</DIV>\n';
      } else if ( siteMetricOrder[mCnt] in myData.metrics ) {
         var nName = siteMetricOrder[mCnt];
         if ( siteMetricOrder[mCnt] in siteMetricLabel ) {
            nName = siteMetricLabel[siteMetricOrder[mCnt]];
         }
         myTableStr += '<TR>\n   <TD NOWRAP ALIGN="left">' + nName + '\n   <' +
            'TD NOWRAP>&nbsp;\n';
         myTableStr += '   <TD COLSPAN="3"><A HREF="javascript:void(0);" ID=' +
            '"' + siteMetricOrder[mCnt] + '/yrday/' + myData.site +
            '" ONMOUSEDOWN="canvas_clicked(this, event)"><CANVAS ID="cnvs_' +
            siteMetricOrder[mCnt] + '_s3" WIDTH="626" HEIGHT="18"></CANVAS><' +
            '/A>\n';
      } else if ( siteMetricOrder[mCnt] == "***Othr***" ) {
         // loop over site metrics and write any not in siteMetricOrder:
         for ( var mName in myData.metrics ) {
            if ( siteMetricOrder.indexOf(mName) >= 0 ) {
               continue;
            }
            myTableStr += '<TR>\n   <TD ALIGN="left">' + mName +
               '\n   <TD NOWRAP>&nbsp;\n';
            // yesterday's, column:
            myTableStr += '   <TD COLSPAN="3"><CANVAS ID="cnvs_' + mName +
               '_s3" WIDTH="626" HEIGHT="18"></CANVAS>\n';
         }
      } else if ( siteMetricOrder[mCnt] == "**Elmnts**" ) {
         // loop over site elements and write the metrics of each:
         for ( var cnt=0; cnt < myData.elements.length; cnt+=1 ) {
            // concatenate host and type excluding domain
            var eName = myData.elements[cnt].host + ' / ' +
               myData.elements[cnt].type;

            myTableStr += '<TR>\n   <TD COLSPAN="5" bgcolor="#000000" STYLE=' +
               '"line-height:2px;">&nbsp;\n<TR>\n   <TD COLSPAN="5" bgcolor=' +
               '"#FFFFFF" STYLE="line-height:8px;">&nbsp;\n<TR>\n   <TD COLS' +
               'PAN="5" bgcolor="#FFFFFF" ALIGN="left"><SPAN STYLE="font-siz' +
               'e:large;">' + eName + '</SPAN>\n';
            eName = myData.elements[cnt].host + '/' + myData.elements[cnt].type;
            eName = eName.replace(' ', '');
            // loop over metrics of element:
            for ( var iCnt=0; iCnt < srvcMetricOrder.length; iCnt+=1 ) {
               if ( srvcMetricOrder[iCnt] == "***LINE***" ) {
                  myTableStr += '<TR>\n   <TD COLSPAN="5" bgcolor="#000000" ' +
                     'STYLE="border-left:24px solid white; line-height:2px;"' +
                     '>&nbsp;</DIV>\n<TR>\n   <TD COLSPAN="5" bgcolor="#FFFF' +
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
                  myTableStr += '   <TD COLSPAN="3"><A HREF="javascript:void' +
                     '(0);" ID="' + srvcMetricOrder[iCnt] + '/yrday/' +
                     myData.elements[cnt].host + '/' +
                     myData.elements[cnt].type +
                     '" ONMOUSEDOWN="canvas_clicked(this, event)"><CANVAS ID' +
                     '="cnvs_' + eName + '_' + srvcMetricOrder[iCnt] +
                     '_s3" WIDTH="626" HEIGHT="18"></CANVAS></A>\n';
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
                     myTableStr += '   <TD COLSPAN="3"><A HREF="javascript:v' +
                        'oid(0);" ID="' + mName + '/yrday/' +
                        myData.elements[cnt].host + '/' +
                        myData.elements[cnt].type +
                        '" ONMOUSEDOWN="canvas_clicked(this, event)"><CANVAS' +
                        ' ID="cnvs_' + eName + '_' + mName +
                        '_s3" WIDTH="626" HEIGHT="18"></CANVAS></A>\n';
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
      } else if ( siteMetricOrder[mCnt] == "***GGUS***" ) {
         myTableStr += '<TR>\n   <TD ALIGN="left">GGUS tickets:\n' +
            '   <TD NOWRAP>&nbsp;';
         var myTime = new Date( myData.time * 1000 );
         myTime.setUTCHours(0, 0, 0, 0);
         var midnight = Math.trunc( myTime.valueOf() / 1000 );
         myData.ggus.sort();
         // GGUS tickets opened today:
         myTableStr += '\n   <TD COLSPAN="3"><DIV STYLE="text-align: center"' +
            '>&nbsp;';
         for ( var iTckt = 0; iTckt < myData.ggus.length; iTckt += 1 ) {
            if ( myData.ggus[iTckt][1] >= midnight ) {
               myTableStr += '[<A HREF="https://helpdesk.ggus.eu/#ticket/zoo' +
                  'm/' + myData.ggus[iTckt][0] + '">' +
                  myData.ggus[iTckt][0] + '</A>]&nbsp;';
            }
         }
         myTableStr += '</DIV>\n';
      } else if ( siteMetricOrder[mCnt] in myData.metrics ) {
         var nName = siteMetricOrder[mCnt];
         if ( siteMetricOrder[mCnt] in siteMetricLabel ) {
            nName = siteMetricLabel[siteMetricOrder[mCnt]];
         }
         myTableStr += '<TR>\n   <TD NOWRAP ALIGN="left">' + nName + '\n   <' +
            'TD NOWRAP>&nbsp;\n';
         myTableStr += '   <TD COLSPAN="3"><A HREF="javascript:void(0);" ID=' +
            '"' + siteMetricOrder[mCnt] + '/today/' + myData.site +
            '" ONMOUSEDOWN="canvas_clicked(this, event)"><CANVAS ID="cnvs_' +
            siteMetricOrder[mCnt] + '_s4" WIDTH="626" HEIGHT="18"></CANVAS><' +
            '/A>\n';
      } else if ( siteMetricOrder[mCnt] == "***Othr***" ) {
         // loop over site metrics and write any not in siteMetricOrder:
         for ( var mName in myData.metrics ) {
            if ( siteMetricOrder.indexOf(mName) >= 0 ) {
               continue;
            }
            myTableStr += '<TR>\n   <TD ALIGN="left">' + mName +
               '\n   <TD NOWRAP>&nbsp;\n';
            // fifth, today's, column:
            myTableStr += '   <TD COLSPAN="3"><CANVAS ID="cnvs_' + mName +
               '_s4" WIDTH="626" HEIGHT="18"></CANVAS>\n';
         }
      } else if ( siteMetricOrder[mCnt] == "**Elmnts**" ) {
         // loop over site elements and write the metrics of each:
         for ( var cnt=0; cnt < myData.elements.length; cnt+=1 ) {
            // concatenate host and type excluding domain
            var eName = myData.elements[cnt].host + ' / ' +
               myData.elements[cnt].type;

            myTableStr += '<TR>\n   <TD COLSPAN="5" bgcolor="#000000" STYLE=' +
               '"line-height:2px;">&nbsp;\n<TR>\n   <TD COLSPAN="5" bgcolor=' +
               '"#FFFFFF" STYLE="line-height:8px;">&nbsp;\n<TR>\n   <TD COLS' +
               'PAN="5" bgcolor="#FFFFFF" ALIGN="left"><SPAN STYLE="font-siz' +
               'e:large;">' + eName + '</SPAN>\n';
            eName = myData.elements[cnt].host + '/' + myData.elements[cnt].type;
            eName = eName.replace(' ', '');
            // loop over metrics of element:
            for ( var iCnt=0; iCnt < srvcMetricOrder.length; iCnt+=1 ) {
               if ( srvcMetricOrder[iCnt] == "***LINE***" ) {
                  myTableStr += '<TR>\n   <TD COLSPAN="5" bgcolor="#000000" ' +
                     'STYLE="border-left:24px solid white; line-height:2px;"' +
                     '>&nbsp;</DIV>\n<TR>\n   <TD COLSPAN="5" bgcolor="#FFFF' +
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
                  myTableStr += '   <TD COLSPAN="3"><A HREF="javascript:void' +
                     '(0);" ID="' + srvcMetricOrder[iCnt] + '/today/' +
                     myData.elements[cnt].host + '/' +
                     myData.elements[cnt].type +
                     '" ONMOUSEDOWN="canvas_clicked(this, event)"><CANVAS ID' +
                     '="cnvs_' + eName + '_' + srvcMetricOrder[iCnt] +
                     '_s4" WIDTH="626" HEIGHT="18"></CANVAS></A>\n';
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
                     myTableStr += '   <TD COLSPAN="3"><A HREF="javascript:v' +
                        'oid(0);" ID="' + mName + '/today/' +
                        myData.elements[cnt].host + '/' +
                        myData.elements[cnt].type +
                        '" ONMOUSEDOWN="canvas_clicked(this, event)"><CANVAS' +
                        ' ID="cnvs_' + eName + '_' + mName +
                        '_s4" WIDTH="626" HEIGHT="18"></CANVAS></A>\n';
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

function writeFweekTable() {

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
      'IG>&nbsp;</BIG>\n   <TH NOWRAP ALIGN="left"><BIG><B>' +
      dateString2(myData.time + 86400) + '</B></BIG>\n   <TH NOWRAP ALIGN="c' +
      'enter"><BIG><B>Following Week</B></BIG>\n   <TH NOWRAP ALIGN="right">' +
      '<BIG><B>' + dateString2(myData.time + 7 * 86400) + '</B></BIG>\n';


   // loop over metrics in siteMetricOrder and write a table row for each:
   for ( var mCnt=0; mCnt < siteMetricOrder.length; mCnt+=1 ) {
      if ( siteMetricOrder[mCnt] == "***LINE***" ) {
         myTableStr += '<TR>\n   <TD COLSPAN="5" bgcolor="#000000" STYLE="li' +
            'ne-height:2px;">&nbsp;\n<TR>\n   <TD COLSPAN="5" bgcolor="#FFFF' +
            'FF" STYLE="line-height:2px;">&nbsp;\n';
      } else if ( siteMetricOrder[mCnt] == "***GGUS***" ) {
         myTableStr += '<TR>\n   <TD ALIGN="left">GGUS tickets:\n' +
            '   <TD NOWRAP>&nbsp;';
         var myTime = new Date( myData.time * 1000 );
         myTime.setUTCHours(0, 0, 0, 0);
         var midnight = Math.trunc( myTime.valueOf() / 1000 );
         myData.ggus.sort();
         // GGUS tickets opened the following week:
         myTableStr += '\n   <TD COLSPAN="3"><DIV STYLE="text-align: center"' +
            '>&nbsp;';
         for ( var iTckt = 0; iTckt < myData.ggus.length; iTckt += 1 ) {
            if ( myData.ggus[iTckt][1] >= midnight + 86400 ) {
               myTableStr += '[<A HREF="https://helpdesk.ggus.eu/#ticket/zoo' +
                  'm/' + myData.ggus[iTckt][0] + '">' +
                  myData.ggus[iTckt][0] + '</A>]&nbsp;';
            }
         }
         myTableStr += '</DIV>\n';
      } else if ( siteMetricOrder[mCnt] in myData.metrics ) {
         var nName = siteMetricOrder[mCnt];
         if ( siteMetricOrder[mCnt] in siteMetricLabel ) {
            nName = siteMetricLabel[siteMetricOrder[mCnt]];
         }
         myTableStr += '<TR>\n   <TD NOWRAP ALIGN="left">' + nName + '\n   <' +
            'TD NOWRAP>&nbsp;\n';
         myTableStr += '   <TD COLSPAN="3"><A HREF="javascript:void(0);" ID=' +
            '"' + siteMetricOrder[mCnt] + '/fweek/' + myData.site +
            '" ONMOUSEDOWN="canvas_clicked(this, event)"><CANVAS ID="cnvs_' +
            siteMetricOrder[mCnt] + '_s5" WIDTH="730" HEIGHT="18"></CANVAS><' +
            '/A>\n';
      } else if ( siteMetricOrder[mCnt] == "***Othr***" ) {
         // loop over site metrics and write any not in siteMetricOrder:
         for ( var mName in myData.metrics ) {
            if ( siteMetricOrder.indexOf(mName) >= 0 ) {
               continue;
            }
            myTableStr += '<TR>\n   <TD ALIGN="left">' + mName +
               '\n   <TD NOWRAP>&nbsp;\n';
            // following week's, column:
            myTableStr += '   <TD COLSPAN="3"><CANVAS ID="cnvs_' + mName +
               '_s5" WIDTH="730" HEIGHT="18"></CANVAS>\n';
         }
      } else if ( siteMetricOrder[mCnt] == "**Elmnts**" ) {
         // loop over site elements and write the metrics of each:
         for ( var cnt=0; cnt < myData.elements.length; cnt+=1 ) {
            // concatenate host and type excluding domain
            var eName = myData.elements[cnt].host + ' / ' +
               myData.elements[cnt].type;

            myTableStr += '<TR>\n   <TD COLSPAN="5" bgcolor="#000000" STYLE=' +
               '"line-height:2px;">&nbsp;\n<TR>\n   <TD COLSPAN="5" bgcolor=' +
               '"#FFFFFF" STYLE="line-height:8px;">&nbsp;\n<TR>\n   <TD COLS' +
               'PAN="5" bgcolor="#FFFFFF" ALIGN="left"><SPAN STYLE="font-siz' +
               'e:large;">' + eName + '</SPAN>\n';
            eName = myData.elements[cnt].host + '/' + myData.elements[cnt].type;
            eName = eName.replace(' ', '');
            // loop over metrics of element:
            for ( var iCnt=0; iCnt < srvcMetricOrder.length; iCnt+=1 ) {
               if ( srvcMetricOrder[iCnt] == "***LINE***" ) {
                  myTableStr += '<TR>\n   <TD COLSPAN="5" bgcolor="#000000" ' +
                     'STYLE="border-left:24px solid white; line-height:2px;"' +
                     '>&nbsp;</DIV>\n<TR>\n   <TD COLSPAN="5" bgcolor="#FFFF' +
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
                  myTableStr += '   <TD COLSPAN="3"><A HREF="javascript:void' +
                     '(0);" ID="' + srvcMetricOrder[iCnt] + '/fweek/' +
                     myData.elements[cnt].host + '/' +
                     myData.elements[cnt].type +
                     '" ONMOUSEDOWN="canvas_clicked(this, event)"><CANVAS ID' +
                     '="cnvs_' + eName + '_' + srvcMetricOrder[iCnt] +
                     '_s5" WIDTH="730" HEIGHT="18"></CANVAS></A>\n';
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
                     myTableStr += '   <TD COLSPAN="3"><A HREF="javascript:v' +
                        'oid(0);" ID="' + mName + '/fweek/' +
                        myData.elements[cnt].host + '/' +
                        myData.elements[cnt].type +
                        '" ONMOUSEDOWN="canvas_clicked(this, event)"><CANVAS' +
                        ' ID="cnvs_' + eName + '_' + mName +
                        '_s5" WIDTH="730" HEIGHT="18"></CANVAS></A>\n';
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

function fillPmonthCanvases() {

   // for the tic length we need to know the weekday:
   var dataDay  = ( new Date(myData.time * 1000) ).getDay();
   var cData;
   var cDom;
   var cCtx;
   var mData;

   // loop over site metrics and for each fill the s1 canvases:
   for ( var mName in myData.metrics ) {

      // s1 canvas, previous month, 120 six-hour/quarter-day entries:
      cData = myData.metrics[mName].pmonth.split("");
      cDom = document.getElementById('cnvs_' + mName + '_s1');
      cCtx = cDom.getContext("2d");
      mData = Math.min(cData.length, 120 );
      for ( var qday=0; qday < mData; qday+=1) {
         if ( qday % 4 == 0 ) {
            if ( (dataDay - 38 + Math.trunc(qday/4)) % 7 == 0 ) {
               // full scale tick at the start of the week, Sunday-to-Monday
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(6*qday+2*Math.trunc(qday/4),0,2,18);
            } else {
               // 75% tick at the start of a day
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(6*qday+2*Math.trunc(qday/4),4,2,14);
            }
         }
         switch ( cData[ qday ] ) {
            case "o":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,18);
               break;
            case "w":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,18);
               break;
            case "e":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,18);
               break;
            case "p":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,6);
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),12,6,6);
               break;
            case "d":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,18);
               break;
            case "a":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,4);
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),6,6,2);
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),10,6,2);
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),14,6,4);
               break;
            case "r":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),7,6,4);
               break;
            case "R":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,6);
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),6,6,12);
            case "S":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,6);
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),6,6,12);
            case "T":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,6);
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),6,6,12);
            case "U":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,6);
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),6,6,12);
            case "V":
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,6);
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),6,6,12);
            case "W":
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,18);
               break;
            case "H":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,4);
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),4,6,14);
            case "I":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,4);
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),4,6,14);
            case "J":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,4);
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),4,6,14);
            case "K":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,4);
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),4,6,14);
            case "L":
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,4);
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),4,6,14);
            case "M":
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,18);
               break;
            default:
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,18);
         }
      }
   }

   // loop over site elements and fill the s1 canvases of each metric:
   for ( var cnt=0; cnt < myData.elements.length; cnt+=1 ) {
      var eName = myData.elements[cnt].host + '/' + myData.elements[cnt].type;
      eName = eName.replace(' ', '');
      // loop over metrics of element:
      for ( var mName in myData.elements[cnt].metrics ) {
         // s2 canvas, previous week, 7*24 one-hour entries:
         cData = myData.elements[cnt].metrics[mName].pmonth.split("");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_s1');
         cCtx = cDom.getContext("2d");
         mData = Math.min(cData.length, 120 );
         for ( var qday=0; qday < mData; qday+=1) {
            if ( qday % 4 == 0 ) {
               if ( (dataDay - 38 + Math.trunc(qday/4)) % 7 == 0 ) {
                  // full scale tick at the start of the week, Sunday-to-Monday
                  cCtx.fillStyle = "#000000";
                  cCtx.fillRect(6*qday+2*Math.trunc(qday/4),0,2,18);
               } else {
                  // 75% tick at the start of a day
                  cCtx.fillStyle = "#000000";
                  cCtx.fillRect(6*qday+2*Math.trunc(qday/4),4,2,14);
               }
            }
            switch ( cData[ qday ] ) {
               case "o":
                  cCtx.fillStyle = "#80FF80";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,18);
                  break;
               case "w":
                  cCtx.fillStyle = "#FFFF00";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,18);
                  break;
               case "e":
                  cCtx.fillStyle = "#FF0000";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,18);
                  break;
               case "p":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,6);
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),12,6,6);
                  break;
               case "d":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,18);
                  break;
               case "a":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,4);
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),6,6,2);
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),10,6,2);
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),14,6,4);
                  break;
               case "r":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),7,6,4);
                  break;
               case "R":
                  cCtx.fillStyle = "#80FF80";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,6);
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),6,6,12);
               case "S":
                  cCtx.fillStyle = "#FFFF00";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,6);
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),6,6,12);
               case "T":
                  cCtx.fillStyle = "#FF0000";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,6);
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),6,6,12);
               case "U":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,6);
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),6,6,12);
               case "V":
                  cCtx.fillStyle = "#F4F4F4";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,6);
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),6,6,12);
               case "W":
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,18);
                  break;
               case "H":
                  cCtx.fillStyle = "#80FF80";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,4);
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),4,6,14);
               case "I":
                  cCtx.fillStyle = "#FFFF00";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,4);
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),4,6,14);
               case "J":
                  cCtx.fillStyle = "#FF0000";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,4);
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),4,6,14);
               case "K":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,4);
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),4,6,14);
               case "L":
                  cCtx.fillStyle = "#F4F4F4";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,4);
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),4,6,14);
               case "M":
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,18);
                  break;
               default:
                  cCtx.fillStyle = "#F4F4F4";
                  cCtx.fillRect(2+6*qday+2*Math.trunc(qday/4),0,6,18);
            }
         }
      }
   }
}

function fillPweekCanvases() {

   // for the tic length we need to know the weekday:
   var dataDay  = ( new Date(myData.time * 1000) ).getDay();
   var cData;
   var cDom;
   var cCtx;
   var mData;

   // loop over site metrics and for each fill the s2 canvases:
   for ( var mName in myData.metrics ) {

      // s2 canvas, previous week, 7*24 one-hour entries:
      cData = myData.metrics[mName].pweek.split("");
      cDom = document.getElementById('cnvs_' + mName + '_s2');
      cCtx = cDom.getContext("2d");
      mData = Math.min(cData.length, 168 );
      for ( var hour=0; hour < mData; hour+=1) {
         if ( hour % 24 == 0 ) {
            if ( (dataDay - 8 + Math.trunc(hour/24)) % 7 == 0 ) {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(4*hour+2*Math.trunc(hour/6),0,2,18);
            } else {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(4*hour+2*Math.trunc(hour/6),4,2,14);
            }
         } else if ( hour % 6 == 0 ) {
            // 50% tick at the start of a six-hour/quarter-day period
            cCtx.fillStyle = "#000000";
            cCtx.fillRect(4*hour+2*Math.trunc(hour/6),9,2,9);
         }
         switch ( cData[ hour ] ) {
            case "o":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
               break;
            case "w":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
               break;
            case "e":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
               break;
            case "p":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,6);
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),12,4,6);
               break;
            case "d":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
               break;
            case "a":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,4);
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),6,4,2);
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),10,4,2);
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),14,4,4);
               break;
            case "r":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),7,4,4);
               break;
            case "R":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,6);
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),6,4,12);
               break;
            case "S":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,6);
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),6,4,12);
               break;
            case "T":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,6);
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),6,4,12);
               break;
            case "U":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,6);
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),6,4,12);
               break;
            case "V":
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,6);
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),6,4,12);
               break;
            case "W":
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
               break;
            case "H":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,4);
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),4,4,14);
               break;
            case "I":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,4);
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),4,4,14);
               break;
            case "J":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,4);
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),4,4,14);
               break;
            case "K":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,4);
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),4,4,14);
               break;
            case "L":
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,4);
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),4,4,14);
               break;
            case "M":
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
               break;
            default:
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
         }
      }
   }

   // loop over site elements and fill the s2 canvases of each metric:
   for ( var cnt=0; cnt < myData.elements.length; cnt+=1 ) {
      var eName = myData.elements[cnt].host + '/' + myData.elements[cnt].type;
      eName = eName.replace(' ', '');
      // loop over metrics of element:
      for ( var mName in myData.elements[cnt].metrics ) {
         // s2 canvas, previous week, 7*24 one-hour entries:
         cData = myData.elements[cnt].metrics[mName].pweek.split("");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_s2');
         cCtx = cDom.getContext("2d");
         mData = Math.min(cData.length, 168 );
         for ( var hour=0; hour < mData; hour+=1) {
            if ( hour % 24 == 0 ) {
               if ( (dataDay - 8 + Math.trunc(hour/24)) % 7 == 0 ) {
                  cCtx.fillStyle = "#000000";
                  cCtx.fillRect(4*hour+2*Math.trunc(hour/6),0,2,18);
               } else {
                  cCtx.fillStyle = "#000000";
                  cCtx.fillRect(4*hour+2*Math.trunc(hour/6),4,2,14);
               }
            } else if ( hour % 6 == 0 ) {
               // 50% tick at the start of a six-hour/quarter-day period
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(4*hour+2*Math.trunc(hour/6),9,2,9);
            }
            switch ( cData[ hour ] ) {
               case "o":
                  cCtx.fillStyle = "#80FF80";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
                  break;
               case "w":
                  cCtx.fillStyle = "#FFFF00";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
                  break;
               case "e":
                  cCtx.fillStyle = "#FF0000";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
                  break;
               case "p":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,6);
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),12,4,6);
                  break;
               case "d":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
                  break;
               case "a":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,4);
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),6,4,2);
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),10,4,2);
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),14,4,4);
                  break;
               case "r":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),7,4,4);
                  break;
               case "R":
                  cCtx.fillStyle = "#80FF80";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,6);
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),6,4,12);
                  break;
               case "S":
                  cCtx.fillStyle = "#FFFF00";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,6);
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),6,4,12);
                  break;
               case "T":
                  cCtx.fillStyle = "#FF0000";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,6);
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),6,4,12);
                  break;
               case "U":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,6);
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),6,4,12);
                  break;
               case "V":
                  cCtx.fillStyle = "#F4F4F4";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,6);
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),6,4,12);
                  break;
               case "W":
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
                  break;
               case "H":
                  cCtx.fillStyle = "#80FF80";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,4);
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),4,4,14);
                  break;
               case "I":
                  cCtx.fillStyle = "#FFFF00";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,4);
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),4,4,14);
                  break;
               case "J":
                  cCtx.fillStyle = "#FF0000";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,4);
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),4,4,14);
                  break;
               case "K":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,4);
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),4,4,14);
                  break;
               case "L":
                  cCtx.fillStyle = "#F4F4F4";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,4);
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),4,4,14);
                  break;
               case "M":
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
                  break;
               default:
                  cCtx.fillStyle = "#F4F4F4";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
            }
         }
      }
   }
}

function fillYesterdayCanvases() {

   // for the tic length we need to know the weekday:
   var dataDay  = ( new Date(myData.time * 1000) ).getDay();
   var cData;
   var cDom;
   var cCtx;
   var mData;

   // loop over site metrics and for each fill the s3 canvases:
   for ( var mName in myData.metrics ) {

      // s3 canvas, yesterday, 24*4 quarter-hour entries:
      cData = myData.metrics[mName].yesterday.split("");
      cDom = document.getElementById('cnvs_' + mName + '_s3');
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
            case "o":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
               break;
            case "w":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
               break;
            case "e":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
               break;
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
            case "R":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,12);
               break;
            case "S":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,12);
               break;
            case "T":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,12);
               break;
            case "U":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,12);
               break;
            case "V":
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,12);
               break;
            case "W":
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
               break;
            case "H":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),4,6,14);
               break;
            case "I":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),4,6,14);
               break;
            case "J":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),4,6,14);
               break;
            case "K":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),4,6,14);
               break;
            case "L":
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),4,6,14);
               break;
            case "M":
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
               break;
            default:
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
         }
      }
   }

   // loop over site elements and fill the s3 canvases of each metric:
   for ( var cnt=0; cnt < myData.elements.length; cnt+=1 ) {
      var eName = myData.elements[cnt].host + '/' + myData.elements[cnt].type;
      eName = eName.replace(' ', '');
      // loop over metrics of element:
      for ( var mName in myData.elements[cnt].metrics ) {
         // s3 canvas, yesterday, 24*4 quarter-hour entries:
         cData = myData.elements[cnt].metrics[mName].yesterday.split("");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_s3');
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
               case "o":
                  cCtx.fillStyle = "#80FF80";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
                  break;
               case "w":
                  cCtx.fillStyle = "#FFFF00";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
                  break;
               case "e":
                  cCtx.fillStyle = "#FF0000";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
                  break;
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
               case "R":
                  cCtx.fillStyle = "#80FF80";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,12);
                  break;
               case "S":
                  cCtx.fillStyle = "#FFFF00";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,12);
                  break;
               case "T":
                  cCtx.fillStyle = "#FF0000";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,12);
                  break;
               case "U":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,12);
                  break;
               case "V":
                  cCtx.fillStyle = "#F4F4F4";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,12);
                  break;
               case "W":
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
                  break;
               case "H":
                  cCtx.fillStyle = "#80FF80";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),4,6,14);
                  break;
               case "I":
                  cCtx.fillStyle = "#FFFF00";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),4,6,14);
                  break;
               case "J":
                  cCtx.fillStyle = "#FF0000";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),4,6,14);
                  break;
               case "K":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),4,6,14);
                  break;
               case "L":
                  cCtx.fillStyle = "#F4F4F4";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),4,6,14);
                  break;
               case "M":
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
                  break;
               default:
                  cCtx.fillStyle = "#F4F4F4";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
            }
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
   for ( var mName in myData.metrics ) {

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
            case "o":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
               break;
            case "w":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
               break;
            case "e":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
               break;
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
            case "R":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,12);
               break;
            case "S":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,12);
               break;
            case "T":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,12);
               break;
            case "U":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,12);
               break;
            case "V":
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,12);
               break;
            case "W":
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
               break;
            case "H":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),4,6,14);
               break;
            case "I":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),4,6,14);
               break;
            case "J":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),4,6,14);
               break;
            case "K":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),4,6,14);
               break;
            case "L":
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),4,6,14);
               break;
            case "M":
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
               break;
            default:
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
         }
      }
   }

   // loop over site elements and fill the s4 canvases of each metric:
   for ( var cnt=0; cnt < myData.elements.length; cnt+=1 ) {
      var eName = myData.elements[cnt].host + '/' + myData.elements[cnt].type;
      eName = eName.replace(' ', '');
      // loop over metrics of element:
      for ( var mName in myData.elements[cnt].metrics ) {
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
               case "o":
                  cCtx.fillStyle = "#80FF80";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
                  break;
               case "w":
                  cCtx.fillStyle = "#FFFF00";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
                  break;
               case "e":
                  cCtx.fillStyle = "#FF0000";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
                  break;
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
               case "R":
                  cCtx.fillStyle = "#80FF80";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,12);
                  break;
               case "S":
                  cCtx.fillStyle = "#FFFF00";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,12);
                  break;
               case "T":
                  cCtx.fillStyle = "#FF0000";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,12);
                  break;
               case "U":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,12);
                  break;
               case "V":
                  cCtx.fillStyle = "#F4F4F4";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,6);
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),6,6,12);
                  break;
               case "W":
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
                  break;
               case "H":
                  cCtx.fillStyle = "#80FF80";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),4,6,14);
                  break;
               case "I":
                  cCtx.fillStyle = "#FFFF00";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),4,6,14);
                  break;
               case "J":
                  cCtx.fillStyle = "#FF0000";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),4,6,14);
                  break;
               case "K":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),4,6,14);
                  break;
               case "L":
                  cCtx.fillStyle = "#F4F4F4";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,4);
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),4,6,14);
                  break;
               case "M":
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
                  break;
               default:
                  cCtx.fillStyle = "#F4F4F4";
                  cCtx.fillRect(2+6*qhour+2*Math.trunc(qhour/4),0,6,18);
            }
         }
      }
   }
}

function fillFweekCanvases() {

   // for the tic length we need to know the weekday:
   var dataDay  = ( new Date(myData.time * 1000) ).getDay();
   var cData;
   var cDom;
   var cCtx;
   var mData;

   // loop over site metrics and for each fill the s5 canvases:
   for ( var mName in myData.metrics ) {

      // s5 canvas, following week, 7*24 one-hour entries:
      cData = myData.metrics[mName].fweek.split("");
      cDom = document.getElementById('cnvs_' + mName + '_s5');
      cCtx = cDom.getContext("2d");
      mData = Math.min(cData.length, 168 );
      for ( var hour=0; hour < mData; hour+=1) {
         if ( hour % 24 == 0 ) {
            if ( (dataDay - 8 + Math.trunc(hour/24)) % 7 == 0 ) {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(4*hour+2*Math.trunc(hour/6),0,2,18);
            } else {
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(4*hour+2*Math.trunc(hour/6),4,2,14);
            }
         } else if ( hour % 6 == 0 ) {
            // 50% tick at the start of a six-hour/quarter-day period
            cCtx.fillStyle = "#000000";
            cCtx.fillRect(4*hour+2*Math.trunc(hour/6),9,2,9);
         }
         switch ( cData[ hour ] ) {
            case "o":
               cCtx.fillStyle = "#80FF80";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
               break;
            case "w":
               cCtx.fillStyle = "#FFFF00";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
               break;
            case "e":
               cCtx.fillStyle = "#FF0000";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
               break;
            case "p":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,6);
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),12,4,6);
               break;
            case "d":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
               break;
            case "a":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,4);
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),6,4,2);
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),10,4,2);
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),14,4,4);
               break;
            case "r":
               cCtx.fillStyle = "#6080FF";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),7,4,4);
               break;
            case "R":
            case "S":
            case "T":
            case "U":
            case "V":
            case "W":
               cCtx.fillStyle = "#A000A0";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
               break;
            case "H":
            case "I":
            case "J":
            case "K":
            case "L":
            case "M":
               cCtx.fillStyle = "#663300";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
               break;
            default:
               cCtx.fillStyle = "#F4F4F4";
               cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
         }
      }
   }

   // loop over site elements and fill the s5 canvases of each metric:
   for ( var cnt=0; cnt < myData.elements.length; cnt+=1 ) {
      var eName = myData.elements[cnt].host + '/' + myData.elements[cnt].type;
      eName = eName.replace(' ', '');
      // loop over metrics of element:
      for ( var mName in myData.elements[cnt].metrics ) {
         // s5 canvas, following week, 7*24 one-hour entries:
         cData = myData.elements[cnt].metrics[mName].fweek.split("");
         cDom = document.getElementById('cnvs_' + eName + '_' + mName + '_s5');
         cCtx = cDom.getContext("2d");
         mData = Math.min(cData.length, 168 );
         for ( var hour=0; hour < mData; hour+=1) {
            if ( hour % 24 == 0 ) {
               if ( (dataDay - 8 + Math.trunc(hour/24)) % 7 == 0 ) {
                  cCtx.fillStyle = "#000000";
                  cCtx.fillRect(4*hour+2*Math.trunc(hour/6),0,2,18);
               } else {
                  cCtx.fillStyle = "#000000";
                  cCtx.fillRect(4*hour+2*Math.trunc(hour/6),4,2,14);
               }
            } else if ( hour % 6 == 0 ) {
               // 50% tick at the start of a six-hour/quarter-day period
               cCtx.fillStyle = "#000000";
               cCtx.fillRect(4*hour+2*Math.trunc(hour/6),9,2,9);
            }
            switch ( cData[ hour ] ) {
               case "o":
                  cCtx.fillStyle = "#80FF80";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
                  break;
               case "w":
                  cCtx.fillStyle = "#FFFF00";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
                  break;
               case "e":
                  cCtx.fillStyle = "#FF0000";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
                  break;
               case "p":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,6);
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),12,4,6);
                  break;
               case "d":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
                  break;
               case "a":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,4);
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),6,4,2);
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),10,4,2);
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),14,4,4);
                  break;
               case "r":
                  cCtx.fillStyle = "#6080FF";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),7,4,4);
                  break;
               case "R":
               case "S":
               case "T":
               case "U":
               case "V":
               case "W":
                  cCtx.fillStyle = "#A000A0";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
                  break;
               case "H":
               case "I":
               case "J":
               case "K":
               case "L":
               case "M":
                  cCtx.fillStyle = "#663300";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
                  break;
               default:
                  cCtx.fillStyle = "#F4F4F4";
                  cCtx.fillRect(2+4*hour+2*Math.trunc(hour/6),0,4,18);
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
