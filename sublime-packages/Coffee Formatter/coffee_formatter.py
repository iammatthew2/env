import sublime
import sublime_plugin
import re
import sys
import os
from subprocess import call

directory = os.path.dirname(os.path.realpath(__file__))
libs_path = os.path.join(directory, "libs")
is_py2k = sys.version_info < (3, 0)

# Use the original script to format a piece of code


def format(code, opt):

    temp_coffee_path = os.path.join(directory, 'temp.coffee')

    with open(temp_coffee_path, 'w') as f:
        f.write(code)

    call(["node", os.path.join(directory, 'js', 'formatter.js'),
          temp_coffee_path])

    with open(os.path.join(directory, 'temp.coffee'), 'r') as f:
        return f.read()

# Python 2.x on Windows can't properly import from non-ASCII paths, so
# this code added the DOC 8.3 version of the lib folder to the path in
# case the user's username includes non-ASCII characters


def add_lib_path(lib_path):
    def _try_get_short_path(path):
        path = os.path.normpath(path)
        if is_py2k and os.name == 'nt' and isinstance(path, unicode):
            try:
                import locale
                path = path.encode(locale.getpreferredencoding())
            except:
                from ctypes import windll, create_unicode_buffer
                buf = create_unicode_buffer(512)
                if windll.kernel32.GetShortPathNameW(path, buf, len(buf)):
                    path = buf.value
        return path
    lib_path = _try_get_short_path(lib_path)
    if lib_path not in sys.path:
        sys.path.append(lib_path)

add_lib_path(libs_path)

import merge_utils

s = None


def plugin_loaded():
    global s
    s = sublime.load_settings("CoffeeFormatter.sublime-settings")

if is_py2k:
    plugin_loaded()


def is_coffee_buffer(view):
    fName = view.file_name()
    vSettings = view.settings()
    syntaxPath = vSettings.get('syntax')
    syntax = ""
    ext = ""

    if (fName is not None):  # file exists, pull syntax type from extension
        ext = os.path.splitext(fName)[1][1:]
    if (syntaxPath is not None):
        syntax = os.path.splitext(syntaxPath)[0].split('/')[-1].lower()

    return ext in ['coffee', 'litcoffee'] or\
        "coffeescript" in syntax or "coffeescript (literate)" in syntax


class PreSaveFormatListner(sublime_plugin.EventListener):

    """Event listener to run CoffeeFormat during the presave event"""

    def on_pre_save(self, view):
        if(s.get("format_on_save") is True and is_coffee_buffer(view)):
            view.run_command("coffee_format")


class CoffeeFormatCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        # settings = self.view.settings()

        opts = {}

        selection = self.view.sel()[0]
        formatSelection = False
        # formatting a selection/highlighted area
        if(len(selection) > 0):
            formatSelection = True

        if formatSelection:
            self.format_selection(edit, opts)
        else:
            self.format_whole_file(edit, opts)

    def format_selection(self, edit, opts):
        def get_line_indentation_pos(view, point):
            line_region = view.line(point)
            pos = line_region.a
            end = line_region.b
            while pos < end:
                ch = view.substr(pos)
                if ch != ' ' and ch != '\t':
                    break
                pos += 1
            return pos

        def get_indentation_count(view, start):
            indent_count = 0
            i = start - 1
            while i > 0:
                ch = view.substr(i)
                scope = view.scope_name(i)
                # Skip preprocessors, strings, characaters and comments
                if 'string.quoted' in scope or\
                        'comment' in scope or 'preprocessor' in scope:
                    extent = view.extract_scope(i)
                    i = extent.a - 1
                    continue
                else:
                    i -= 1

                if ch == '}':
                    indent_count -= 1
                elif ch == '{':
                    indent_count += 1
            return indent_count

        view = self.view
        regions = []
        for sel in view.sel():
            start = get_line_indentation_pos(view, min(sel.a, sel.b))
            region = sublime.Region(
                view.line(start).a,  # line start of first line
                view.line(max(sel.a, sel.b)).b)  # line end of last line
            indent_count = get_indentation_count(view, start)
            # Add braces for indentation hack
            code = '{' * indent_count
            if indent_count > 0:
                code += '\n'
            code += view.substr(region)
            # Performing astyle formatter
            formatted_code = format(code, opts)
            if indent_count > 0:
                for _ in range(indent_count):
                    index = formatted_code.find('{') + 1
                    formatted_code = formatted_code[index:]
                formatted_code = re.sub(r'[ \t]*\n([^\r\n])', r'\1',
                                        formatted_code, 1)
            else:
                # HACK: While no identation, a '{' will generate a blank line,
                # so strip it.
                search = "\n{"
                if search not in code:
                    formatted_code = formatted_code.replace(search, '{', 1)
            # Applying formatted code
            view.replace(edit, region, formatted_code)
            # Region for replaced code
            if sel.a <= sel.b:
                regions.append(sublime.Region(region.a, region.a + len(
                    formatted_code)))
            else:
                regions.append(sublime.Region(region.a + len(
                    formatted_code), region.a))
        view.sel().clear()
        # Add regions of formatted code
        [view.sel().add(region) for region in regions]

    def format_whole_file(self, edit, opts):
        view = self.view
        settings = view.settings()
        region = sublime.Region(0, view.size())
        code = view.substr(region)
        formatted_code = format(code, opts)

        if(settings.get("ensure_newline_at_eof_on_save") and
           not formatted_code.endswith("\n")):
            lineEnding = {
                'system': os.linesep,
                'windows': "\r\n",
                'unix': "\n"
            }[settings.get("default_line_ending")]
            formatted_code = formatted_code + lineEnding

        _, err = merge_utils.merge_code(view, edit, code, formatted_code)
        if err:
            sublime.error_message("CoffeeFormatter: Merge failure: '%s'" % err)

    def is_visible(self):
        return is_coffee_buffer(self.view)
