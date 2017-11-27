#!/usr/bin/perl -w

# the script can run with or without an evaluation list
# if it's run with an evaluation list, an evaluation subset will be created using that list
# otherwise, the original submission - if it passes validation - is used for evaluation

if (! ($ARGV[0] || $ARGV[1])) {
    print "Usage: $0 system_submission\n";
    print "Or:\n";
    print "Usage: $0 system_submission eval_filelist\n";
    exit (1);
} elsif ( $ARGV[0] !~ /\.tab$/) {
    print "Incorrect submission file extension - please make sure it is \*.tab\n";
    exit (1);
}

$submission = $ARGV[0];

#$total_errs = 0;

# this 2017 version checks for nested mentions. Since there's no guarantee that
# the system output is perfectly ordered, we need to reorder the returns while
# performing other checks first

open (SYSIN, "<:utf8", $submission) || die "Cannot open $submission";

@sysdoclist = ();
%sysdoclistmentions = ();

%check_duplicate_lines = ();
%check_duplicate_mention_ids = ();

$ln = 0;

$blank_line = 0;
$duplicate_line = 0;
$incorrect_field_number = 0;
$missing_sys_id = 0;
$inconsistent_sys_id = 0;
$missing_mention_id = 0;
$missing_mention_string = 0;
$missing_entity_id = 0;
$missing_entity_type = 0;
$unsupported_entity_type = 0;
$missing_mention_type = 0;
$unsupported_mention_type = 0;
$missing_confidence = 0;
$incorrect_confidence = 0;

$missing_mention_span = 0;
$missing_colon = 0;
$missing_doc_id = 0;
$invalid_offset_format = 0;

$old_sys_id = "1";
$duplicate_mention_id = 0;

%mention_by_line = ();


