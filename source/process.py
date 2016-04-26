#
# This script generates the patterns used in lua-wow.cson
#
# Copy the relevate bits from the following sites into the specified file then
# run the script! `python process.py > chunks.cson`
#
#   http://wow.gamepedia.com/Global_functions   -> raw_api
#   http://wow.gamepedia.com/Events             -> raw_events
#   http://wowprogramming.com/docs/widgets      -> raw_widgets
#
# Could probably automate downloading the content, but meh
#

from __future__ import with_statement
import re
import sys


class Parser(object):
    def __init__(self, filename):
        self.filename = filename

    @property
    def raw_data(self):
        with open(self.filename) as fp:
            return fp.readlines()


class APIParser(Parser):
    re_header = re.compile(ur"^((.+) Functions)", re.I)
    re_line = re.compile(ur"^(\w+\.?\w+)$", re.I)
    re_split_c = re.compile(ur"^(.+)\.(.+)$", re.I)

    # not raw because the brackets at the end break syntax hightlighting >.>
    chunk_pattern = """  {
    'match': '(?<![^.]\\\\.|:)\\\\b(%s)\\\\b(?=\\\\s*(?:[({"\\\']|\\\\[\\\\[))'
    'name': 'support.function.wow.%s'
  }"""

    @property
    def data(self):
        raw = self.raw_data
        cleaned = []
        whitelist = [
            # add the c-side lua functions
            'debugbreak', 'debugdump', 'debuginfo', 'debugload', 'debuglocals', 'debugprint',
            'debugprofilestart', 'debugprofilestop', 'debugstack', 'debugtimestamp',
            'hooksecure', 'issecure', 'issecurevariable', 'forceinsecure', 'securecall',
            'getprinthandler', 'print', 'setprinthandler', 'tostringall'
        ]
        lua = [
            # some hardcoded non-standard std functions
            'Lua Functions',
            'fastrandom',  # old math.random, which has been replaced by securerandom
            'fmod', 'mod',  # math.mod renamed math.fmod, with math.mod == %
            # trig functions that operate in degrees (math lib uses radians)
            'acos', 'asin', 'atan', 'atan2', 'cos', 'rad', 'sin', 'tan'
            # string lib references and utf8 stuff
            'strbyte', 'strchar', 'strcmputf8i', 'strconcat', 'strfind', 'strjoin', 'strlen',
            'strlenutf8', 'strlower', 'strmatch', 'strrep', 'strrev', 'strsplit', 'strsub',
            'strtrim', 'strupper',
            # table.wipe, how does lua not have this by default D;
            'table.wipe', 'wipe'
        ]
        tables = {}
        last_table = None

        for line in raw:
            line = line.strip()

            if line:
                header = self.re_header.match(line)
                if header:
                    if last_table is not None:
                        cleaned.append(ur'%s\\.(%s)' % (last_table, u'|'.join(tables[last_table])))
                        last_table = None

                    cleaned.append(header.groups()[0])
                    continue

                if self.re_line.match(line):
                    # quick builtin test
                    if line == line.lower() and line not in whitelist:
                        continue

                    # handle the C_ tables like language-lua handles std libs
                    if '.' in line:
                        table, func = self.re_split_c.match(line).groups()
                        if table not in tables:
                            if last_table is not None:
                                cleaned.append(ur'%s\\.(%s)' % (last_table, u'|'.join(tables[last_table])))

                            tables[table] = []
                            last_table = table

                        tables[table].append(func)
                    else:
                        if last_table is not None:
                            cleaned.append(ur'%s\\.(%s)' % (last_table, u'|'.join(tables[last_table])))
                            last_table = None

                        cleaned.append(line)

        for line in lua:
            cleaned.append(line)

        return cleaned

    def process(self):
        date = None
        try:
            data = self.data
        except IOError, message:
            print >> sys.stderr, message
            return

        chunks = {}

        header, chunk = None, None

        for line in data:
            header_check = self.re_header.match(line)
            if header_check:
                # put up the last header
                if header:
                    chunks[header] = chunk

                header = header_check.groups()[1].lower()
                chunk = []
                continue

            chunk.append(line)

        chunks[header] = chunk

        for header, chunk in chunks.iteritems():
            print self.chunk_pattern % (u'|'.join(chunk), header)


class EventParser(Parser):
    re_strip_desc = re.compile(ur'^([A-Z]+_[A-Z_]+)\s.+')
    chunk_pattern = r"""  {
    'match': '(\'|")(%s)\\1'
    'name': 'constant.wow.event'
  }"""

    @property
    def data(self):
        raw = self.raw_data
        cleaned = []

        for line in raw:
            line = line.strip()
            if not line or line.startswith('REMOVED '):
                continue

            match = self.re_strip_desc.match(line)
            if match:
                cleaned.append(match.groups()[0])

        return cleaned

    def process(self):
        data = None
        try:
            data = self.data
        except IOError, message:
            print >> sys.stderr, message
            return

        print self.chunk_pattern % u'|'.join(data)


