#!/usr/bin/perl -w

use LWP::Simple;
use Time::Local;

# Commissioning criteria
$thrsh = 50;   # Minimum success rate

# Variable initialization
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

# SSB input file
$ssbdir = "/afs/cern.ch/cms/LCG/SiteComm";
#$ssbdir = "/tmp"; # remove after debugging

$url_prod = &datasvc_url('prod', $start, $end);
$url_debug = &datasvc_url('debug', $start, $end);

%quality_debug = &get_quality($url_debug);
%quality_prod = &get_quality($url_prod);
%quality = &quality_combine(\%quality_debug, \%quality_prod);

foreach ( keys %quality ) {
    $lup{$_} = $hup{$_} = $ldown{$_} = $hdown{$_} = $outcross{$_} = $incross{$_} = 0;
    $t_lup{$_} = $t_hup{$_} = $t_ldown{$_} = $t_hdown{$_} = $t_outcross{$_} = $t_incross{$_} = 0;
}

# Extract the commissioned links
%comm_links_prod = &comm_prod_links('prod');
%comm_links_debug = &comm_prod_links('debug');

# Calculate number of good links per site
$totlinks = 0;
$goodlinks = 0;
foreach my $site ( keys %quality ) {
    my $tier = substr($site, 1, 1);
    my $stier = $tier;
    $stier = 1 if ($stier == 0); # Treat T0_CH_CERN as a T1
    foreach my $dest ( keys %{$quality{$site}} ) {
	next unless ( $comm_links_prod{$site}{$dest} == 1 and
		      $comm_links_debug{$site}{$dest} == 1);
	my $dtier = substr($dest, 1, 1);
	$dtier = 1 if ($dtier == 0);
	my $q;
	if ($quality{$site}{$dest}[0]+$quality{$site}{$dest}[1] > 0) {
	    $q = 100. *
		$quality{$site}{$dest}[0] / ($quality{$site}{$dest}[0]+
					      $quality{$site}{$dest}[1]);
	} else {
	    $q = 0;
	}
	$totlinks++;
	$goodlinks++ if ( $q >= $thrsh );

# Uplinks
	if ( $stier > $dtier ) {
	    $hup{$dest}++ if ( $q >= $thrsh );
	    $lup{$site}++ if ( $q >= $thrsh );
	    $t_hup{$dest}++;
	    $t_lup{$site}++;

# Links between Tier-1's
	} elsif ( $stier == $dtier ) {
	    $outcross{$site} += 1 if ( $q >= $thrsh );
	    $incross{$dest} += 1 if ( $q >= $thrsh );
	    $t_outcross{$site}++;
	    $t_incross{$dest}++;
	}

# Downlinks
	if ( $tier < $dtier ) {
	    $ldown{$dest}++ if ( $q >= $thrsh );
	    $hdown{$site}++ if ( $q >= $thrsh );
	    $t_ldown{$dest}++;
	    $t_hdown{$site}++;
	}
    }
}

print "Tot links: $totlinks  Good links: $goodlinks\n";

# Generate combined rows for Tier-1 sites
@tsites = ();
foreach my $site ( sort keys %quality ) {
    my $t = substr($site, 1, 1);
    $t = 1 if ($t == 0);  # Treat T0_CH_CERN as a T1
    next if ( $t != 1 );
    my $tsite = $site;
    $tsite =~ s/_Export//;
    $tsite =~ s/_Buffer//;
    $tsite =~ s/_Disk//;
    push @tsites, $tsite unless grep(/$tsite/, @tsites);
    if (exists $outcross{$tsite}) {
	$outcross{$tsite} += $outcross{$site};
    } else {
	$outcross{$tsite} = $outcross{$site}; 
    }
    if (exists $incross{$tsite}) {
	$incross{$tsite} += $incross{$site};
    } else {
	$incross{$tsite} = $incross{$site}; 
    }
    if (exists $hup{$tsite}) {
	$hup{$tsite} += $hup{$site};
    } else {
	$hup{$tsite} = $hup{$site}; 
    }
    if (exists $hdown{$tsite}) {
	$hdown{$tsite} += $hdown{$site};
    } else {
	$hdown{$tsite} = $hdown{$site}; 
    }
    if (exists $ldown{$tsite}) {
	$ldown{$tsite} += $ldown{$site};
    } else {
	$ldown{$tsite} = $ldown{$site}; 
    }
    if (exists $t_outcross{$tsite}) {
	$t_outcross{$tsite} += $t_outcross{$site};
    } else {
	$t_outcross{$tsite} = $t_outcross{$site}; 
    }
    if (exists $t_incross{$tsite}) {
	$t_incross{$tsite} += $t_incross{$site};
    } else {
	$t_incross{$tsite} = $t_incross{$site}; 
    }
    if (exists $t_hup{$tsite}) {
	$t_hup{$tsite} += $t_hup{$site};
    } else {
	$t_hup{$tsite} = $t_hup{$site}; 
    }
    if (exists $t_hdown{$tsite}) {
	$t_hdown{$tsite} += $t_hdown{$site};
    } else {
	$t_hdown{$tsite} = $t_hdown{$site}; 
    }
    if (exists $t_ldown{$tsite}) {
	$t_ldown{$tsite} += $t_ldown{$site};
    } else {
	$t_ldown{$tsite} = $t_ldown{$site}; 
    }
}

