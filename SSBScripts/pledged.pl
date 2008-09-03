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
	        SLOTS   => ''};
    bless $self, $class;
}

package main;

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
    my $slots = $sites{$_} ->{SLOTS};
    my $quarter = $sites{$_} ->{QUARTER};
    next if (&gt($quarter, &curr_quarter()));
    $data{$cms} = [$quarter, $slots] if (!defined $data{$cms} or
					 &gt($quarter, ${$data{$cms}}[0]));
}
foreach my $cms (sort keys %data){
    my $timestamp = &timestamp();
    my $quarter = ${$data{$cms}}[0];
    my $slots = ${$data{$cms}}[1];
    my $colour = 'green';
    $colour = "yellow" if (&gt(&curr_quarter(), $quarter));
    my $pledge_url = 'https://cmsweb.cern.ch/sitedb/reports/showReport?reportid=quarterly_pledges.ini';
    printf "%s\t%s\t%s\t%s\t%s\n", $timestamp, $cms, $slots,
    $quarter, $pledge_url;
}

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
    }
}

sub h_char_names {
    my $p = shift;
    my $a = shift;

    if ($p->in_element('site')) {
	$sitename = $a;
    } elsif ($p->in_element('cms') and $sitename) {
	$site2cms{$sitename} = $a;
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

    my @time = localtime(time);
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
