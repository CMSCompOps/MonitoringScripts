#!/usr/bin/perl -w

use strict;

eval "use JSON; 1" or eval "use JSON::XS; 1" or die;
use LWP::Simple;
use XML::LibXML;
use Net::SSL;
use LWP::UserAgent;

our ($GSIPROXY, $ssbdir, $file_pledged_disk, $file_pledged_tape,
    $ref_pledges, $ref_sites, %data);

# Define HTTPS environment to use proxy
if (defined $ENV{X509_CERT_DIR}) {
    $ENV{HTTPS_CA_DIR} = $ENV{X509_CERT_DIR};
} else {
    $ENV{HTTPS_CA_DIR} = "/etc/grid-security/certificates";
}

if (defined $ENV{X509_USER_PROXY}) {
    $GSIPROXY = $ENV{X509_USER_PROXY};
} else {
    $GSIPROXY = "/tmp/x509up_u$<";
}

print $GSIPROXY;

$ENV{HTTPS_CA_FILE} = $GSIPROXY;
$ENV{HTTPS_CERT_FILE} = $GSIPROXY;
$ENV{HTTPS_KEY_FILE}  = $GSIPROXY;

$ssbdir = $ARGV[0];
$file_pledged_disk = "$ssbdir/pledged_disk.txt";
$file_pledged_tape = "$ssbdir/pledged_tape.txt";

# Get JSON file from SiteDB
#my $url_p = "https://cmsweb.cern.ch/sitedb/data/prod/resource-pledges";
my @time = gmtime(time);
my $year = 1900 + $time[5];
my $url_p = "https://wlcg-rebus.cern.ch/apps/pledges/resources/" . $year . "/all/json";
#my $url_s = "https://cmsweb.cern.ch/sitedb/data/prod/site-names";
my $url_s = "http://cmssst.web.cern.ch/cmssst/vofeed/vofeed.xml";

# Parse JSON
my $ua = LWP::UserAgent->new;
$ua->default_header(Accept => 'application/json');
my $response = $ua->get($url_p) or die "Cannot retrieve JSON\n";
print $response->decoded_content;
$ref_pledges = decode_json($response->decoded_content);
#$response = $ua->get($url_s) or die "Cannot retrieve JSON\n";
#$ref_sites = decode_json($response->decoded_content);
#
## Build site name maps
#my %site2cms = my %cms2site = ();
#foreach my $item (@{$ref_sites->{'result'}}) {
#    my $type = $item->[0];
#    if ($type eq 'cms') {
#	$site2cms{$item->[1]} = $item->[2];
#	$cms2site{$item->[2]} = $item->[1];
#    }
#}
my %site2cms = my %cms2site = ();
my $dom = XML::LibXML->load_xml(location => $url_s);
foreach my $grid ($dom->findnodes('/root/atp_site/group')) {
   my $grptyp = $grid->findvalue('./@type');
   if ( $grptyp eq 'CMS_Site' ) {
      my $grpnam = $grid->findvalue('./@name');
      my $atpnam = $grid->findvalue('../@name');
      if ( $atpnam ne "" ) {
         $site2cms{$atpnam} = $grpnam;
         $cms2site{$grpnam} = $atpnam;
      }
   }
}

# Extract pledge data
%data = ();
foreach my $cms (sort keys %cms2site) {
    my $tier = substr($cms, 1 ,1);
    my $name = substr($cms, 6);
    my $site = $cms2site{$cms};
    my $disk = my $tape = 0;
    foreach my $item (@{$ref_pledges}) {
	my $s = $item->{'Federation'};
        my $t = substr($item->{'Tier'}, 5, 1);
        next if ( $t ne $tier);
	if ((index($s, $site) != -1) or (index($s, $name) != -1)) {
	   if (($item->{'PledgeType'} eq "Disk") and ( $item->{'CMS'} ne "")){
              $disk = $item->{'CMS'};
           }
           if (($item->{'PledgeType'} eq "Tape") and ( $item->{'CMS'} ne "")) {
              $tape = $item->{'CMS'};
           }
        }
    }
    next if (($disk == 0) and ($tape == 0));
    $data{$cms} = [$year, $disk, $tape];
}

open(DISK, "> $file_pledged_disk") or
    die "Cannot create $file_pledged_disk\n";
open(TAPE, "> $file_pledged_tape") or
    die "Cannot create $file_pledged_tape\n";

foreach my $cms (sort keys %data){
    my $timestamp = &timestamp();
    my $quarter = ${$data{$cms}}[0];
    my $disk = ${$data{$cms}}[1];
    my $tape = ${$data{$cms}}[2];
    my $colour = 'green';
    $colour = "yellow" if (&curr_quarter() > $quarter);
    $colour = "red" if (&curr_quarter() - $quarter > 1);
    my $pledge_url = "https://wlcg-rebus.cern.ch/apps/pledges/resources/";
    printf DISK "%s\t%s\t%s\t%s\t%s\n", $timestamp, $cms, $disk,
    $colour, $pledge_url;
    printf TAPE "%s\t%s\t%s\t%s\t%s\n", $timestamp, $cms, $tape,
    $colour, $pledge_url;
}

close DISK;
close TAPE;

sub timestamp {

    my @time = localtime(time);
    my $timestamp = sprintf("%s-%02d-%02d %02d:%02d:%02d",
                            1900 + $time[5],
                            1 + $time[4],
                            $time[3],
                            $time[2],
                            $time[1],
                            $time[0]
                            );
    return $timestamp;
}

sub curr_quarter {

    my @time = gmtime(time);
    my $year = 1900 + $time[5];
    my $q = int(($time[4] / 3) + 1);
    return "$year";
}
