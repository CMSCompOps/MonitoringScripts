#!/usr/bin/perl -w

# Program to generate a text file with the job success rates SSB
#
#   Input: activity name
#   Writes the lists to files in the current directory
#

eval "use JSON; 1" or eval "use JSON::XS; 1" or die;
use Net::SSL;
use LWP::UserAgent;
use XML::Parser;
use File::Temp("tempfile");

$NAME = 'jr_successrate.pl';

# Array with all Sites and tiers
$lastsiteid = 0;
%dbinfo = ();

my $activity = $ARGV[0];
my $outfile = $ARGV[1];
my $last = $ARGV[2];

die "Usage: $NAME <activity>\n" if (! defined $activity);

# Define HTTPS environment to use proxy
$ENV{HTTPS_CA_DIR} = (defined $ENV{X509_CERT_DIR})?$ENV{X509_CERT_DIR}:"/etc/grid-security/certificates";
my $GSIPROXY = (defined $ENV{X509_USER_PROXY})?$ENV{X509_USER_PROXY}:"/tmp/x509up_u$<";
$ENV{HTTPS_CA_FILE} = $GSIPROXY;
$ENV{HTTPS_CERT_FILE} = $GSIPROXY;
$ENV{HTTPS_KEY_FILE}  = $GSIPROXY;

# Get JSON file from SiteDB
my $url = "https://cmsweb.cern.ch/sitedb/data/prod/site-names";
#my $url = "http://cmssst.web.cern.ch/cmssst/siteDbInfo/site_names.json";

# Set header to select output format
$header = HTTP::Headers->new(
			     Accept => 'application/json');

$ua = LWP::UserAgent->new;
$ua->default_headers($header);

my $response = $ua->get($url) or die "Cannot retrieve JSON\n";

# Define output file
my $filepath;
if ($outfile) {
    $filepath = $outfile;
} else {
    $filepath = "/afs/cern.ch/cms/LCG/SiteComm/successrate_$activity.txt";
}
($fh, $tmpfile) = tempfile(UNLINK => 1) or die "Cannot create temporary file\n";

# Parse JSON
my $ref = decode_json($response->decoded_content);
my @sites;
foreach my $item (@{$ref->{'result'}}) {
    my $type = $item->[0];
    if ($type eq 'cms') {
	push @sites, $item->[2];
    }
}

# Exit if no sites are found

if (! @sites) {
    die "No sites found!\n";
}

$last = 24 if (!$last);    

# Time interval for Dashboard job monitoring
my $start = &dbtime(time-$last*3600);
my $end = &dbtime(time);

# Time interval for Dashboard links
my $start3 = &dbtime3(time-$last*3600);
my $end3 = &dbtime3(time);

&get_successrates($activity, $start, $end);

foreach my $cms ( sort @sites ) {
    my $t = tier($cms);
    next if ( $t eq 'X' );

# Skip T1_CH_CERN
    next if ($cms eq 'T1_CH_CERN');
    next if ($cms eq 'T0_CH_CERN'); # Change to T2 at end of LS1
    my $timestamp = &dbtime2(time); 
    my $sr = &get_sr($cms);
    my $colour;
#    $cms = 'T2_CH_CERN' if ($cms eq 'T0_CH_CERN'); # Uncomment at end of LS1
    my $comm_url = &successrate_url($cms, $start3, $end3, $activity);
    if ( $sr eq 'NA' ) {
	$colour = 'white';
	$sr = 'n/a';
	printf $fh "%s\t%s\t%s\t%s\t%s\n", $timestamp, $cms, $sr,
	$colour, $comm_url;
    } else {
	$colour = 'green';
	if ( $t == 0 or $t == 1 ) {
	    $colour = 'red' if ( $sr < 90 );
	} elsif ( $t == 2 or $t == 3 ) {
	    $colour = 'red' if ( $sr < 80 );
	}
	printf $fh "%s\t%s\t%.1f\t%s\t%s\n", $timestamp, $cms, $sr,
	$colour, $comm_url;
    }
} 
close $fh;
system("/bin/cp -f $tmpfile $filepath"); 

# Handler routines

sub h_sr_start {
    my $p = shift;
    my $el = shift;
    if ($el eq 'item' and $p->in_element('summaries')) {
	$lastsiteid++;
	$dbinfo{$lastsiteid} = {} unless (defined $dbinfo{$lastsiteid});
    }
}

