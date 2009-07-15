#!/usr/bin/perl -w

use LWP::Simple;
use Time::Local;

# Commissioning criteria
$thrsh = 50;   # Minimum quality
$t1ft0 = 1;    # Minimum number of links from T0 for T1
$t1ft1 = 2;    # Minimum number of links from T1 for T1
$t1tt1 = 2;    # Minimum number of links to T1 for T1
$t1tt2 = 10;   # Minimum number of links to T2 for T1
$t1ft2 = 0;    # Minimum number of links from T2 for T1
$t2ft1 = 2;    # Minimum number of links from T1 for T2
$t2tt1 = 1;    # Minimum number of links to T1 for T2

$debug = 1;

# Variable initialization
$base_url_debug = "http://cmsweb.cern.ch/phedex/debug/Reports::DailyReport?reportfile=__date__.txt";
$base_url_prod = "http://cmsweb.cern.ch/phedex/production/Reports::DailyReport?reportfile=__date__.txt";
%lup = %hup = %outcross = %incross = %ldown = %hdown = ();
%t_lup = %t_hup = %t_outcross = %t_incross = %t_ldown = %t_hdown = ();

die "Usage: Links.pl [date]\n" if (@ARGV > 1);

# Input is the day, otherwise today by default
my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday) = gmtime(time);
$mday = "0$mday" if (length($mday) == 1);
$year += 1900;
$mon += 1;
$mon = "0$mon" if (length($mon) == 1);
$date = $year . $mon . $mday;
$date = $ARGV[0] if ( $ARGV[0] );

# Time interval for PhEDEx plots
($start, $end) = &dategm($date);

# HTML report locations
$dir = '/afs/cern.ch/user/a/asciaba/www/links';
$file = "link_qual_$date.html";
$url_report = "http://cern.ch/asciaba/links/$file";

# SSB input file
$ssbdir = "/afs/cern.ch/cms/LCG/SiteComm";
$ssbpath = "$ssbdir/links_quality.txt";

# URL for PhEDEx reports
$url_prod = $base_url_prod;
$url_prod =~ s/__date__/$date/;
$url_debug = $base_url_debug;
$url_debug =~ s/__date__/$date/;

# Parsing and combination production+debug
($dbgtime, $ref1) = &get_quality($url_debug);
%quality_debug = %$ref1;
($prdtime, $ref2) = &get_quality($url_prod);
%quality_prod  = %$ref2;
%quality       = &quality_combine(\%quality_debug, \%quality_prod);
foreach ( keys %quality ) {
    $lup{$_} = $hup{$_} = $ldown{$_} = $hdown{$_} = $outcross{$_} = $incross{$_} = 0;
    $t_lup{$_} = $t_hup{$_} = $t_ldown{$_} = $t_hdown{$_} = $t_outcross{$_} = $t_incross{$_} = 0;
}


# Calculate number of good links per site
$totlinks = 0;
$goodlinks = 0;
foreach my $site ( keys %quality ) {
    my $tier = substr($site, 1, 1);
    foreach my $dest ( keys %{$quality{$site}} ) {
	my $dtier = substr($dest, 1, 1);
	my $q = $quality{$site}{$dest}[0];
	$totlinks++;
	$goodlinks++ if ( $q >= $thrsh );

# Uplinks
	if ( $tier > $dtier ) {
	    $hup{$dest}++ if ( $q >= $thrsh );
	    $lup{$site}++ if ( $q >= $thrsh );
	    $t_hup{$dest}++;
	    $t_lup{$site}++;

# Links between Tier-1's
	} elsif ( $tier == $dtier ) {
	    $outcross{$site} += 1 if ( $q >= $thrsh );
	    $incross{$dest} += 1 if ( $q >= $thrsh );
	    $t_outcross{$site}++;
	    $t_incross{$dest}++;

# Downlinks
	} elsif ( $tier < $dtier ) {
	    $ldown{$dest}++ if ( $q >= $thrsh );
	    $hdown{$site}++ if ( $q >= $thrsh );
	    $t_ldown{$dest}++;
	    $t_hdown{$site}++;
	    if ( $tier == 0 ) {
		$outcross{'T1_CH_CERN_Buffer'}++ if ( $q >= $thrsh );
		$t_outcross{'T1_CH_CERN_Buffer'}++;
	    }
	}
    }
}

print "Tot links: $totlinks  Good links: $goodlinks\n";

# Correction for CERN
$ldown{'T1_CH_CERN_Buffer'}++;
$t_ldown{'T1_CH_CERN_Buffer'}++;

