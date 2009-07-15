#!/usr/bin/perl -w
#
# Prints all the CMS sites by CMS name
#
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

#Get XML file from SiteDB

my $url = "https://cmsweb.cern.ch/sitedb/reports/showXMLReport?reportid=naming_convention.ini";
my $doc = get($url) or die "Cannot retrieve XML\n";

# Parse XML

$p = new XML::Parser(Handlers => {Char  => \&h_char_names});
$p->parse($doc) or die "Cannot parse XML\n";

print map("$_\n", sort @sites);

# Handler routines

sub h_char_names {
    my $p = shift;
    my $a = shift;

    if ($p->in_element('cms')) {
	push @sites, $a unless grep (/$a/, @sites);
    }
}
