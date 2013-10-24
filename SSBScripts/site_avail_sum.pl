#!/usr/bin/perl -w

# Program to generate a text file with the site availabilities for the SSB
#
#   Input: none
#   Writes the lists to files in the current directory
#

use JSON;
use LWP::UserAgent;
use File::Temp("tempfile");

my $outfile = $ARGV[0];

# Define HTTPS environment to use proxy
$ENV{HTTPS_CA_DIR} = (defined $ENV{X509_CERT_DIR})?$ENV{X509_CERT_DIR}:"/etc/grid-security/certificates";
my $GSIPROXY = (defined $ENV{X509_USER_PROXY})?$ENV{X509_USER_PROXY}:"/tmp/x509up_u$<";
$ENV{HTTPS_CA_FILE} = $GSIPROXY;
$ENV{HTTPS_CERT_FILE} = $GSIPROXY;
$ENV{HTTPS_KEY_FILE}  = $GSIPROXY;

#Get JSON file from SiteDB
my $url = "https://cmsweb.cern.ch/sitedb/data/prod/site-names";
# Set header to select output format
$header = HTTP::Headers->new(
			     Accept => 'application/json');

$ua = LWP::UserAgent->new;
$ua->default_headers($header);

my $response = $ua->get($url) or die "Cannot retrieve JSON\n";

# Parse JSON
my $ref = from_json($response->decoded_content);
my @sites;
foreach my $item (@{$ref->{'result'}}) {
    my $type = $item->[0];
    if ($type eq 'cms') {
	push @sites, $item->[2];
    }
}

# Define output file
my $filepath;
if ($outfile) {
    $filepath = $outfile;
} else {
    $filepath = "/afs/cern.ch/cms/LCG/SiteComm/site_avail_sum.txt";
}
($fh, $tmpfile) = tempfile(UNLINK => 1) or die "Cannot create temporary file\n";

# Exit if no sites are found

if (! @sites) {
    die "No sites found!\n";
}
%seen = ();

foreach my $cms ( sort @sites ) {
    next if $seen{$cms}++;
    my $t = tier($cms);
    next if ( $t eq 'X' );
# Skip T[01]_CH_CERN
    next if ($cms eq 'T0_CH_CERN');
    next if ($cms eq 'T1_CH_CERN');
    my $timestamp = &timestamp;
    my $avail = &get_avail($cms);
    die "Cannot get XML\n" if ($avail eq 'error');
    next if ( $avail eq 'NA' );
    my $colour = 'green';
    if ( $t == 0 or $t == 1 ) {
	$colour = 'red' if ( $avail ne 'NA' and $avail < 90 );
    } elsif ( $t == 2 ) {
	$colour = 'red' if ( $avail ne 'NA' and $avail < 80 );
    }
    $colour = 'red' if ( $avail eq 'NA' );
    my $comm_url = &avail_url($cms);
    printf $fh "%s\t%s\t%s\t%s\t%s\n", $timestamp, $cms, "${avail}",
    $colour, $comm_url;
} 
close $fh;
system("/bin/cp -f $tmpfile $filepath"); 

sub timestamp {

    my @time = gmtime(time);
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

sub ptime {

    my @time = @_;
    my $t = sprintf("%s-%02d-%02d",
			1900 + $time[5], 1 + $time[4], $time[3]);
    return $t;
}

sub get_avail {

    my $site = shift;
    my $avail = 'NA';
    my $url = "http://dashb-cms-sum.cern.ch/dashboard/request.py/getAvailabilityResults?profile_name=CMS_CRITICAL_FULL&view=siteavl&time_range=last24&plot_type=ranking&group_name=${site}";
    my $cmd = "curl -H \'Accept: text/xml\' \'$url\' 2> /dev/null";
    open(SUM,"$cmd | xmllint --format - |") or warn 'Cannot query SUM\n';
    my $a = '';
    while (<SUM>) {
	chomp;
	if (/<item>(\d*\.+\d*)<\/item>/) {
	    $avail = sprintf "%.3f", $1;
            $avail = $avail * 100.;
	}
    }
    return $avail;
}

sub avail_url {

    my $site = shift;
    my $start = &ptime(gmtime(time));
    my $end = &ptime(gmtime(time+86400));
    my $url = "http://dashb-cms-sum.cern.ch/dashboard/request.py/historicalsmryview-sum#view=siteavl&time%5B%5D=individual&starttime=$start&endtime=$end&profile=CMS_CRITICAL_FULL&group=AllGroups&site%5B%5D=$site&type=quality";
    return $url;
}

sub tier {
    my $site = shift;
    return substr $site, 1, 1;
}
