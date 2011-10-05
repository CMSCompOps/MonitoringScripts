#!/usr/bin/perl -w

#use strict;

use LWP::Simple;
use XML::Parser;

package Site;

sub new {
    my $class = shift;
    my $id = shift;
    my $self = {ID => $id,
	        NAME    => '',
	        QUARTER => '',
	        DISK => '',
	        TAPE => '',
	        SLOTS   => ''};
    bless $self, $class;
}

package main;

$ssbdir = "/afs/cern.ch/cms/LCG/SiteComm/";
$file_pledged_slots = "$ssbdir/pledged_slots.txt";
$file_pledged_disk = "$ssbdir/pledged_disk.txt";
$file_pledged_tape = "$ssbdir/pledged_tape.txt";

# Array with all Sites and tiers
%sites = ();

#Get XML file from SiteDB

my $url_p = "https://cmsweb.cern.ch/sitedb/reports/showXMLReport?reportid=quarterly_pledges.ini";
my $url_s = "https://cmsweb.cern.ch/sitedb/reports/showXMLReport?reportid=naming_convention.ini";
my $doc_p = get($url_p) or die "Cannot retrieve XML\n";
my $doc_s = get($url_s) or die "Cannot retrieve XML\n";

# Parse XML

$p = new XML::Parser(Handlers => {Start => \&h_start, Char  => \&h_char_pledges});
$p->parse($doc_p) or die "Cannot parse XML\n";
$p = new XML::Parser(Handlers => {Char  => \&h_char_names});
$p->parse($doc_s) or die "Cannot parse XML\n";

%data = ();
foreach (keys %sites) {
    my $name = $sites{$_}->{NAME};
    my $cms = $site2cms{$name};
    my $id = $site2id{$name};
    my $slots = $sites{$_} ->{SLOTS};
    my $quarter = $sites{$_} ->{QUARTER};
    my $disk = $sites{$_} ->{DISK};
    my $tape = $sites{$_} ->{TAPE};
    next if (&gt($quarter, &curr_quarter()));
    $data{$cms} = [$quarter, $slots, $disk, $tape, $id] if (!defined $data{$cms} or
					 &gt($quarter, ${$data{$cms}}[0]));
}

open(SLOTS, "> $file_pledged_slots") or
    die "Cannot create $file_pledged_slots\n";
open(DISK, "> $file_pledged_disk") or
    die "Cannot create $file_pledged_disk\n";
open(TAPE, "> $file_pledged_tape") or
    die "Cannot create $file_pledged_tape\n";

foreach my $cms (sort keys %data){
    my $timestamp = &timestamp();
    my $quarter = ${$data{$cms}}[0];
    my $slots = ${$data{$cms}}[1];
    my $disk = ${$data{$cms}}[2];
    my $tape = ${$data{$cms}}[3];
    my $id = ${$data{$cms}}[4];
    my $colour = 'green';
    $colour = "yellow" if (&gt(&curr_quarter(), $quarter));
    $colour = "red" if (&diff(&curr_quarter(), $quarter) > 4);
    my ($y, $q) = split /\./, $quarter;
    my $pledge_url = "https://cmsweb.cern.ch/sitedb/resources/?site=$id&quarter=$q&year=$y";
    printf SLOTS "%s\t%s\t%s\t%s\t%s\n", $timestamp, $cms, $slots,
    $colour, $pledge_url;
    printf DISK "%s\t%s\t%s\t%s\t%s\n", $timestamp, $cms, $disk,
    $colour, $pledge_url;
    printf TAPE "%s\t%s\t%s\t%s\t%s\n", $timestamp, $cms, $tape,
    $colour, $pledge_url;
}

close SLOTS;
close DISK;
close TAPE;

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

sub h_char_pledges {
    my $p = shift;
    my $a = shift;

    if ($p->in_element('NAME')) {
	my $site = $sites{$lastid};
	$site->{NAME} = $a;
    } elsif ($p->in_element('PLEDGEQUARTER')) {
	my $site = $sites{$lastid};
	$site->{QUARTER} = $a;
    } elsif ($p->in_element('JOB_SLOTS')) {
	my $site = $sites{$lastid};
	$site->{SLOTS} = $a;
    } elsif ($p->in_element('DISK_STORE')) {
	my $site = $sites{$lastid};
	$site->{DISK} = $a;
    } elsif ($p->in_element('TAPE_STORE')) {
	my $site = $sites{$lastid};
	$site->{TAPE} = $a;
    }
}

sub h_char_names {
    my $p = shift;
    my $a = shift;

    if ($p->in_element('id')) {
	$id2 = $a;
    } elsif ($p->in_element('site')) {
	$sitename = $a;
    } elsif ($p->in_element('cms') and $sitename) {
	$site2cms{$sitename} = $a;
	$site2id{$sitename} = $id2;
    }
}

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
    return "$year.$q";
}

sub gt {
    my ($q1, $q2) = @_;
    my @a = split /\./, $q1;
    my $a = $a[0]*10 + $a[1];
    @a = split /\./, $q2;
    my $b = $a[0]*10 + $a[1];
    if ($a > $b) {
	return 1;
    } else {
	return 0;
    }
}

sub diff {
    my ($a1, $a2) = @_;
    my ($y1, $q1) = split /\./, $a1;
    my ($y2, $q2) = split /\./, $a2;
    return ($y1 - $y2 ) * 4 + ($q1 - $q2);
}

