""" sgrep.py is a (semi-complete) Python implementation of the Unix command-line tool grep
but using Python 're' regular expressions.  It also supports the -s command, which filters
Subversion, CVS, and Mercurial subdirectories out of the search.

This software is licensed under the MIT license reprinted below:

The MIT License (MIT)

Copyright (c) 2008-2014 Scott Stafford

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

__version__ = 4.0

import re,sys,os,glob,fnmatch

debug = False

def isbinary(c): return ord(c)<10 or ord(c)>127

def main(args):
    from optparse import OptionParser, OptionGroup

    usage = """\
usage: %prog [options] PATTERN [FILE1] ..."""

    parser = OptionParser(usage=usage)
    group = OptionGroup(parser, "Regexp selection and interpretation")
    group.add_option("-e", "--regexp", metavar="PATTERN", help="use PATTERN for matching", action='store', type='string')
    group.add_option("-f", "--file", metavar="FILE", help="obtain PATTERN from FILE", action='store', type='string')
    group.add_option("-i", "--ignore-case", help="ignore case distinctions", action='store_true')
    group.add_option("-w", "--word-regexp", help="force PATTERN to match only whole words", action='store_true')
    group.add_option("-x", "--line-regexp", help="force PATTERN to match only whole lines", action='store_true')
    parser.add_option_group(group)
    
    group = OptionGroup(parser, "Miscellaneous")
    group.add_option("--no-messages", help="suppress error messages", action='store_true')
    group.add_option("-v", "--invert-match", help="select non-matching lines", action='store_true')
    group.add_option("-V", "--version", help="print version information and exit", action='store_true')
    group.add_option("--regexhelp", "--rh", help="print Python regular expression help", action='store_true')
    parser.add_option_group(group)
    
    group = OptionGroup(parser, "Output control")
    group.add_option("-m", "--max-count", metavar="NUM", help="stop after NUM matches", action='store', type='int')
    group.add_option("-n", "--line-number", help="emit line numbers", action='store_true')
    group.add_option("-H", "--with-filename", help="print the filename for each match", action='store_true')
    group.add_option("--no-filename", help="suppress the prefixing filename on output", action='store_true')
    group.add_option("--label", metavar="LABEL", help="print LABEL as filename for standard input", action='store', type='string',default='(standard input)')
    group.add_option("-o", "--only-matching", help="show only the part of a line matching PATTERN", action='store_true')
    group.add_option("-q", "--quiet", "--silent", help="suppress only normal output", action='store_true')
    group.add_option("--binary-files", metavar="TYPE", help="assume that binary files are TYPE. TYPE is `binary', `text', or `without-match'",
        action='store', type='choice', choices = [ "binary", "text", "without-match"], default="binary")
    group.add_option("-a", "--text", help="equivalent to --binary-files=text", action='store_true')
    group.add_option("-I", dest = 'ignore_binary_files', help="skip binary files", action='store_true')
    group.add_option("-d", "--directories", metavar = 'ACTION', help="how to handle directories; ACTION is `read', `recurse', or `skip'", 
        action='store', type='choice', choices = [ "read", "recurse", "skip"], default=None)
    group.add_option("-R", "-r", "--recursive", help="equivalent to --directories=recurse", action='store_true')
    group.add_option("--exclude", metavar='FILE_PATTERN', help="skip files and directories matching FILE_PATTERN", default=[], action='append', type='string')
    group.add_option("--exclude-dir", metavar="PATTERN", help="directories that match PATTERN will be skipped.", default=[], action='append', type='string')
    group.add_option("-s", "--novcs", help="equivalent to --exclude-dir for `CVS', `.hg', `.svn', `.git'", action='store_true')
    group.add_option("-l", "--files-with-matches",help="print only names of FILEs containing matches", action="store_true")
    group.add_option("-c", "--count", help="print only a count of matching lines per FILE", action='store_true')    
    parser.add_option_group(group)
    
    group = OptionGroup(parser, "Context control")
    group.add_option("-B", "--before-context", metavar="NUM", help="print NUM lines of leading context", action='store', type='int', default=0)
    group.add_option("-A", "--after-context", metavar="NUM", help="print NUM lines of trailing context", action='store', type='int', default=0)
    group.add_option("-C", "--context", metavar="NUM", help="print NUM lines of output context", action='store', type='int', default=0)
    
    (options, args) = parser.parse_args()
    
    if options.version:
        print """\
sgrep.py %(__version__)s

Copyright (C) 2008-2010 Scott Stafford
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
"""%globals()
        sys.exit(0)
    
    if options.regexhelp:
        print r"""\
This documentation is excerpted from the Python 2.6 re.__doc__ string:

Regular expressions can contain both special and ordinary characters.
Most ordinary characters, like "A", "a", or "0", are the simplest
regular expressions; they simply match themselves.  You can
concatenate ordinary characters, so last matches the string 'last'.

