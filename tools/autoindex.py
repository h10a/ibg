"""
Add Sphinx index entries to RST source.

TODO: scan directory tree, look for *.rst
TODO: add option to remove entries
"""

import os
import re
import sys

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser


# Configuration defaults.
defaults = {'comment': ".. Generated by autoindex",
            'mintext': '5000',
            'noindex': ''}

# Read config settings.
config = ConfigParser(defaults, allow_no_value=True)
config.optionxform = str

thisdir = os.path.dirname(__file__)
conffile = os.path.join(thisdir, "autoindex.cfg")
config.read(conffile)

# Extract keywords and role mappings.
def getmap(section):
    mapping = {}

    if config.has_section(section):
        for name in config.options(section):
            if name not in defaults:
                mapping[name] = config.get(section, name)

    return mapping

keywords = getmap('keywords')
rolemap = getmap('rolemap')

# Autoindex comment.
comment = config.get('DEFAULT', 'comment')

# Minimum amount of text twixt identical entries.
mintext = config.getint('DEFAULT', 'mintext')

# Don't add index entries after paragraphs matching this.
noindex = config.get('DEFAULT', 'noindex').strip().split("\n")

if noindex:
    noindex_patterns = "(%s)" % "|".join(noindex)
else:
    noindex_patterns = None

# Paragraph separator.
separator = "\n\n"


def main(args):
    # Parse command args.
    if len(args) == 2:
        infile = args[1]
        outfile = None
    elif len(args) == 3:
        infile, outfile = args[1:]
    else:
        sys.exit("Usage: %s INFILE [OUTFILE]" % args[0])

    ##dump_paragraphs(infile)

    # Do indexing.
    autoindex_file(infile, outfile)


def autoindex_file(infile, outfile=None):
    "Add index entries to a file."

    # Get original text.
    with open(infile) as fp:
        text = fp.read()

    # Index it.
    itext = autoindex_text(text)

    # Write output (but don't modify original if nothing changed).
    if outfile or itext != text:
        if outfile == '-':
            sys.stdout.write(itext)
        else:
            with open(outfile or infile, "wb") as fp:
                fp.write(itext)


def autoindex_text(text):
    "Add index entries to the given text."
    return separator.join(indexed_paragraphs(text))


def indexed_paragraphs(text):
    "Yield indexed paragraphs from the specified text."

    # Current text position.
    textpos = 0

    # Text position of last entries for each index word (to avoid too many
    # close together for the same entry).
    lastpos = {}

    def addindex(index, name, desc=None):
        if name not in lastpos or lastpos[name] + mintext < textpos:
            index.append((name, desc, textpos))
            lastpos[name] = textpos

    # Whether to add index entries.
    noindex = False

    for info in paragraph_info(text):
        # Update text count.
        para = info['text']
        textpos += len(para)

        # Initialise index (list of [name, desc, textpos]).
        index = []

        # Find index entries for roles.
        for match in re.finditer(r':(.+?):`(.+?)`', para):
            role, name = match.groups()
            if role in rolemap:
                addindex(index, name, rolemap[role])

        # Find index entries for keywords.
        paraline = para.replace("\n", " ")
        for word, desc in keywords.items():
            if re.search(r'\b' + word + r'\b', paraline):
                addindex(index, word, desc)

        # Yield index paragraph if required.
        if index and not noindex:
            indent = info['indent']
            lines = [indent + comment]
            lines.append(indent + ".. index::")

            for name, desc, pos in sorted(index):
                msg = "autoindex: " + name

                if desc:
                    text = "   pair: %s; %s" % (name, desc)
                    msg += " (" + desc + ")"
                else:
                    text = "   single: %s" % name

                lines.append(indent + text)
                sys.stderr.write("%s [%s]\n" % (msg, pos))

            yield "\n".join(lines)

        noindex = info['noindex']

        # Yield paragraph.
        yield para


def unindexed_paragraphs(text):
    "Yield paragraphs stripped of autoindex comments."

    for para in text.split(separator):
        if comment not in para:
            yield para


def paragraph_info(text):
    "Yield paragraph information from text."

    noindex = False
    noindex_level = None

    for para in unindexed_paragraphs(text):
        indent = re.match(r' *', para).group()
        level = len(indent)

        # Detect first entry in a list.  Should be at same indent level as
        # its text.
        match = re.match(r'\* ', para.lstrip())
        if match:
            level += len(match.group())

        if noindex_patterns:
            if not noindex and re.search(noindex_patterns, para, re.M):
                noindex_level = level
                noindex = True
            elif noindex_level is not None and level <= noindex_level:
                noindex_level = None
                noindex = False

        yield {'text': para,
               'noindex': noindex,
               'indent': indent,
               'level': level}


def dump_paragraphs(infile):
    print noindex_patterns

    with open(infile) as fp:
        text = fp.read()

    for info in paragraph_info(text):
        print info['level'], info['noindex'], info['text'].replace("\n", " ")


if __name__ == "__main__":
    main(sys.argv)