# Generate input files for SSB
&generate_ssbfile("$ssbdir/links_quality_t1ft0.txt", 1, 1);
&generate_ssbfile("$ssbdir/links_quality_t1ft1.txt", 1, 3);
&generate_ssbfile("$ssbdir/links_quality_t1tt1.txt", 1, 2);
&generate_ssbfile("$ssbdir/links_quality_t1ft2.txt", 1, 5);
&generate_ssbfile("$ssbdir/links_quality_t1tt2.txt", 1, 4);
&generate_ssbfile("$ssbdir/links_quality_t2ft1.txt", 2, 3);
&generate_ssbfile("$ssbdir/links_quality_t2tt1.txt", 2, 2);
&generate_combined_metric("$ssbdir/links_quality.txt");

sub generate_combined_metric {
    my $filename = shift;
    open(SSB, ">$filename") or die "Cannot write SSB input file $filename\n";
    my @sites = sort keys %quality;
    push @sites, @tsites;
    foreach my $site ( sort @sites ) {
	my $t = substr($site, 1, 1);
	$t = 1 if ($t == 0);  # Treat T0_CH_CERN as a T1
	next if ( $site =~ /Buffer/ );
	next if ( $site =~ /Disk/ );
	next if ( $site =~ /Export/ );
	my $timestamp = &timestamp;
	my $url_report = 'https://dashb-ssb.cern.ch/dashboard/request.py/siteview#currentView=Good+links&highlight=true';
	my $color = 'red';
	my $value = 'ERROR';
	my @status = &site_status($site);
	if ($t == 1 &&
	    !($site =~ /_Disk$/ or $site =~ /_Buffer$/) &&
	    grep(/${site}_Buffer/, @sites) &&
	    grep(/${site}_Disk/, @sites)) {
	    my @status_disk = &site_status($site . "_Disk");
	    my @status_buffer = &site_status($site . "_Buffer");
	    $status[0] = $status_disk[0] && $status_buffer[0];
	}
	if ( $status[0] ) {
	    $color = 'green';
	    $value = 'OK';
	}
	printf SSB "%s\t%s\t%s\t%s\t%s\n", $timestamp, $site, $value, $color,
	$url_report;
    }
	close SSB;
}
    
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
    my @sites = sort keys %quality;
    push @sites, @tsites;
    foreach my $site ( sort @sites ) {
	my $t = substr($site, 1, 1);
	$t = 1 if ($t == 0); # Treat T0_CH_CERN as a T1
	next if ( $t != $tier );
	my $timestamp = &timestamp;
	my $goodlinks = ${$map[$index-1]}{$site};
	my $totlinks = ${"t_" . $map[$index-1]}{$site};
	my $color = 'red';
	my $url_report = &phedex_link($site, $index);
	my @status = &site_status($site);
	if ($t == 1 &&
	    !($site =~ /_Disk$/ or $site =~ /_Buffer$/) &&
	    grep(/${site}_Buffer/, @sites) &&
	    grep(/${site}_Disk/, @sites)) {
	    my @status_disk = &site_status($site . "_Disk");
	    my @status_buffer = &site_status($site . "_Buffer");
	    $status[$index] = $status_disk[$index] && $status_buffer[$index];
	}
	if ( $status[$index] ) {
	    $color = 'green';
	}
	printf SSBL "%s\t%s\t%s\t%s\t%s\n", $timestamp, $site,
	"$goodlinks/$totlinks", $color, $url_report;
    }
    close SSBL;
}