class WidgetParser(Parser):
    re_strip_forward = re.compile(ur"[^=]+= (\w+:\w+\().+")
    re_strip_desc = re.compile(ur"^([^\ ]+) ", re.I)
    re_parse = re.compile(ur"([^:]+):([^\(]+)", re.I)

    chunk_pattern = r"""  {
    'match': '(?<=[.:])\\s*\\b(%s)\\b(?=[( {])'
    'name': 'support.function.wow.widget.%s'
  }"""

    chunk_list = set([
        'ArchaeologyDigSiteFrame',
        'Alpha',
        'Animation',
        'AnimationGroup',
        'Button',
        'Browser',
        'CheckButton',
        'ColorSelect',
        'ControlPoint',
        'Cooldown',
        'DressUpModel',
        'EditBox',
        'Font',
        'FontInstance',
        'FontString',
        'Frame',
        'GameTooltip',
        'LayeredRegion',
        'MessageFrame',
        'Minimap',
        'MovieFrame',
        'ParentedObject',
        'Path',
        'PlayerModel',
        'QuestPOIFrame',
        'Region',
        'Rotation',
        'Scale',
        'ScenarioPOIFrame',
        'ScriptObject',
        'ScrollFrame',
        'ScrollingMessageFrame',
        'SimpleHTML',
        'Slider',
        'StatusBar',
        'TabardModel',
        'Texture',
        'Translation',
        'UIObject',
        'VisibleRegion'
    ])

    hierarchy = {
        # noqa
        'process_order': ['PlayerModel', 'Button', 'Frame', 'LayeredRegion', 'VisibleRegion', 'Region', 'Animation', 'ParentedObject', 'FontInstance', 'UIObject', 'ScriptObject'],

        'ScriptObject': ['Frame', 'Animation', 'AnimationGroup'],
        'UIObject': ['ParentedObject', 'FontInstance'],
            'FontInstance': ['FontString', 'Font', 'EditBox', 'MessageFrame', 'ScrollingMessageFrame'],
            'ParentedObject': ['Region', 'ControlPoint', 'AnimationGroup', 'Animation'],
                'Animation': ['Alpha', 'Path', 'Rotation', 'Scale', 'Translation'],
                'Region': ['VisibleRegion'],
                    'VisibleRegion': ['LayeredRegion', 'Frame'],
                        'LayeredRegion': ['Texture', 'FontString'],
                        'Frame': ['ArchaeologyDigSiteFrame', 'Browser', 'Button', 'ColorSelect', 'Cooldown', 'GameTooltip', 'Minimap', 'MovieFrame', 'PlayerModel', 'QuestPOIFrame', 'ScenarioPOIFrame', 'ScrollFrame', 'SimpleHTML', 'Slider', 'StatusBar', 'EditBox', 'MessageFrame', 'ScrollingMessageFrame'],
                            'Button': ['CheckButton'],
                            'PlayerModel': ['TabardModel', 'DressUpModel'],
    }

    @property
    def data(self):
        raw = self.raw_data
        cleaned = []

        for line in raw:
            line = line.strip()

            if not line:
                continue

            match = None
            if u"=" in line:
                match = self.re_strip_forward.match(line)

            if not match:
                match = self.re_strip_desc.match(line)

            if match:
                cleaned.append(match.groups()[0])

        return cleaned

    def clean_chunks(self):
        chunk_sets = dict((header, set(funcs)) for header, funcs in self.chunks.items())
        new_chunks = dict((header, set(funcs)) for header, funcs in self.chunks.items())

        # self.hierarchy['process_order'].reverse()
        for header in self.hierarchy['process_order']:
            children = self.hierarchy[header]

            # get common funcs
            common = chunk_sets[header].copy()
            for child in children:
                common.intersection_update(chunk_sets[child])

            for child in children:
                new_chunks[child].difference_update(common)

            diff = common == chunk_sets[header]

            if not diff:
                print >> sys.stderr, 'fuck'
                print >> sys.stderr, header, chunk_sets[header].difference(common)

        self.chunks = new_chunks

    def process(self):
        data = None
        try:
            data = self.data
        except IOError, message:
            print >> sys.stderr, message
            return

        chunks = {}
        for line in data:
            if line.strip() in self.chunk_list:
                continue

            match = self.re_parse.match(line.strip())

            if not match:
                print >> sys.stderr, "Line not matched: %s" % line
                continue

            header, func = match.groups()

            if header not in self.chunk_list:
                print >> sys.stderr, "Header not found: %s" % header

            if header not in chunks:
                chunks[header] = []

            chunks[header].append(func)

        self.chunks = chunks
        self.clean_chunks()

        for header, chunk in self.chunks.iteritems():
            print self.chunk_pattern % (u'|'.join(chunk), header)


if __name__ == '__main__':
    APIParser('raw_api').process()
    WidgetParser('raw_widget').process()
    EventParser('raw_events').process()
