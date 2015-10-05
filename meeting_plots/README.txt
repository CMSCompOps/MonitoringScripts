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
#                The script runs on vocms077 Friday and Saturday mornings
#                at 7:07 am for a preliminary version of the plots, i.e.
#                so people can see the site status for the past week when
#                they update their twiki sections on the weekend.
#                The real run of the script is Monday mornings at 7:07 am
#                (and at 9:17 am). In case of an execution error an email
#                is send and the area left incomplete. Hopefully the run
#                at 9 o'clock will fill in any previously inaccessible
#                plot/table. When the area is complete the sript makes
#                a copy into a year.week subdirectory of which the latest
#                four are kept. The script needs to be run after the
#                site readiness is updated for Sunday. (So we have the
#                Monday-to-Sunday week plots for the meeting.)