while (my $line = <SYSIN>) {
    chomp ($line);
    $ln++;

    my $valid = 1;
    
    $mention_by_line{$ln} = $line;
    
    my $line_errs = 0;

    #blank lines will be tolerated
    if ($line =~ /^\s*$/) {
	print "Blank line at line $ln\n";
	$blank_line++;
	next;
    }


    if ($check_duplicate_lines{$line}) {
	print "Line $ln: duplicate line found at $check_duplicate_lines{$line}; current line not checked further\n";
	$duplicate_line++;
	next;
    } else {
	$check_duplicate_lines{$line} = $ln;
    }

    
    my @fields = split ('\t', $line);
    my $number_of_fields = $#fields + 1;
    if ($number_of_fields != 8) {
	print "Line $ln: number of fields is $number_of_fields instead of 8\n";
	$incorrect_field_number++;
	next;        #if the number of fields is wrong, no futher checking for this line
    }

    my ($sys_id, $mention_id, $mention_string, $mention_span, $entity_id, $entity_type, $mention_type, $confidence) = split ('\t', $line);


    #system id problems reported but ignored in validation
    if ($sys_id =~ /^\s*$/) {
	$missing_sys_id++;
	print "Line $ln: missing system id found\n";
    } elsif ($old_sys_id eq "1") {
	$old_sys_id = $sys_id;   #take the first non-missing system id identified
    } elsif ($sys_id ne $old_sys_id) {
	$old_sys_id = $sys_id;
	$inconsistent_sys_id++;
	print "Line $ln: inconsistent system id found\n";
    }
    
    #mention id's should be unique
    if ($mention_id =~ /^\s*$/) {
	$missing_mention_id++;
	print "Line $ln: missing mention id found\n";
    } elsif ($check_duplicate_mention_ids{$mention_id}) {
	$duplicate_mention_id++;
	print "Line $ln: duplicate mention id found at line $check_duplicate_mention_ids{$mention_id}\n";
	print "  L$ln:\t$line\n";
	print "  L$check_duplicate_mention_ids{$mention_id}:\t$mention_by_line{$check_duplicate_mention_ids{$mention_id}}\n";
    } else {
	$check_duplicate_mention_ids{$mention_id} = $ln;
    }

    #mention string
    if ($mention_string =~ /^\s*$/) {
	$missing_mention_string++;
	print "Line $ln: missing mention string found\n";
    }


    #entity id is essential for linking task and cannot be ignored
    if ($entity_id =~ /^\s*$/) {
	$missing_entity_id++;
	print "Line $ln: missing entity id found\n";
#	next;
    }

    #entity type - errors not tolerated
    if ($entity_type =~ /^\s*$/) {
	$missing_entity_type++;
	print "Line $ln: missing entity type found\n";
    } elsif (!($entity_type eq "GPE" || $entity_type eq "LOC" || $entity_type eq "ORG" || $entity_type eq "PER")) {
	$unsupported_entity_type++;
	print "Line $ln: $entity_type is an unsupported entity type\n";
    }

   #mention type - errors can be tolerated
    if ($mention_type =~ /^\s*$/) {
	$missing_mention_type++;
	print "Line $ln: missing mention type found\n";
    } elsif ($mention_type ne "NAM") {
	$unsupported_mention_type++;
	print "Line $ln: $mention_type is a unsupported mention type\n";
    }

    #confidence value should be between 0 and 1

    if ($confidence =~ /^\s*$/) {
	$missing_confidence++;
	print "Line $ln: missing confidence value found\n";
    } elsif ($confidence !~ /^[.0-9]+$/) {
	$incorrect_confidence++;
	print "Line $ln - incorrect confidence value: $confidence\n";
    } elsif  ( ! ($confidence >= 0 && $confidence <=1)) {
	$incorrect_confidence++;
	print "Line $ln - incorrect confidence value: $confidence\n";
    }

    if ($mention_span =~ /^\s*$/) {
	$missing_mention_span++;
	print "Line $ln: missing mention span field found\n";
	next;    #no further checking if mention span field is missing
    }

    
    if ($mention_span !~ /\:/) {
	$missing_colon++;
	print "Line $ln: mention span field missing colon delimiter\n";
	next;        #no further checking if mention span field does not have a colon delimiter
    }

    my ($doc_id, $span) = split (':', $mention_span);

    if ($doc_id =~ /^\s*$/) {
	$missing_doc_id++;
	print "Line $ln: missing document id found\n";
	next;       #no further checking if there's no doc id
    }

    if ($span !~ /^\d+\-\d+$/) {
	print "Line $ln - invalid offset format: $span\n";
	$invalid_offset_format++;
	next;       #if the span of offset is not in the correct format of digits-digits, no futher checking for this line
    }

    #preparing for checking nested mentions

    $line = "$line" ."\t". "$ln";   #store original line number
    
    if (! $sysdoclistmentions{$doc_id}) {
	$sysdoclistmentions{$doc_id} = $line;
	push @sysdoclist, $doc_id;
    } else {        #use a character unlikely seen in any documents
	$sysdoclistmentions{$doc_id} = "$sysdoclistmentions{$doc_id}" . "\x{0080}". "$line";
    }
    
}

close (SYSIN);

#checking for nested mentions

$nested_mention = 0;
$interleaved_mention = 0;