# Generate HTML report
if ( $debug ) {
    open(HTML, ">$dir/$file") or die "Cannot write HTML report\n";
    print HTML &header;
    foreach ( sort keys %quality ) {
	my $tier = substr($_, 1, 1);
	if ( $tier == 1 ) {
	    print HTML &site_report($_);
	} elsif ( $tier == 2 ) {
	    print HTML &site_report($_);
	}
    }
    print HTML &footer;
    close HTML;
    unlink "$dir/link_qual_latest.html";
    symlink "$dir/$file", "$dir/link_qual_latest.html";
}

# Generate input files for SSB
open(SSB, ">$ssbpath") or die "Cannot write SSB input file\n";
foreach my $site ( sort keys %quality ) {
    next if ( $site =~ /^T0/ );
    my $timestamp = &timestamp;
    my $status = 'no';
    my $color = 'red';
    my @status = &site_status2($site);
    if ( $status[0] ) {
	$status = 'yes';
	$color = 'green';
    }
    $site =~ s/_Export//;
    $site =~ s/_Buffer//;
    $site =~ s/_Disk//;
    printf SSB "%s\t%s\t%s\t%s\t%s\n", $timestamp, $site, $status, $color,
    $url_report;
}
close SSB;

&generate_ssbfile("$ssbdir/links_quality_t1ft0.txt", 1, 1);
&generate_ssbfile("$ssbdir/links_quality_t1ft1.txt", 1, 3);
&generate_ssbfile("$ssbdir/links_quality_t1tt1.txt", 1, 2);
&generate_ssbfile("$ssbdir/links_quality_t1ft2.txt", 1, 5);
&generate_ssbfile("$ssbdir/links_quality_t1tt2.txt", 1, 4);
&generate_ssbfile("$ssbdir/links_quality_t2ft1.txt", 2, 3);
&generate_ssbfile("$ssbdir/links_quality_t2tt1.txt", 2, 2);

sub generate_ssbfile {
    my $filename = shift;
    my $tier = shift;
    my $index = shift;
    my @map;
    if ( $tier == 1 ) {
	@map = ('ldown', 'outcross', 'incross', 'hdown', 'hup');
    } else {
	@map = ('', 'lup', 'ldown');
    }
    open(SSBL, ">$filename") or die "Cannot write SSB input file $filename\n";
    foreach my $site ( sort keys %quality ) {
	my $t = substr($site, 1, 1);
	next if ( $site =~ /^T0/ );
	next if ( $t != $tier );
	my $timestamp = &timestamp;
	my $status = ${$map[$index-1]}{$site};
	my $color = 'red';
	my @status = &site_status2($site);
	if ( $status[$index] ) {
	    $color = 'green';
	}
	$site =~ s/_Export//;
	$site =~ s/_Buffer//;
	$site =~ s/_Disk//;
	printf SSBL "%s\t%s\t%s\t%s\t%s\n", $timestamp, $site, $status, $color,
	$url_report;
    }
    close SSBL;
}

# Returns 1 if the site satisfies sitecomm metrics, 0 otherwise
sub site_status {
    my $site = shift;
    my @status = (0, 0, 0, 0, 0, 0);
    my $tier = substr($site, 1, 1);
    if ( $tier == 1 ) {
	$status[1] = ($ldown{$site} >= $t1ft0);
	$status[3] = ($incross{$site} >= $t1ft1);
	$status[2] = ($outcross{$site} >= $t1tt1);
	$status[5] = ($hup{$site} >= $t1ft2);
	$status[4] = ($hdown{$site} >= $t1tt2);
	$status[0] = $status[1] && $status[2] && $status[3] &&
	    $status[4] && $status[5];
    } elsif ( $tier == 2 ) {
	$status[3] = ($ldown{$site} >= $t2ft1);
	$status[2] = ($lup{$site} >= $t2tt1);
	$status[0] = $status[2] && $status[3];
    }
    return @status;
}

# Version using the new metrics (number of good links >= 50% of links)
sub site_status2 {
    my $site = shift;
    my @status = (0, 0, 0, 0, 0, 0);
    my $tier = substr($site, 1, 1);
    if ( $tier == 1 ) {
	$status[1] = ($ldown{$site} >= int(0.5*$t_ldown{$site}));
	$status[3] = ($incross{$site} >= int(0.5*$t_incross{$site}));
	$status[2] = ($outcross{$site} >= int(0.5*$t_outcross{$site}));
	$status[5] = ($hup{$site} >= int(0.5*$t_hup{$site}));
	$status[4] = ($hdown{$site} >= int(0.5*$t_hdown{$site}));
	$status[0] = $status[1] && $status[2] && $status[3] &&
	    $status[4] && $status[5];
    } elsif ( $tier == 2 ) {
	$status[3] = ($ldown{$site} >= int(0.5*$t_ldown{$site}));
	$status[2] = ($lup{$site} >= int(0.5*$t_lup{$site}));
	$status[0] = $status[2] && $status[3];
    }
    return @status;
}

sub color {
    my $s = shift;
    my $c = 'red';
    $c = 'white' if ( $s );
    return $c;
}

