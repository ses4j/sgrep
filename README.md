sgrep
=====

Grep-clone written in Python and using Python regular expressions.

```
Usage: sgrep.py [options] PATTERN [FILE1] ...

Options:
  -h, --help            show this help message and exit

  Regexp selection and interpretation:
    -e PATTERN, --regexp=PATTERN
                        use PATTERN for matching
    -f FILE, --file=FILE
                        obtain PATTERN from FILE
    -i, --ignore-case   ignore case distinctions
    -w, --word-regexp   force PATTERN to match only whole words
    -x, --line-regexp   force PATTERN to match only whole lines

  Miscellaneous:
    --no-messages       suppress error messages
    -v, --invert-match  select non-matching lines
    -V, --version       print version information and exit
    --regexhelp, --rh   print Python regular expression help

  Output control:
    -m NUM, --max-count=NUM
                        stop after NUM matches
    -n, --line-number   emit line numbers
    -H, --with-filename
                        print the filename for each match
    --no-filename       suppress the prefixing filename on output
    --label=LABEL       print LABEL as filename for standard input
    -o, --only-matching
                        show only the part of a line matching PATTERN
    -q, --quiet, --silent
                        suppress only normal output
    --binary-files=TYPE
                        assume that binary files are TYPE. TYPE is `binary',
                        `text', or `without-match'
    -a, --text          equivalent to --binary-files=text
    -I                  skip binary files
    -d ACTION, --directories=ACTION
                        how to handle directories; ACTION is `read',
                        `recurse', or `skip'
    -R, -r, --recursive
                        equivalent to --directories=recurse
    --exclude=FILE_PATTERN
                        skip files and directories matching FILE_PATTERN
    --exclude-dir=PATTERN
                        directories that match PATTERN will be skipped.
    -s, --novcs         equivalent to --exclude-dir for `CVS', `.hg', `.svn',
                        `.git'
    -l, --files-with-matches
                        print only names of FILEs containing matches
    -c, --count         print only a count of matching lines per FILE
```