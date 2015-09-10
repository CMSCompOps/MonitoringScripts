#txt
#
# meeting_plots
# =============
# The CMS Computing Operations Site Support and Infrastructure team
# has weekly meetings with Tier-0, 1, and 2 administrators and
# coordinators and the Test, metric, site-readiness maintainers and
# support personnel.
# https://twiki.cern.ch/twiki/bin/view/CMS/CompOpsSiteSupportInfraMeeting
#
# Performance plots and graphs of the previous week are used in the
# meeting and discussed. To collect/prepare the material for the
# meeting the site support team setup an area at ~cmssst/www/meet_plots
# accessible as http://cmssst.web.cern.ch/cmssst/meet_plots/
#
# meet_plots.sh  Bourne shell script to generate/collect the plots and
#                tables for the Monday group chat meeting.
#                The script is setup to run Monday mornings on vocms077 
#                at 7:07 am (and at 9:17 am). The script moves images
#                of the previous week into a year.week subdirectory of
#                which the latest four are kept. In case a plot/table
#                is inaccessible, the area is left incomplete and the
#                9 o'clock execution hopefully fills in any missing
#                plots/tables. The script needs to be run after the
#                site readiness is updated for Sunday. (So we have the
#                Monday-to-Sunday week plots for the meeting.)