sub site_report {
    my $site = $_;
    my $output = "";
    my $tier = substr($site, 1, 1);
    my @status = &site_status2($site);
    if ( $tier == 1 ) {
	$output =
	    "<tr><td bgcolor=" . &color($status[0]) . ">$site</td>" .
	    "<td align=\"center\" bgcolor=" . &color($status[1]) .
	    "><a href=\"".
	    &phedex_link($site, 1) . "\">$ldown{$site}</a></td>" .
	    "<td align=\"center\" bgcolor=" . &color($status[3]) .
	    "><a href=\"".
	    &phedex_link($site, 3) . "\">$incross{$site}</a></td>" .
	    "<td align=\"center\" bgcolor=" . &color($status[2]) .
	    "><a href=\"".
	    &phedex_link($site, 2) . "\">$outcross{$site}</a></td>" .
	    "<td align=\"center\" bgcolor=" . &color($status[5]) .
	    "><a href=\"".
	    &phedex_link($site, 5) . "\">$hup{$site}</a></td>" .
	    "<td align=\"center\" bgcolor=" . &color($status[4]) .
	    "><a href=\"".
	    &phedex_link($site, 4) . "\">$hdown{$site}</a></td>" .
	    "</tr>\n";
    } elsif ( $tier == 2 ) {
	$output =
	    "<tr><td bgcolor=" . &color($status[0]) . ">$site</td>" .
	    "<td>&nbsp;</td>" .
	    "<td align=\"center\" bgcolor=" . &color($status[3]) .
	    "><a href=\"".
	    &phedex_link($site, 3) . "\">$ldown{$site}</a></td>" .
	    "<td align=\"center\" bgcolor=" . &color($status[2]) .
	    "><a href=\"".
	    &phedex_link($site, 2) . "\">$lup{$site}</a></td>" .
	    "<td>&nbsp;</td>" .
	    "<td>&nbsp;</td>" .
	    "</tr>\n";
    }	
    return $output
}

sub get_quality {
    my $url = shift;
    my $report = get($url) or die "Cannot retrieve PhEDEx report\n";
    my $parse = 0;
    my $gentime;
    my %quality = ();
    foreach ( split /\n/, $report ) {
	if ( /generated at (.*) by/ ) {
	    $gentime = $1;
	}
	$parse = 1 if ( /1-day period/ );
	$parse = 0 if ( /7-day period/ );
	if ( $parse ) {
	    if ( /^(T\w*)\s+/ ) {
		$dest = $1 ;
	    }
	    if ( /^\. (T\w+)/ ) {
		$source = $1;
		next if ( $source =~ /MSS/ || $dest =~ /MSS/ );
		next if ( $source =~ /^T3/ || $dest =~ /^T3/ );
		my @data = split /\s+/, $_;
		my $succ = $data[5];
		$succ =~ s/%//;
		$succ = 0 if ( $succ eq 'N/A' );
		my $ftot = $data[4];
		if ( $debug ) {
		    system("echo $succ >> quality.vec");
		}
		$quality{$source}{$dest} = [$succ, $ftot];
	    }
	}
    }
    return ($gentime, \%quality);
}

sub quality_combine {
    my ($hashref1, $hashref2) = @_;
    my %q1 = %$hashref1;
    my %q2 = %$hashref2;
    my %q;
    my @sites = ();
    foreach my $s (keys %q1, keys %q2) {
	push @sites, $s if ( ! grep(/$s/, @sites) );
    }
    foreach my $s ( @sites ) {
	my @dests = ();
	foreach my $d ( keys %{$q1{$s}}, keys %{$q2{$s}} ) {
	    push @dests, $d if ( ! grep(/$d/, @dests) );
	}
	foreach my $d ( @dests ) {
	    my $q1 = (defined ${$q1{$s}{$d}}[0])?${$q1{$s}{$d}}[0]:-1;
	    my $q2 = (defined ${$q2{$s}{$d}}[0])?${$q2{$s}{$d}}[0]:-1;
	    my $t1 = (defined ${$q1{$s}{$d}}[1])?${$q1{$s}{$d}}[1]:-1;
	    my $t2 = (defined ${$q2{$s}{$d}}[1])?${$q2{$s}{$d}}[1]:-1;
	    my $q;
	    my $t;
	    if ( $q1 < 0 ) {
		$q = $q2;
		$t = $t2;
	    } elsif ( $q2 < 0 ) {
		$q = $q1;
		$t = $t1;
	    } elsif ( $q1 == 0 ) {
		$q = $q2;
		$t = $t2;
	    } elsif ( $q2 == 0 ) {
		$q = $q1;
		$t = $t1;
	    } else {
		$q = 1/((1/$q1*$t1+1/$q2*$t2)/($t1+$t2));
		$t = $t1+$t2;
	    }
	    $q{$s}{$d} = [$q, $t];
	}
    }
    return %q;
}