foreach my $doc_id (@sysdoclist) {

    # if the document has only one mention, skip checking
    if ($sysdoclistmentions{$doc_id} !~ /\x{0080}/) {
	next;
    }

    my @mentions = split ('\x{0080}', $sysdoclistmentions{$doc_id});

    for ($i = 0; $i < $#mentions; $i++) {
	my $mention_i = $mentions[$i];
	my ($team_i, $mID_i, $m_i, $mspan_i, $kbID_i, $cat_i, $type_i, $conf_i, $ln_i) = split ('\t', $mention_i);
	my ($sysDocID_i, $span_i) = split ('\:', $mspan_i);
	my ($beg_i, $end_i) = split ('-', $span_i);
	
	for ($j = $i+1; $j <= $#mentions; $j++) {
	    my $mention_j = $mentions[$j];
	    my ($team_j, $mID_j, $m_j, $mspan_j, $kbID_j, $cat_j, $type_j, $conf_j, $ln_j) = split ('\t', $mention_j);
	    my ($sysDocID_j, $span_j) = split ('\:', $mspan_j);
	    my ($beg_j, $end_j) = split ('-', $span_j);

	    if ($beg_i == $beg_j && $end_i == $end_j) {
		if ($team_i ne $team_j) {
		    print "Lines $ln_i and $ln_j: same mentions with different team id\'s\n";
		} 
		if ($mID_i ne $mID_j) {
		    print "Lines $ln_i and $ln_j: same mentions with different mention id\'s\n";
		}
		if ($kbID_i ne $kbID_j) {          # this may be allowed in the future
		    print "Lines $ln_i and $ln_j: same mentions with different linkings\n";
		} 
		if ($cat_i ne $cat_j) {
		    print "Lines $ln_i and $ln_j: same mentions with different entity types\n";
		} 
		if ($type_i ne $type_j) {
		    print "Lines $ln_i and $ln_j: same mentions with different mention types\n";
		} 
		if ($conf_i ne $conf_j) {
		    print "Lines $ln_i and $ln_j: same mentions with different confidence scores\n";
		}

		print "  Line $ln_i:\t$team_i\t$mID_i\t$m_i\t$mspan_i\t$kbID_i\t$cat_i\t$type_i\t$conf_i\n";
		print "  Line_$ln_j:\t$team_j\t$mID_j\t$m_j\t$mspan_j\t$kbID_j\t$cat_j\t$type_j\t$conf_j\n";
		next;
	    }

	    if ($beg_j >= $beg_i && $end_j <= $end_i) {
		$nested_mention++;
		print "Mention at $ln_j is embedded in mention at $ln_i\n";
		print "  Line $ln_i:\t$team_i\t$mID_i\t$m_i\t$mspan_i\t$kbID_i\t$cat_i\t$type_i\t$conf_i\n";
		print "  Line_$ln_j:\t$team_j\t$mID_j\t$m_j\t$mspan_j\t$kbID_j\t$cat_j\t$type_j\t$conf_j\n";
		next;
	    }

	    if ($beg_i >= $beg_j && $end_i <= $end_j) {
		$nested_mention++;
		print "Mention at $ln_i is embedded in mention at $ln_j\n";
		print "  Line $ln_i:\t$team_i\t$mID_i\t$m_i\t$mspan_i\t$kbID_i\t$cat_i\t$type_i\t$conf_i\n";
		print "  Line_$ln_j:\t$team_j\t$mID_j\t$m_j\t$mspan_j\t$kbID_j\t$cat_j\t$type_j\t$conf_j\n";
		next;
	    }


	    if (($beg_j > $beg_i && $beg_j <= $end_i) && ($end_j > $end_i) || 
		($beg_i > $beg_j && $beg_i <= $end_j) && ($end_i > $end_j)) {
		$interleaved_mention++;
		print "Mentions at $ln_i and $ln_j are interleaved\n";
		print "  Line $ln_i:\t$team_i\t$mID_i\t$m_i\t$mspan_i\t$kbID_i\t$cat_i\t$type_i\t$conf_i\n";
		print "  Line_$ln_j:\t$team_j\t$mID_j\t$m_j\t$mspan_j\t$kbID_j\t$cat_j\t$type_j\t$conf_j\n";
		next;
	    }
	    
	}
	
    }
    
}


if ($blank_line > 0) {
    print "There are $blank_line blank line(s) (tolerated).\n";
}

if ($duplicate_line > 0) {
    print "There are $duplicate_line duplicate line(s).\n";
}

if ($incorrect_field_number > 0) {
    print "There are $incorrect_field_number line(s) with an incorrect number of fields.\n";
}

if ($missing_sys_id > 0) {
    print "There are $missing_sys_id line(s) with a missing systerm id (tolerated).\n";
}

