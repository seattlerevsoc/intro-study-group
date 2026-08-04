# Intro Study Group Materials

This repository has our organization's introductory study group materials copied
into a single convenient location, compiled into both pdf and epub formats.

The articles are generated based on the .rst files (ReStructured Text). In
short, the reason for this is because it is a relatively simple language which
can be used to generate both LaTeX (which becomes the pdf) and XHTML (which
becomes the epub). As a result, all content edits should be made in the .rst
files, not the .tex or .xhtml files. The process for generating these files is
not simple enough that a non-computer toucher can understand it, unfortunately.
And that is not likely to change any time soon, unless we'd like to throw
substantially more time and money at this than we have had so far. 

## For computer touchers who want to run this on their own machine...

Generating these files on your own computer requires a Linux or Mac machine, or
that you are willing to deal with Cygwin if you're on Windows. No, there is no
simpler way to accomplish this at the moment; in the future we could move the
generation onto remote machines to avoid the hassle for the convenience of less
technical people, but until then, there just is no way around dealing with some
relatively complicated tools. In addition, you need to have `make`, `python`,
and `latexmk` to be able to generate these files on your own machine. The python
packages which do the magic of the generation are handled by `uv` and a nice
virtual environment.

An actual tutorial on how to set this repository up will be available if
requested by enough people. Until then, you'll have to deal with trial and
error, and the typical "well, it works on my machine!" dynamic.