sub phedex_link {
    my $site = shift;
    my $type = shift;
    my $base_url = "http://cmsweb.cern.ch/phedex/graphs/quality_all?link=link&no_mss=true&to_node=__dest__&from_node=__src__&%2FWebSite&starttime=${start}&span=3600&endtime=${end}";
    my $tier = substr($site, 1, 1);
    my $url = $base_url;
    if ( $tier == 1 ) {
	if ( $type == 1 ) {              # CERN -> site
	    $url =~ s/__src__/CERN/;
	    $url =~ s/__dest__/$site/;
	} elsif ( $type == 2 ) {         # site -> T1
	    $site = 'CERN' if ( $site =~ /CERN/ );
	    $url =~ s/__src__/$site/;
	    $url =~ s/__dest__/T1/;
	    
	} elsif ( $type == 3 ) {         # T1 -> site
	    $url =~ s/__src__/T1/;
	    $url =~ s/__dest__/$site/;
	} elsif ( $type == 4 ) {         # site -> T2
	    $url =~ s/__src__/$site/;
	    $url =~ s/__dest__/T2/;
	} elsif ( $type == 5 ) {         # T2 -> site
	    $url =~ s/__src__/T2/;
	    $url =~ s/__dest__/$site/;
	}
    } elsif ( $tier == 2 ) {
	if ( $type == 2 ) {              # site -> T1
	    $url =~ s/__src__/$site/;
	    $url =~ s/__dest__/T1/;
	} elsif ( $type == 3 ) {         # T1 -> site
	    $url =~ s/__src__/T1/;
	    $url =~ s/__dest__/$site/;
	}
    }
    return $url;
}

sub header {
    my $string = 
	"<html><body>\n" .
	"<title>Site link quality report $date</title>\n" .
	"<h1>Number of good links per site</h1>\n" .
	"<p>Links are classified as follows:</p>\n" .
	"<table border=\"1\">\n" .
	"<tr><td>link from T0</td><td>the downlink from CERN</td></tr>\n" .
	"<tr><td>links from T1</td><td>for Tier-1 sites, the incoming links from other Tier-1 sites; for Tier-2 sites, the downlinks from Tier-1 sites</td></tr>\n" .
	"<tr><td>links to T1</td><td>for Tier-1 sites, the outgoing links to other Tier-1 sites; for Tier-2 sites, the uplinks to Tier-1 sites</td><tr>\n" .
	"<tr><td>links to T2</td><td>for Tier-1 sites, the downlinks to Tier-2 sites</td><tr>\n" .
	"</table>\n" .
	"<p>Links are counted only if they have a quality better than <b>$thrsh%</b> in the previous day. These are the minimum numbers of links per type:</p>\n" .
	"<table border=\"1\">\n" .
	"<tr><th>&nbsp;</th><th>Tier-1</th><th>Tier-2</th></tr>\n" .
	"<tr><td>link from T0</td><td>$t1ft0</td><td>&nbsp;</td></tr>\n" .
	"<tr><td>links from T1</td><td>$t1ft1</td><td>$t2ft1</td></tr>\n" .
	"<tr><td>links to T1</td><td>$t1tt1</td><td>$t2tt1</td></tr>\n" .
	"<tr><td>links to T2</td><td>$t1tt2</td><td>&nbsp;</td></tr>\n" .
	"</table>\n" .
	"<h2>Site status vs. good links</h2>\n" .
	"<p>PhEDEx <a href=\"$url_debug\">debug report</a> generated at $dbgtime.</p>\n" .
	"<p>PhEDEx <a href=\"$url_prod\">production report</a> generated at $prdtime.</p>\n" .
	"<table border=\"1\">\n" .
	"<colgroup span=\"6\">\n" .
	"<col></col>\n" .
	"<col width=\"80\"></col>\n" .
	"<col width=\"80\"></col>\n" .
	"<col width=\"80\"></col>\n" .
	"<col width=\"80\"></col>\n" .
	"<col width=\"80\"></col>\n" .
	"<tr><th>Site</th> <th>link from T0</th> <th>links from T1</th> <th>links to T1</th> <th>links from T2</th><th>links to T2</th></tr>\n";
    return $string;
}

sub footer {
    my $string =
	"</table>\n" .
	"</body></html>\n";
    return $string;
}

sub dategm {
    my $date = shift;
    my $year = substr($date, 0, 4);
    $year -= 1900;
    my $mon = substr($date, 4, 2);
    $mon -= 1;
    my $day = substr($date, 6, 2);
    my $start = timegm(0, 0, 0, $day, $mon, $year) - 86400;
    my $end = timegm(59, 59, 23, $day, $mon, $year) - 86400;
    return ($start, $end);
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
