#!/usr/bin/perl -w

use strict;

eval "use JSON; 1" or eval "use JSON::XS; 1" or die;
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

$ssbdir = "/afs/cern.ch/user/c/cmssst/www/ssb/storage/";
$file_pledged_disk = "$ssbdir/pledged_disk.txt";
$file_pledged_tape = "$ssbdir/pledged_tape.txt";

# Get JSON file from SiteDB
my $url_p = "https://cmsweb.cern.ch/sitedb/data/prod/resource-pledges";
my $url_s = "https://cmsweb.cern.ch/sitedb/data/prod/site-names";

# Parse JSON
my $ua = LWP::UserAgent->new;
$ua->default_header(Accept => 'application/json');
my $response = $ua->get($url_p) or die "Cannot retrieve JSON\n";
print $response->decoded_content;
$ref_pledges = decode_json($response->decoded_content);
$response = $ua->get($url_s) or die "Cannot retrieve JSON\n";
$ref_sites = decode_json($response->decoded_content);

# Build site name maps
my %site2cms = my %cms2site = ();
foreach my $item (@{$ref_sites->{'result'}}) {
    my $type = $item->[0];
    if ($type eq 'cms') {
	$site2cms{$item->[1]} = $item->[2];
	$cms2site{$item->[2]} = $item->[1];
    }
}

# Extract pledge data
%data = ();
foreach my $cms (keys %cms2site) {
    my $site = $cms2site{$cms};
    my $disk = my $tape = -1;
    my $time = 0.;
    my $quarter = 0;
    foreach my $item (@{$ref_pledges->{'result'}}) {
	my $s = $item->[0];
	next if ($s ne $site or $item->[2] > &curr_quarter());
	if ($item->[1] > $time) {
	    $disk = $item->[4];
	    $tape = $item->[5];
	    $time = $item->[1];
	    $quarter = $item->[2];
	}
    }
    next if ($quarter == 0);
    $data{$cms} = [$quarter, $disk, $tape];
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
    my $pledge_url = "https://cmsweb.cern.ch/sitedb/prod/pledges?q=$quarter";
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
