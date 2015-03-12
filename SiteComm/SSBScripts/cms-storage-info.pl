#!/usr/bin/perl -w
#####################################################################
#
# Storage information generator for the CMS Site Status Board
#
# Author: Andrea Sciaba'
# Notes: supersedes script InfoFromDBS_text by Xiao Mei
# Version: 1.1
# Date: 06/11/2013
#
#####################################################################

use warnings;
use LWP::Simple;
use XML::Parser;
use Net::LDAP;

$debug = 0;
$ssbdir = "/afs/cern.ch/cms/LCG/SiteComm/";
$mydir = $ARGV[0];
if ($mydir) {
    $ssbdir = $mydir;
}
$file_phedex_sub = "$ssbdir/subscription.txt";
$file_phedex_cust = "$ssbdir/custodial.txt";
$file_phedex_ncust = "$ssbdir/noncustodial.txt";
$file_used_online = "$ssbdir/usedOnline.txt";
$file_total_online = "$ssbdir/totalOnline.txt";
$file_free_online = "$ssbdir/freeOnline.txt";
$file_used_nearline = "$ssbdir/usedNearline.txt";
$file_total_nearline = "$ssbdir/totalNearline.txt";
$file_free_nearline = "$ssbdir/freeNearline.txt";
$file_install_online = "$ssbdir/installOnline.txt";
$file_install_nearline = "$ssbdir/installNearline.txt";

$bdii = "lcg-bdii.cern.ch:2170";

# Information sources: PhEDEx data service, DBS, BDII

# Associate SEs to PhEDEx nodes
&phedex_se;

# Loop on all CMS SAs and sum up space information by site
&bdii_info;

# Output PhEDEx information
open(PHEDEX_SUB, "> $file_phedex_sub") or
    die "Cannot create $file_phedex_sub\n";
open(PHEDEX_CUST, "> $file_phedex_cust") or
    die "Cannot create $file_phedex_cust\n";
open(PHEDEX_NCUST, "> $file_phedex_ncust") or
    die "Cannot create $file_phedex_ncust\n";

# 1) Loop on all sites with at least one PhEDEx node
# 2) For each site, loop on all its PhEDEx nodes
# 3) skip node if PhEDEx has no information about it
# 4) extract subscribed data, custodial data, non-custodial data at site
# 5) write in SSB for sites with information
foreach my $cms (sort keys %cms2phedex) {
    my ($tsub, $tcust, $tncust, $turl, $hasnode) = (0, 0, 0, '', 0);
    my @nodes = @{$cms2phedex{$cms}};
    foreach my $node (@nodes) {
	next if ($node =~ /^TX/ or $node =~ /^TV/);
	my ($sub, $cust, $ncust, $url) = &get_phedex_info($node);
	next if ($sub == -1);
	$hasnode = 1;
	$turl = "https://cmsweb/phedex/prod/Reports::SiteUsage?node=$node#" unless ($node =~ /Disk/ or $node =~ /Buffer/);
	$tsub += $sub;
	$tcust += $cust;
	$tncust += $ncust;
    }
    next unless ($hasnode);
    my $time = &timestamp;
    my $color = "green";
    printf PHEDEX_SUB "%s\t%s\t%.1f\t%s\t%s\n", $time, $cms, $tsub,
    $color, $turl;
    printf PHEDEX_CUST "%s\t%s\t%.1f\t%s\t%s\n", $time, $cms, $tcust,
    $color, $turl;
    printf PHEDEX_NCUST "%s\t%s\t%.1f\t%s\t%s\n", $time, $cms, $tncust,
    $color, $turl;
}
close PHEDEX_SUB;
close PHEDEX_CUST;
close PHEDEX_NCUST;

# Generate SSB files with BDII information
# Values set to -1 if nothing was found in BDII

# TotalOnline: red if space <= 1 TB or information missing
open(BDII, "> $file_total_online") or
    die "Cannot create $file_total_online\n";
foreach my $cms (sort keys %cms2phedex) {
    my $time = &timestamp;
    my $color = "green";
    my $turl = 'n/a';
    my $space = -1;
    $space = $total_online{$cms} if (defined $total_online{$cms});
    if (defined $total_online{$cms} && $total_online{$cms} > 0 && defined $used_online{$cms} && defined $free_online{$cms}) {
	if (abs($total_online{$cms} - $used_online{$cms} - $free_online{$cms}) / $total_online{$cms} > 0.1) {
	    $color = "yellow";
	}
    }
    $color = "red" if ($space <= 1);
    printf BDII "%s\t%s\t%.1f\t%s\t%s\n", $time, $cms,
    $space, $color, $turl;
}
close BDII;