if ($inconsistent_sys_id > 0) {
    print "There are $inconsistent_sys_id line(s) with an inconsistent systerm id (tolerated).\n";
}

if ($missing_mention_id > 0) {
    print "There are $missing_mention_id line(s) with a missing mention id.\n";
}

if ($duplicate_mention_id > 0) {
    print "There are $duplicate_mention_id non-dupilcate line(s) with a duplicate mention id.\n";
}

if ($missing_mention_string > 0) {
    print "There are $missing_mention_string line(s) with a missing mentions string.\n";
}

if ($missing_entity_id > 0) {
    print "There are $missing_entity_id line(s) with a missing entity id.\n";
}

if ($missing_entity_type > 0) {
    print "There are $missing_entity_type line(s) with a missing entity type.\n";
}

if ($unsupported_entity_type > 0) {
    print "There are $unsupported_entity_type line(s) with an unsupported entity type.\n";
}

if ($missing_mention_type > 0) {
    print "There are $missing_mention_type line(s) with a missing mention type.\n";
}

if ($unsupported_mention_type > 0) {
    print "There are $unsupported_mention_type line(s) with an unsupported mention type.\n";
}   

if ($missing_confidence > 0) {
    print "There are $missing_confidence line(s) with a missing confidence value.\n";
}		
	
if ($incorrect_confidence > 0) {
    print "There are $incorrect_confidence line(s) with an incorrect confidence value.\n";
}

if ($missing_mention_span > 0) {
    print "There are $missing_mention_span line(s) with a missing mention span field.\n";
}

if ($missing_doc_id > 0) {
    print "There are $missing_doc_id line(s) with a missing doc id.\n";
}

if ($missing_colon > 0) {
    print "There are $missing_colon line(s) missing the colon that separates doc id from mention offsets.\n";
}		

if ($invalid_offset_format > 0) {
    print "There are $invalid_offset_format line(s) with an invalid offset format.\n";
}

if ($nested_mention > 0) {
    print "There are $nested_mention nested mention(s).\n";
}

if ($interleaved_mention > 0) {
    print "There are $interleaved_mention interleaved mention(s).\n";
}


if ($incorrect_field_number > 0 || 
    $missing_mention_id > 0 || 
    $missing_mention_string > 0 ||
    $missing_entity_id > 0 || 
    $missing_mention_span > 0 ||
    $missing_doc_id > 0 || 
    $missing_colon > 0 ||
    $invalid_offset_format > 0 || 
    $nested_mention > 0 || 
    $interleaved_mention > 0)  {
    print "Validation failed!\n";
    exit(1);
}




if ($ARGV[1]) {
    $evallist = $ARGV[1];
    open (GL, "<$evallist") || die "Validation passed but cannot open $evallist";

    %goldevallist = ();
    while (my $line = <GL>) {
	chomp $line;
	$goldevallist{$line} = 1;
    }

    # adding _eval to system submission file for new eval input file
    ($systemeval = $submission) =~ s/\.tab/\_eval\.tab/;

    open (SYSEVAL, ">:utf8", $systemeval) || die "Validation passed but cannot open $systemeval";
    open (SYSIN, "<:utf8", $submission);

    $sys_mention_count = 0;
    
    while (my $line = <SYSIN>) {
	chomp ($line);
	my ($sys_id, $mention_id, $mention_string, $mention_span, $entity_id, $entity_type, $mention_type, $confidence) = split ('\t', $line);
	my ($doc_id, $span) = split (':', $mention_span);
	if ($goldevallist{$doc_id}) {
	    print SYSEVAL "$line\n";
	    $sys_mention_count++;
	}
    }

    if ($sys_mention_count == 0) {
	print "Validation passed, but there's a problem matching the doc id\'s with the eval set. Pleasae check your submission.\n";
	exit(1);
    }

    print "Validation passed. An eval set has been extratced from your submission for scoring.\n";
    exit (0);

} else {
    print "Validation passed.\n";
}

exit(0);