sub h_sr_char {
    my $p = shift;
    my $a = shift;
    $a =~ tr/ //;

    if ($p->in_element('name')) {
	$dbinfo{$lastsiteid}->{'name'} = $a;
    }
    if ($p->in_element('app-succeeded')) {
	$dbinfo{$lastsiteid}->{'app-succeeded'} = $a;
    }
    if ($p->in_element('unsuccess')) {
	$dbinfo{$lastsiteid}->{'unsuccess'} = $a;
	my $b = $dbinfo{$lastsiteid}->{'unsuccess'};
    }
    if ($p->in_element('terminated')) {
	$dbinfo{$lastsiteid}->{'terminated'} = $a;
    }
    if ($p->in_element('allunk')) {
	$dbinfo{$lastsiteid}->{'allunk'} = $a;
    }
    if ($p->in_element('cancelled')) {
        $dbinfo{$lastsiteid}->{'cancelled'} = $a;
    }
}

sub dbtime {

    my $time = shift;
    my @time = gmtime($time);
    my $timestamp = sprintf("%s-%02d-%02d%s%02d%s%02d%s%02d",
			    1900 + $time[5],
			    1 + $time[4],
			    $time[3],'%20',
			    $time[2],'%3A',
			    $time[1],'%3A',
			    $time[0]
			    );
    return $timestamp;
}

sub dbtime2 {

    my $time = shift;
    my @time = gmtime($time);
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

sub dbtime3 {

    my $time = shift;
    my @time = gmtime($time);
    my $timestamp = sprintf("%s-%02d-%02d+%02d:%02d",
                            1900 + $time[5],
                            1 + $time[4],
                            $time[3],
                            $time[2],
                            $time[1]
                            );
    return $timestamp;
}


sub get_sr {
    my $site = shift;
    my $sr = 'NA';
    foreach my $id ( keys %dbinfo ) {
	next unless ( $site eq $dbinfo{$id}->{'name'} );
	my $succ = $dbinfo{$id}->{'app-succeeded'};
	my $unsucc = $dbinfo{$id}->{'unsuccess'};
	my $term = $dbinfo{$id}->{'terminated'};
	my $unkn = $dbinfo{$id}->{'allunk'};
        my $canc = $dbinfo{$id}->{'cancelled'};
	if ($term - $canc - $unkn < 10) {
#	    warn "WARNING: too few jobs. Skipping site = " . $site . " terminated = " . $term . " cancelled = " . $canc . " allunk = " . $unkn . "\n";
	    next;
        }
	$sr = ($succ - $unsucc) / ($term - $canc - $unkn) * 100.;
        if ($sr < 0. or $sr > 100. or ($term - $canc - $unkn < 0.)) {
            warn "ERROR: site = " . $site . " success rate = " . $sr .
		"\napp-succeded = " . $succ . " unsuccess = " . $unsucc .
		" terminated = " . $term . " cancelled = " . $canc . " allunkn = " .
		$unkn . "\n";
        }
    }
    return $sr;
}

sub get_successrates {

    my $activity = shift;
    my $start = shift;
    my $end = shift;
    my $sr = 'NA';
    my $url = "http://dashb-cms-job.cern.ch/dashboard/request.py/jobsummary-plot-or-table?user=&site=&ce=&submissiontool=&datset=&application=&rb=&activity=$activity&grid=&date2=$end&date1=$start&sortby=site&nbars=&scale=linear&jobtype=&tier=&check=terminated";
    my $cmd = "curl -H \'Accept: text/xml\' \'$url\' 2> /dev/null";
    my $output = `$cmd`;
    if ( defined $output ) {
	my $p = new XML::Parser(Handlers => {Start => \&h_sr_start, Char  => \&h_sr_char});
	$p->parse($output) or die "Cannot parse XML\n";
    } else{
        die "Cannot get XML\n";
    }
}

sub successrate_url {

    my $site = shift;
    my $start = shift;
    my $end = shift;
    my $activity = shift;
    my $url = "http://dashb-cms-job.cern.ch/dashboard/templates/web-job2/#user=&refresh=0&table=Jobs&p=1&records=25&activemenu=0&usr=&site=$site&submissiontool=&application=&activity=$activity&status=&check=terminated&tier=&date1=$start&date2=$end&sortby=ce&scale=linear&bars=20&ce=&rb=&grid=&jobtype=&submissionui=&dataset=&submissiontype=&task=&subtoolver=&genactivity=&outputse=&appexitcode=&accesstype=";
    return $url;
}

sub tier {
    my $site = shift;
    return substr $site, 1, 1;
}
