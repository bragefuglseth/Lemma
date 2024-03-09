#!/usr/bin/env python3
# coding: utf-8

# Copyright (C) 2017-present Robert Griesel
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>

from lemma.helpers.observable import Observable


class MarkdownScanner(Observable):

    def __init__(self, document):
        Observable.__init__(self)
        self.document = document

        self.markdown = ''

    def update(self):
        self.markdown = '# ' + self.document.title + '\n'
        self.document.lines.accept(self)
        self.markdown = self.markdown[:-1] # remove last EOL
        self.document.markdown = self.markdown

    def visit_root(self, root):
        for line in root.children:
            line.accept(self)

    def visit_line(self, line):
        for char in line.children:
            char.accept(self)

    def visit_mathlist(self, mathlist):
        self.markdown += '$`'
        for symbol in mathlist.children:
            symbol.accept(self)
        self.markdown += '`$'

    def visit_char(self, char):
        self.markdown += char.content

    def visit_math_symbol(self, symbol):
        self.markdown += '\\' + symbol.name

    def visit_eol(self, node):
        self.markdown += '\n'

    def visit_eoml(self, node):
        pass


