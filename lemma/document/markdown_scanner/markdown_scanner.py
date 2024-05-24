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


class MarkdownScanner(object):

    def __init__(self, document):
        self.document = document

        self.markdown = ''
        self.current_tags = set()
        self.current_link = None

    def update(self):
        self.markdown = '# ' + self.document.title + '\n'

        self.current_tags = set()
        self.current_link = None

        for child in self.document.ast.root:
            self.process_node(child)
        self.close_current_tags()

        self.markdown = self.markdown[:-1] # remove last EOL
        self.document.markdown = self.markdown

    def process_node(self, node):
        if node.link != self.current_link:
            if self.current_link != None:
                self.close_current_link()

        if node.tags != self.current_tags:
            self.close_current_tags()
            self.current_tags = node.tags
            self.open_current_tags()

        if node.link != self.current_link:
            if node.link != None:
                self.open_current_link()
            self.current_link = node.link

        if node.is_matharea():
            self.markdown += '$`'
            for child in node:
                self.process_node(child)
            self.markdown += '`$'

        elif node.head == 'EOL':
            self.markdown += '\n'

        elif node.head == 'placeholder':
            pass

        else:
            self.markdown += node.head

    def open_current_tags(self):
        if 'bold' in self.current_tags: self.markdown += '**'
        if 'italic' in self.current_tags: self.markdown += '*'

    def close_current_tags(self):
        if 'bold' in self.current_tags: self.markdown += '**'
        if 'italic' in self.current_tags: self.markdown += '*'

    def open_current_link(self):
        self.markdown += '['

    def close_current_link(self):
        if self.current_link == None: return

        self.markdown += '](' + self.current_link.target + ')'


