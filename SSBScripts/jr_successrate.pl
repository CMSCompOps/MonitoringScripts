#!/usr/bin/perl -w

# Program to generate a text file with the job success rates SSB
#
#   Input: activity name
#   Writes the lists to files in the current directory
#

use LWP::Simple;
use XML::Parser;
use File::Temp("tempfile");

# Small class for Sites

package Site;

sub new {
    my $class = shift;
    my $id = shift;
    my $self = {ID => $id, CMS => '', SAM => ''};
    bless $self, $class;
}

sub tier {
    my $self = shift;
    return substr $self->{CMS}, 1, 1;
}

# Main program

package main;

$NAME = 'jr_successrate.pl';

# Array with all Sites and tiers
%seen = ();
%sites = ();
$lastsiteid = 0;
%dbinfo = ();

my $activity = $ARGV[0];
die "Usage: $NAME <activity>\n" if (! defined $activity);

#Get XML file from SiteDB

my $url = "https://cmsweb.cern.ch/sitedb/sitedb/reports/showXMLReport/?reportid=naming_convention.ini";
my $doc = get($url) or die "Cannot retrieve XML\n";
my $filepath = "/afs/cern.ch/cms/LCG/SiteComm/successrate_$activity.txt";
($fh, $tmpfile) = tempfile(UNLINK => 1) or die "Cannot create temporary file\n";

# Parse XML

$p = new XML::Parser(Handlers => {Start => \&h_start, Char  => \&h_char});
$p->parse($doc) or die "Cannot parse XML\n";

# Exit if no sites are found

if (! %sites) {
    die "No sites found!\n";
}

my $start = &dbtime(time);
my $end = &dbtime(time-86400);
my $start3 = &dbtime3(time-86400);
my $end3 = &dbtime3(time);

&get_successrates($activity, $start, $end);

foreach my $s ( sort {$a->{CMS} cmp $b->{CMS}} values %sites ) {
    my $cms = $s->{CMS};
    next if $seen{$cms}++;
    my $t = $s->tier;
    next if ( $t eq 'X' );

# Skip T1_CH_CERN
    next if ($s->{CMS} eq 'T1_CH_CERN');
    my $timestamp = &dbtime2(time); 
    my $sr = &get_sr($s->{CMS});

    next if ( $sr eq 'NA' );
    my $colour = 'green';
    if ( $t == 0 or $t == 1 ) {
	$colour = 'red' if ( $sr ne 'NA' and $sr < 90 );
    } elsif ( $t == 2 ) {
	$colour = 'red' if ( $sr ne 'NA' and $sr < 80 );
    }
    my $comm_url = &successrate_url($s->{CMS}, $start3, $end3, $activity);
    printf $fh "%s\t%s\t%.1f\t%s\t%s\n", $timestamp, $s->{CMS}, $sr,
    $colour, $comm_url;

# Use T0_CH_CERN for T1_CH_CERN
    if ( $s->{CMS} eq 'T0_CH_CERN' ) {
	printf $fh "%s\t%s\t%.1f\t%s\t%s\n", $timestamp, 'T1_CH_CERN',
        $sr, $colour, $comm_url;
    }
} 
close $fh;
system("/bin/cp -f $tmpfile $filepath"); 

# Handler routines

sub h_start {
    my $p = shift;
    my $el = shift;
    my %attr = ();
    while (@_) {
	my $a = shift;
	my $v = shift;
	$attr{$a} = $v;
    }
    if ($el eq 'item') {
	$lastid = $attr{id};
	my $s = new Site($attr{id});
	$sites{$lastid} = $s;
    }
}

sub h_sr_start {
    my $p = shift;
    my $el = shift;
    if ($el eq 'item' and $p->in_element('summaries')) {
	$lastsiteid++;
	$dbinfo{$lastsiteid} = {} unless (defined $dbinfo{$lastsiteid});
    }
}
sub h_char {
    my $p = shift;
    my $a = shift;
    $a =~ tr/ //;

    if ($p->in_element('cms')) {
	my $site = $sites{$lastid};
	$site->{CMS} = $a; 
    }
    if ($p->in_element('sam')) {
	my $site = $sites{$lastid};
	$site->{SAM} = $a; 
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

sub timestamp {
    my $timestamp = &dbtime2(time);
    return $timestamp;
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
        $sr = 100.;
	next unless ($term - $canc - $unkn != 0);
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
    my $url = "http://dashb-cms-job.cern.ch/dashboard/request.py/jobsummary-plot-or-table?user=&site=&ce=&submissiontool=&datset=&application=&rb=&activity=$activity&grid=&date2=$start&date1=$end&sortby=site&nbars=&scale=linear&jobtype=&tier=&check=terminated";
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
    my $url = "http://dashb-cms-job.cern.ch/templates/iview/#user=&refresh=0&table=Jobs&p=1&records=25&activemenu=0&usr=&site=$site&submissiontool=&application=&activity=$activity&status=&check=terminated&tier=&date1=$start&date2=$end&sortby=ce&scale=linear&bars=20&ce=&rb=&grid=&jobtype=&submissionui=&dataset=&submissiontype=&task=&subtoolver=&genactivity=&outputse=&appexitcode=&accesstype=";
    return $url;
}