# UsedOnline: red if space <= 1 TB or information missing
open(BDII, "> $file_used_online") or
    die "Cannot create $file_used_online\n";
foreach my $cms (sort keys %cms2phedex) {
    my $time = &timestamp;
    my $color = "green";
    my $turl = 'n/a';
    my $space = -1;
    $space = $used_online{$cms} if (defined $used_online{$cms});
    $color = "red" if ($space <= 1);
    printf BDII "%s\t%s\t%.1f\t%s\t%s\n", $time, $cms,
    $space, $color, $turl;
}
close BDII;

# FreeOnline: red if space <= 1 TB or information missing
open(BDII, "> $file_free_online") or
    die "Cannot create $file_free_online\n";
foreach my $cms (sort keys %cms2phedex) {
    my $time = &timestamp;
    my $color = "green";
    my $turl = 'n/a';
    my $space = -1;
    $space = $free_online{$cms} if (defined $free_online{$cms});
    $color = "red" if ($space <= 1);
    printf BDII "%s\t%s\t%.1f\t%s\t%s\n", $time, $cms,
    $space, $color, $turl;
}
close BDII;

# TotalNearline: red if information missing
open(BDII, "> $file_total_nearline") or
    die "Cannot create $file_total_nearline\n";
foreach my $cms (sort keys %cms2phedex) {
    my $time = &timestamp;
    my $color = "green";
    my $turl = 'n/a';
    my $space = -1;
    my $t1 = ($cms ne 'T1_CH_CERN' and $cms =~ /^T[01]/);
    $space = $total_nearline{$cms} if (defined $total_nearline{$cms});
    if (defined $total_nearline{$cms} && $total_nearline{$cms} > 0 && defined $used_nearline{$cms} && defined $free_nearline{$cms}) {
	if (abs($total_nearline{$cms} - $used_nearline{$cms} - $free_nearline{$cms}) / $total_nearline{$cms} > 0.1) {
	    $color = "yellow";
	}
    }
    $color = "red" if ($space <= 1 && $t1);
    printf BDII "%s\t%s\t%.1f\t%s\t%s\n", $time, $cms,
    $space, $color, $turl;
}
close BDII;

# UsedNearline: red if information missing
open(BDII, "> $file_used_nearline") or
    die "Cannot create $file_used_nearline\n";
foreach my $cms (sort keys %cms2phedex) {
    my $time = &timestamp;
    my $color = "green";
    my $turl = 'n/a';
    my $space = -1;
    my $t1 = ($cms ne 'T1_CH_CERN' and $cms =~ /^T[01]/);
    $space = $used_nearline{$cms} if (defined $used_nearline{$cms});
    $color = "red" if ($space <= 1 && $t1);
    printf BDII "%s\t%s\t%.1f\t%s\t%s\n", $time, $cms,
    $space, $color, $turl;
}
close BDII;

# FreeNearline: red if information missing
open(BDII, "> $file_free_nearline") or
    die "Cannot create $file_free_nearline\n";
foreach my $cms (sort keys %cms2phedex) {
    my $time = &timestamp;
    my $color = "green";
    my $turl = 'n/a';
    my $space = -1;
    my $t1 = ($cms ne 'T1_CH_CERN' and $cms =~ /^T[01]/);
    $space = $free_nearline{$cms} if (defined $free_nearline{$cms});
    $color = "red" if ($space <= 1 && $t1);
    printf BDII "%s\t%s\t%.1f\t%s\t%s\n", $time, $cms,
    $space, $color, $turl;
}
close BDII;

# InstalledOnline: red if information missing
open(BDII, "> $file_install_online") or
    die "Cannot create $file_install_online\n";
foreach my $cms (sort keys %cms2phedex) {
    my $time = &timestamp;
    my $color = "green";
    my $turl = 'n/a';
    my $space = -1;
    $space = $inst_online{$cms} if (defined $inst_online{$cms});
    if (defined $inst_online{$cms} && defined $total_online{$cms} && ($inst_online{$cms} + $total_online{$cms}) > 0) {
	if (2. * abs($inst_online{$cms} - $total_online{$cms}) / ($inst_online{$cms} + $total_online{$cms}) > 0.1) {
	    $color = "yellow";
	}
    }
    $color = "red" if ($space <= 1);
    printf BDII "%s\t%s\t%.1f\t%s\t%s\n", $time, $cms,
    $space, $color, $turl;
}
close BDII;

# InstalledNearline: red if information missing
open(BDII, "> $file_install_nearline") or
    die "Cannot create $file_install_nearline\n";