# Version using the new metrics (number of good links >= 50% of links)
sub site_status {
    my $site = shift;
    my @status = (0, 0, 0, 0, 0, 0);
    my $tier = substr($site, 1, 1);
    $tier = 1 if ($tier == 0);  # Apply T1 rules to T0_CH_CERN
    if ( $tier == 1 ) {
	$status[1] = ($ldown{$site} >= 0.5*$t_ldown{$site});
	$status[2] = ($outcross{$site} >= 0.5*$t_outcross{$site});
	$status[3] = ($incross{$site} >= 0.5*$t_incross{$site});
	$status[4] = ($hdown{$site} >= 0.5*$t_hdown{$site});
	$status[5] = ($hup{$site} >= 0.5*$t_hup{$site});
	$status[0] = $status[1] && $status[2] && $status[3] &&
	    $status[4] && $status[5];
    } elsif ( $tier == 2 ) {
	$status[2] = ($lup{$site} >= 0.5*$t_lup{$site});
	$status[3] = ($ldown{$site} >= 0.5*$t_ldown{$site});
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

sub datasvc_url {
    my $instance = shift;
    my $start = shift;
    my $end = shift;
    my $url = "https://cmsweb.cern.ch/phedex/datasvc/perl/$instance/TransferHistory?starttime=$start&endtime=$end&binwidth=86399";
    return $url;
}

sub get_quality {
    my $url = shift;
    my %quality = ();
    my $report = get($url) or die "Cannot retrieve PhEDEx statistics\n";
    my $VAR1;
    eval $report;
    my %phedexdata = %$VAR1;
    my @links = @{$phedexdata{'PHEDEX'}{'LINK'}};
    foreach my $link (@links) {
	my %linkdata = %$link;
	my $source = $linkdata{'FROM'};
	my $dest = $linkdata{'TO'};
	next if ( $source =~ /MSS/ || $dest =~ /MSS/ );
	next if ( $source =~ /^T3/ || $dest =~ /^T3/ );
	my $transfer = ${$linkdata{'TRANSFER'}}[0];
	my %transferdata = %$transfer;
	my $done = $transferdata{'DONE_FILES'};
	my $fail = $transferdata{'FAIL_FILES'};
	$quality{$source}{$dest} = [$done, $fail];
    }
    return %quality;
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
	    my $o1 = (defined ${$q1{$s}{$d}}[0])?${$q1{$s}{$d}}[0]:-1;
	    my $o2 = (defined ${$q2{$s}{$d}}[0])?${$q2{$s}{$d}}[0]:-1;
	    my $f1 = (defined ${$q1{$s}{$d}}[1])?${$q1{$s}{$d}}[1]:-1;
	    my $f2 = (defined ${$q2{$s}{$d}}[1])?${$q2{$s}{$d}}[1]:-1;
	    my $o;
	    my $f;
	    if ( $o1 < 0 ) {
		$o = $o2;
		$f = $f2;
	    } elsif ( $o2 < 0 ) {
		$o = $o1;
		$f = $f1;
	    } else {
		$o = $o1 + $o2;
		$f = $f1 + $f2;
	    }
	    $q{$s}{$d} = [$o, $f];
	}
    }
    return %q;
}
    
sub phedex_link {
    my $site = shift;
    my $type = shift;
    my $base_url = "https://cmsweb.cern.ch/phedex/graphs/quality_all?link=link&no_mss=true&to_node=__dest__&from_node=__src__&starttime=${start}&span=3600&endtime=${end}";
    my $tier = substr($site, 1, 1);
    $tier = 1 if ($tier == 0); # Treat T0_CH_CERN as a T1
    my $url = $base_url;
    if ( $tier == 1 ) {
	if ( $type == 1 ) {              # CERN -> site
	    $url =~ s/__src__/T0_CH_CERN/;
	    $url =~ s/__dest__/$site/;
	} elsif ( $type == 2 ) {         # site -> T1
	    $url =~ s/__src__/$site/;
	    $url =~ s/__dest__/T[01]/;
	    
	} elsif ( $type == 3 ) {         # T1 -> site
	    $url =~ s/__src__/T[01]/;
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
	    $url =~ s/__dest__/T[01]/;
	} elsif ( $type == 3 ) {         # T1 -> site
	    $url =~ s/__src__/T[01]/;
	    $url =~ s/__dest__/$site/;
	}
    }
    return $url;
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

sub comm_prod_links {
    my $instance = shift;
    my $url = "https://cmsweb.cern.ch/phedex/datasvc/perl/$instance/links";
    my $report = get($url) or die "Cannot retrieve link information\n";
    my $VAR1;
    eval $report;
    my %phedexdata = %$VAR1;
    my @links = @{$phedexdata{'PHEDEX'}{'LINK'}};
    foreach my $link (@links) {
	my %linkdata = %$link;
	my $source = $linkdata{'FROM'};
	my $dest = $linkdata{'TO'};
	my $status = $linkdata{'STATUS'};
	next if ( $source =~ /MSS/ || $dest =~ /MSS/ );
	next if ( $source =~ /^T3/ || $dest =~ /^T3/ );
	if ( $status eq 'ok' ) {
	    $commissioned{$source}{$dest} = 1;
	} else {
	    $commissioned{$source}{$dest} = 0;
	}
    }
    return %commissioned;
}