The special characters are:
    "."      Matches any character except a newline.
    "^"      Matches the start of the string.
    "$"      Matches the end of the string or just before the newline at
             the end of the string.
    "*"      Matches 0 or more (greedy) repetitions of the preceding RE.
             Greedy means that it will match as many repetitions as possible.
    "+"      Matches 1 or more (greedy) repetitions of the preceding RE.
    "?"      Matches 0 or 1 (greedy) of the preceding RE.
    *?,+?,?? Non-greedy versions of the previous three special characters.
    {m,n}    Matches from m to n repetitions of the preceding RE.
    {m,n}?   Non-greedy version of the above.
    "\\"     Either escapes special characters or signals a special sequence.
    []       Indicates a set of characters.
             A "^" as the first character indicates a complementing set.
    "|"      A|B, creates an RE that will match either A or B.
    (...)    Matches the RE inside the parentheses.
             The contents can be retrieved or matched later in the string.
    (?iLmsux) Set the I, L, M, S, U, or X flag for the RE (see below).
    (?:...)  Non-grouping version of regular parentheses.
    (?P<name>...) The substring matched by the group is accessible by name.
    (?P=name)     Matches the text matched earlier by the group named name.
    (?#...)  A comment; ignored.
    (?=...)  Matches if ... matches next, but doesn't consume the string.
    (?!...)  Matches if ... doesn't match next.
    (?<=...) Matches if preceded by ... (must be fixed length).
    (?<!...) Matches if not preceded by ... (must be fixed length).
    (?(id/name)yes|no) Matches yes pattern if the group with id/name matched,
                       the (optional) no pattern otherwise.

The special sequences consist of "\\" and a character from the list
below.  If the ordinary character is not on the list, then the
resulting RE will match the second character.
    \number  Matches the contents of the group of the same number.
    \A       Matches only at the start of the string.
    \Z       Matches only at the end of the string.
    \b       Matches the empty string, but only at the start or end of a word.
    \B       Matches the empty string, but not at the start or end of a word.
    \d       Matches any decimal digit; equivalent to the set [0-9].
    \D       Matches any non-digit character; equivalent to the set [^0-9].
    \s       Matches any whitespace character; equivalent to [ \t\n\r\f\v].
    \S       Matches any non-whitespace character; equiv. to [^ \t\n\r\f\v].
    \w       Matches any alphanumeric character; equivalent to [a-zA-Z0-9_].
             With LOCALE, it will match the set [0-9_] plus characters defined
             as letters for the current locale.
    \W       Matches the complement of \w.
    \\       Matches a literal backslash.
"""        
        sys.exit(0)


    if options.regexp:
        args = [options.regexp] + args        
    if options.file:
        args = [None] + args  # make sure I don't get confused and use this as a pattern
    if len(args) < 1:
        parser.error("Try `sgrep.py --help' for more information.")
        sys.exit(1)
        
    reflags = 0
    if options.ignore_case:
        reflags = reflags | re.IGNORECASE

    if options.ignore_binary_files:
        options.binary_files = 'without-match'
    if options.text:
        options.binary_files = 'text'

    if options.recursive:
        options.directories = 'recurse'

    if options.novcs:
        options.exclude_dir.extend(['.hg', '.svn', 'CVS', '.git'])

    BINARY_FILES_BINARY = 0
    BINARY_FILES_TEXT = 1
    BINARY_FILES_WITHOUT_MATCH = 2
    if options.binary_files == 'binary':
        options.binary_files = BINARY_FILES_BINARY
    elif options.binary_files == 'text':
        options.binary_files = BINARY_FILES_TEXT
    elif options.binary_files == 'without-match':
        options.binary_files = BINARY_FILES_WITHOUT_MATCH
    else:
        raise ValueError("???")

    if options.file:
        try:
            patternFile = open(options.file).readline().strip()
        except IOError, e:
            print "sgrep: %s: %s" % (options.file, "No such file or directory")
            sys.exit(2)
        pattern = re.compile(patternFile, reflags)
        uncompiledPattern = patternFile
    else:
        uncompiledPattern = args[0]
        
    if options.word_regexp:
        uncompiledPattern = r"\b%s\b"%(uncompiledPattern)
    if options.line_regexp:
        uncompiledPattern = r"^%s$"%(uncompiledPattern)
        
    pattern = re.compile(uncompiledPattern, reflags)
    read_from_stdin = False
    
    before_context = max((options.before_context, options.context))
    after_context = max((options.after_context, options.context))
        
    def warning(filename, exception):
        if not options.no_messages and not options.quiet:
            print "sgrep: %s: %s" % (filename, exception)

    if (len(args)>1):
        files = args[1:]

        paths = []
        dirs = []
        for file in files:
            things = glob.glob(file)
            #~ if len(things) == 0:
                #~ warning(file, "No such file or directory")
            for t in things:
                if os.path.isfile(t):
                    paths.append(t)
                else:
                    dirs.append(t)
                    
    elif len(args) == 1:
        # no files specified so get input from stdin
        read_from_stdin = True

    if options.directories == 'read':
        raise RuntimeError("what does read mean, anyway?")
        
    #~ if read_from_stdin:
        #~ show_filename = False
    if options.with_filename or options.directories:
        show_filename = True
    elif options.no_filename:
        show_filename = False
    else:
        if read_from_stdin:
            show_filename = False
        elif len(paths) > 1:
            show_filename = True
        else:
            show_filename = False

    def grep_one_file(path):
        if debug: print "[grep_one_file]" ,path
        
        file_is_binary = False
        if options.binary_files != BINARY_FILES_TEXT:
            try:
                binary_test = open(path,'rb').read(20) # read a few bytes and see if they're binary-ey
            except IOError, e:
                warning(path, e)
                return
            #~ print binary_test
            num_nonascii_chars = [isbinary(c) for c in binary_test].count(True)
            file_is_binary = num_nonascii_chars >= 5
            #~ print "    -- [debug] ",path,"nonascii",num_nonascii_chars,"isbinary=",file_is_binary
            if file_is_binary and options.binary_files == BINARY_FILES_WITHOUT_MATCH:
                #~ print "    -- [debug] skipping..."
                return

        if file_is_binary:
            f = open(path,'rb')
        else:
            f = open(path)
            
        grep_one_stream(f, path, file_is_binary)
        
    def grep_one_stream(f, path = '(unset)', file_is_binary = False):
        hit_count = 0
        lines_since_match = after_context + 1 # init to make sure it can't be hit
        from collections import deque
        rolling_line_cache = deque()
        
        def print_line(path, linenum, data, sep = ':'):
            items = []
            if show_filename:
                items.append(path)
            if options.line_number:
                items.append(str(linenum))
            items.append(data)
            
            if not options.quiet:
                print sep.join(items)
                        
        for i,line in enumerate(f):
            m = pattern.search(line)
            #~ print "   -- debug",i,m
            is_matching = (m is not None and not options.invert_match) or (m is None and options.invert_match)
            lines_since_match += 1
            if is_matching:
                lines_since_match = 0
                hit_count += 1

                if file_is_binary and options.binary_files == BINARY_FILES_BINARY:
                    print "Binary file %s matches" % path
                    return
                elif options.files_with_matches:
                    print path
                    return
                elif options.count:
                    pass
                else:
                    if options.only_matching:
                        if m is None:
                            continue
                        match_detail = m.group(0)
                    else:
                        match_detail = line.rstrip()

                    for j,oldline in enumerate(rolling_line_cache):
                        print_line(path, i+1+j-len(rolling_line_cache), oldline.rstrip(), "-")
                        
                    print_line(path, i+1, match_detail)
                    
                    rolling_line_cache.clear()
                    
                if hit_count == options.max_count:
                    break
            else:
                if before_context>0:
                    rolling_line_cache.append(line)
                    if len(rolling_line_cache)>before_context:
                        rolling_line_cache.popleft()
                    
                if lines_since_match <= after_context:
                    print_line(path, i+1, line.rstrip(), "-")
                    
        if options.count:
            items = []
            if show_filename and path:
                items.append(path)
            items.append(str(hit_count))
            
            if not options.quiet:
                print ":".join(items)

    def filter_and_grep(localfiles, root="./"):
        ## for each file pattern provided, compare vs. files in the directory and grep each matching file
        if debug: print "[filter_and_grep]", localfiles, root
        for file_pattern in files:
            base_file_pattern = os.path.basename(file_pattern)
            matchingfiles = fnmatch.filter(localfiles, base_file_pattern)
            # if debug: print "[filter_and_grep] filtered %d down to %d with %s"%(len(localfiles), len(matchingfiles), base_file_pattern)
            for exclude_pattern in options.exclude:
                matchingfiles = [n for n in matchingfiles if not fnmatch.fnmatch(n, exclude_pattern)]
            for p in matchingfiles:
                grep_one_file(os.path.join(root,p))

    if read_from_stdin:
        grep_one_stream(sys.__stdin__, options.label)
    else:
        if options.directories == 'recurse':
            dir_to_start = os.path.dirname(files[0])
            if dir_to_start=='': dir_to_start = '.'
            if debug: print "[main] dir_to_start",dir_to_start
            for root, dirs, localfiles in os.walk(dir_to_start):
                ## remove any --exclude-dirs from walk recursion
                i = 0
                if len(options.exclude_dir) > 0:
                    while i < len(dirs):
                        for dir_to_exclude in options.exclude_dir:
                            if fnmatch.fnmatch(dirs[i], dir_to_exclude):
                                if debug: print "[main] excluded dir", dirs[i]
                                del dirs[i]
                                break
                        i += 1
                        
                filter_and_grep(localfiles, root)
        else:
            localfiles = (x for x in os.listdir('.') if os.path.isfile(x))
            filter_and_grep(localfiles)

if __name__=='__main__':
    main(sys.argv[1:])
