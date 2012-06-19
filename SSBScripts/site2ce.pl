#!/usr/bin/perl -w
######################################################################
#
# site2ce.pl [--bdii <bdii>] --vo <vo> site
#
# Author: Andrea Sciaba' <Andrea.Sciaba@cern.ch>
#
# Version: 1.0.
#
#   --bdii <bdii>: <bdii> must be in format <hostname>:<port>. If not
#                  specified, LCG_GFAL_INFOSYS is used
#   --vo <vo>:     <vo> must be in format VO:<vo> or VOMS:<fqan>
#   <site>:        <site> corresponds to GlueSiteName
#
######################################################################
use Getopt::Long;
use Net::LDAP;
use Net::LDAP::Message;
use Net::LDAP::Filter;
use LWP::Simple;
use XML::Parser;
use Pod::Usage;

$NAME = 'site2ce.pl';

# Array with all Sites and tiers
%sites = ();
$vo = "cms";
$compact = 0;

GetOptions(
	   'bdii=s' => \$bdii,
	   'vo=s' => \$vo,
	   'compact' => \$compact
	   ) or die("$NAME: wrong arguments.\n");

# BDII server
if (! $bdii) {
    $bdii = $ENV{LCG_GFAL_INFOSYS} or die("$NAME: LCG_GFAL_INFOSYS undefined.\n");
}
@bdiilist = split /,/, $bdii;

if (@ARGV == 0) {
    die("$NAME: a site must be specified.\n");
}
my $site = $ARGV[0];

#Get XML file from SiteDB

my $url = "https://cmsweb.cern.ch/sitedb/reports/showXMLReport?reportid=cms_to_sam.ini";
my $doc = get($url) or die "Cannot retrieve XML\n";

# Parse XML

$p = new XML::Parser(Handlers => {Start => \&h_start, Char  => \&h_char});
$p->parse($doc) or die "Cannot parse XML\n";

@site_list = ();
foreach my $s (values %sites) {
    if ($s->{CMS} eq $site) {
	push @site_list, $s->{SAM};
	if (! $compact) {
	    print "CMS name:  " . $s->{CMS} . "\n";
	    print "BDII name: " . $s->{SAM} . "\n";
        }
	$found = 1;
    }
}
if ( ! $found and ! $compact) {
	print "BDII name: " . $site . "\n";
}

my $ldap = &bdii_init(@bdiilist) or die "$NAME: cannot contact LDAP server.\n";
for $site (@site_list) {
    my $siteid = &siteid($ldap, $site) or die "$NAME: site $site not found.\n";
    my @clusters = &clusters($ldap, $siteid) or warn "$NAME: no clusters associated to site $site.\n";

    if ($output and $compact) {
	print ",";
    }
    $output = '';
    $found = 0;
    foreach my $clusterid (@clusters) {
	my @ces = &ce($ldap, $clusterid, $vo);
	if (! $compact) {
	    map {$output .= "$_\n"} @ces;
	} else {
	    map {$output .= "$_,"} @ces;
	}
    }
    $output =~ s/,$//;
    if ( ! $output ) {
	die "No CEs found\n";
    }
    print $output;
}

sub bdii_init {
    my @bdiilist = @_;
    my $ldap = 0;
    foreach my $bdii (@bdiilist) {
        unless ($ldap = Net::LDAP->new($bdii)) {
            warn("$NAME: failed to contact BDII $bdii.\n");
            next;
        }
        $mesg = $ldap->bind;
        if ($mesg->is_error()) {
            warn("$NAME: error in binding the BDII:\n$mesg->error_text().\n");
            next;
        }
    }
    return $ldap;
}


sub siteid {
    my ($ldap, $site) = @_;
    my $siteid;
    my $base = 'o=grid';
    my $filter = "(&(objectclass=GlueSite)(GlueSiteName=$site))";
    my $mesg = $ldap->search(base   => $base,
                             filter => $filter);
    if ( $mesg->is_error() ) {
        $ldap->unbind();
        warn ("$NAME: error searching the BDII:\n$mesg->error()\n");
	return $siteid;
    }
    my $entry = $mesg->entry(0);
    if (! $entry) {
        $ldap->unbind();
	return $siteid;
    }
    $siteid = $entry->get_value('GlueSiteUniqueID');
    return $siteid;
}

sub clusters {
    my ($ldap, $siteid) = @_;
    my @clusters;
    my $base = 'o=grid';
    my $filter = "(&(objectclass=GlueCluster)(GlueForeignKey=GlueSiteUniqueID=$siteid))";
    my $mesg = $ldap->search(base   => $base,
                             filter => $filter);
    if ( $mesg->is_error() ) {
        $ldap->unbind();
        warn ("$NAME: error searching the BDII:\n$mesg->error()\n");
	return @clusters;
    }
    foreach my $entry ($mesg->entries()) {
	push @clusters, $entry->get_value('GlueClusterUniqueID');
    }
    return @clusters;
}

sub ce {
    my ($ldap, $clusterid, $vo) = @_;
    my $base = 'o=grid';
    my @ces;
    my $filter = "(&(objectclass=GlueCE)(|(GlueCEAccessControlBaseRule=VO:$vo)(GlueCEAccessControlBaseRule=VOMS:/$vo/*))(GlueCEStateStatus=Production)(GlueForeignKey=GlueClusterUniqueID=$clusterid))";
    my $mesg = $ldap->search(base   => $base,
                             filter => $filter);
    if ( $mesg->is_error() ) {
        $ldap->unbind();
        warn ("$NAME: error searching the BDII:\n$mesg->error()\n");
	return @ces;
    }
    foreach my $entry ($mesg->entries()) {
	my $hostname = $entry->get_value('GlueCEInfoHostName');
	push @ces, $hostname if (!grep{/$hostname/} @ces);
    }
    return @ces;
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

sub h_char {
    my $p = shift;
    my $a = shift;

    if ($p->in_element('cms_name')) {
        my $site = $sites{$lastid};
        $site->{CMS} = $a;
    } elsif ($p->in_element('sam_name')) {
        my $site = $sites{$lastid};
        $site->{SAM} = $a;
    }
    
}

package Site;

sub new {
    my $class = shift;
    my $id = shift;
    my $self = {ID => $id, CMS => '', SAM => ''};
    bless $self, $class;
}