foreach my $cms (sort keys %cms2phedex) {
    my $time = &timestamp;
    my $color = "green";
    my $turl = 'n/a';
    my $space = -1;
    my $t1 = ($cms ne 'T1_CH_CERN' and $cms =~ /^T[01]/);
    $space = $inst_nearline{$cms} if (defined $inst_nearline{$cms});
    if (defined $inst_nearline{$cms} && defined $total_nearline{$cms} && ($inst_nearline{$cms} + $total_nearline{$cms}) > 0) {
	if (2. * abs($inst_nearline{$cms} - $total_nearline{$cms}) / ($inst_nearline{$cms} + $total_nearline{$cms}) > 0.1) {
	    $color = "yellow";
	}
    }
    $color = "red" if ($space <= 1 && $t1);
    printf BDII "%s\t%s\t%.1f\t%s\t%s\n", $time, $cms,
    $space, $color, $turl;
}
close BDII;

# Map between storage elements and PhEDEx nodes
# %cms2phedex: maps CMS site name to array of PhEDEx nodes
# %node2se: maps PhEDEx node to SE

sub phedex_se {
    my $url = "https://cmsweb.cern.ch/phedex/datasvc/xml/prod/nodes";
    my $doc = get($url) or die "Cannot retrieve XML from $url\n";
    $p = new XML::Parser(Handlers => {Start => \&h_start_phedex});
    $p->parse($doc);
}
    
sub h_start_phedex {
    my $p = shift;
    my $e = shift;
    my %attr = ();
    while (@_) {
	my $a = shift;
	my $v = shift;
	$attr{$a} = $v;
    }
    if ($e eq 'node') {
	my $se = $attr{'se'};
	$se = 'srm.pic.es' if ($se eq 'srmcms.pic.es');
	my $node = $attr{'name'};
	$node2se{$node} = $se;
	my $cms = $node;
	$cms =~ s/_(Buffer|MSS|Export|Disk)//;
	my @nodes = ();
	@nodes = @{$cms2phedex{$cms}} if ($cms2phedex{$cms});
	push @nodes, $node;
	$cms2phedex{$cms} = \@nodes;
    }
}


