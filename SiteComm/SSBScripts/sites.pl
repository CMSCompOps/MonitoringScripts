#!/usr/bin/perl -w
#
# Prints all the CMS sites by CMS name
#
#use strict;

use LWP::UserAgent;
use JSON;

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

# Modify as needed
my $email = 'Andrea.Sciaba@cern.ch';

# Define HTTPS environment to use proxy
$ENV{HTTPS_CA_DIR} = (defined $ENV{X509_CERT_DIR})?$ENV{X509_CERT_DIR}:"/etc/grid-security/certificates";
my $GSIPROXY = (defined $ENV{X509_USER_PROXY})?$ENV{X509_USER_PROXY}:"/tmp/x509up_u$<";
$ENV{HTTPS_CA_FILE} = $GSIPROXY;
$ENV{HTTPS_CERT_FILE} = $GSIPROXY;
$ENV{HTTPS_KEY_FILE}  = $GSIPROXY;

# Array with all Sites and tiers

#Get JSON file from SiteDB
my $url = "https://cmsweb.cern.ch/sitedb/data/prod/site-names";

# Set header to select output format
$header = HTTP::Headers->new(
			     Accept => 'application/json');

$ua = LWP::UserAgent->new(
			  from => $email);
$ua->default_headers($header);

my $response = $ua->get($url) or die "Cannot retrieve XML\n";
#print $response->decoded_content;

#Parse JSON
my $ref = from_json($response->decoded_content);

my %site2cms = ();
my %site2lcg = ();

foreach my $item (@{$ref->{'result'}}) {
    my $type = $item->[0];
    my $site_name = $item->[1];
    my $alias = $item->[2];

    if ($type eq 'cms') {
	$site2cms{$site_name} = $alias;
    } elsif ($type eq 'lcg') {
	$site2lcg{$site_name} = $alias;
    }
}

foreach (keys %site2cms) {
    print $site2cms{$_} . "\t" . $site2lcg{$_} . "\n";
}

exit 0;

print map("$_\n", sort @sites);

# Handler routines

sub h_char_names {
    my $p = shift;
    my $a = shift;

    if ($p->in_element('cms')) {
	push @sites, $a unless grep (/$a/, @sites);
    }
}