# Query BDII information
sub bdii_info {

# Space is given in TB
    my $k = 1000;
    my $ldap;
    unless ($ldap = Net::LDAP->new($bdii)) {
	warn "Cannot contact $bdii\n";
	return 0;
    }
    my $mesg = $ldap->bind;
    if ($mesg->is_error()) {
	warn "Cannot bind $bdii\n";
	return 0;
    }
    my $base = 'o=grid';

# TODO: check if needed to add VOMS:/cms/*. Answer: NO
    my $filter = '(&(objectclass=GlueSA)(|(GlueSAAccessControlBaseRule=cms)(GlueSAAccessControlBaseRule=VO:cms)))';

# Search all storage areas for CMS
    $mesg = $ldap->search(
			  base => $base,
			  filter => $filter);
    if ($mesg->is_error()) {
	$ldap->unbind();
	warn "Cannot search $bdii\n";
	return 0;
    }

# Loop on all CMS Storage Areas
    foreach my $entry ($mesg->entries()) {
	my $said = $entry->get_value('GlueSALocalID');
	my $dn = $entry->dn();

# Get storage element and skip SA if no SE is found
	my $se = '';
	foreach my $ck ($entry->get_value('GlueChunkKey')) {
	    if ($ck =~ /GlueSEUniqueID=(.+)/) {
		$se = $1;
	    }
	}
	if ($se eq '') {
	    warn "SA with no SE: $dn\n" if ($debug);
            next;
	}

# Exceptions
	next if ($se eq 'srmcms.pic.es');

# Retrieve all Glue 1.3 space attribute values
	my $total_online = $entry->get_value('GlueSATotalOnlineSize');
	my $free_online = $entry->get_value('GlueSAFreeOnlineSize');
	my $used_online = $entry->get_value('GlueSAUsedOnlineSize');
	my $total_nearline = $entry->get_value('GlueSATotalNearlineSize');
	my $free_nearline = $entry->get_value('GlueSAFreeNearlineSize');
	my $used_nearline = $entry->get_value('GlueSAUsedNearlineSize');
	my $inst_online = -1;
	my $inst_nearline = -1;
	foreach my $ic ($entry->get_value('GlueSACapability')) {
	    if ($ic =~ /InstalledOnlineCapacity=(.+)/) {
		$inst_online = $1;
	    } elsif ($ic =~ /InstalledNearlineCapacity=(.+)/) {
		$inst_nearline = $1;
	    } 
	}

# Skip storage area if its storage element is not in PhEDEx
# 1) Loop on CMS sites with >0 PhEDEx nodes
# 2) Loop on site's PhEDEx nodes
# 3) See if node's SE is our SE
# 4) If SE is in PhEDEx, proceed and remember the SE's site name
	my $cms;
	my $isinphedex = 0;
        ses: foreach $c (keys %cms2phedex) {
	    foreach my $n (@{$cms2phedex{$c}}) {
	        my $s = $node2se{$n};
	        if (defined $s and $s eq $se) {
		    $cms = $c;
		    $isinphedex = 1;
		    last ses;
		}
	    }
        }
	next unless $isinphedex;

# Sum up all spaces at the site (remember that we are looping on SAs)
# If a particular space attribute is undefined, it is silently not summed :-)
	if (! defined $total_online) {
	    warn "WARNING: SA without TotalOnlineSize: $dn\n" if ($debug);
	} else {
	    if (defined $total_online{$cms}) {
		$total_online{$cms} += $total_online / $k;
	    } else {
		$total_online{$cms} = $total_online / $k;
	    }
	}
	if (! defined $used_online) {
	    warn "WARNING: SA without UsedOnlineSize: $dn\n" if ($debug);
	} else {
	    if (defined $used_online{$cms}) {
		$used_online{$cms} += $used_online / $k;
	    } else {
		$used_online{$cms} = $used_online / $k;
	    }
	}
	if (! defined $free_online) {
	    warn "WARNING: SA without FreeOnlineSize: $dn\n" if ($debug);
	} else {
	    if (defined $free_online{$cms}) {
		$free_online{$cms} += $free_online / $k;
	    } else {
		$free_online{$cms} = $free_online / $k;
	    }
	}
	if (! defined $total_nearline) {
	    warn "WARNING: SA without TotalNearlineSize: $dn\n" if ($debug);
	} else {
	    if (defined $total_nearline{$cms}) {
		$total_nearline{$cms} += $total_nearline / $k;
	    } else {
		$total_nearline{$cms} = $total_nearline / $k;
	    }
	}
	if (! defined $used_nearline) {
	    warn "WARNING: SA without UsedNearlineSize: $dn\n" if ($debug);
	} else {
	    if (defined $used_nearline{$cms}) {
		$used_nearline{$cms} += $used_nearline / $k;
	    } else {
		$used_nearline{$cms} = $used_nearline / $k;
	    }
	}
	if (! defined $free_nearline) {
	    warn "WARNING: SA without FreeNearlineSize: $dn\n" if ($debug);
	} else {
	    if (defined $free_nearline{$cms}) {
		$free_nearline{$cms} += $free_nearline / $k;
	    } else {
		$free_nearline{$cms} = $free_nearline / $k;
	    }
	}
	if ($inst_online == -1) {
	    warn "WARNING: SA without InstalledOnlineCapacity: $dn\n" if ($debug);
	} else {
	    if (defined $inst_online{$cms}) {$inst_online{$cms} += $inst_online / $k}
	    else {$inst_online{$cms} = $inst_online / $k};
	}
	if ($inst_nearline == -1) {
	    warn "WARNING: SA without InstalledNearlineCapacity: $dn\n" if ($debug);
	} else {
	    if (defined $inst_nearline{$cms}) {$inst_nearline{$cms} += $inst_nearline / $k}
	    else {$inst_nearline{$cms} = $inst_nearline / $k};
	}
    }
}

sub get_phedex_info {

# Input: PhEDEx node
# Output: ( cust_dest + noncust_dest - cust_node - noncust_node,
#           cust_node,
#           noncust_node,
#           nodeusage_url
#         )

    my $node = shift;
    my ($s, $c, $n) = (-1, -1, -1);
    my $url = "https://cmsweb.cern.ch/phedex/datasvc/xml/prod/nodeusage?node=$node";
    my $doc;
    my $count = 0;
    while ($count < 3) {
	$doc = get($url);
	last if (defined $doc);
	sleep 5;
	$count++;
    }
    if (! defined $doc) {
	warn "Could not get node info after 3 attempts: $url\n";
	return ($s, $c, $n, $url);
    }

# PhEDEx numbers are set to -1 when information is missing
# Space measured in TB (powers of 1000)
    my $k = (1000 * 1000 * 1000 * 1000); 
    if ($doc =~ /cust_node_bytes='(\d+)'.*cust_dest_bytes='(\d+)'.*noncust_dest_bytes='(\d+)'.*noncust_node_bytes='(\d+)'/) {
	$s = ($2 + $3 - $1 - $4) / $k;
	$c = $1 / $k;
	$n = $4 / $k;
    } elsif ($debug) {
	warn "WARNING: PhEDEx information incomplete or missing for node $node\n";
    }
    return ($s, $c, $n, $url);
}

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
