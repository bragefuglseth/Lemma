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

import re, urllib.parse
from html.parser import HTMLParser
from lemma.document.ast.node import Node
from lemma.document.ast.link import Link


class Command(HTMLParser):

    def __init__(self, html):
        HTMLParser.__init__(self)

        self.html = html
        self.is_undo_checkpoint = False
        self.update_implicit_x_position = True

        self.open_tags = list()
        self.tags = set()
        self.link_target = None
        self.document = None
        self.composite = None

    def run(self, document):
        self.document = document
        self.composite = Node('list')

        head, divider, rest = self.html.partition('<body>')
        body, divider, rest = rest.partition('</body>')
        self.feed(head)

        if body == '':
            self.composite.append(Node('EOL', '\n'))
        else:
            self.feed(body)

        self.document.ast.root = self.composite
        self.document = None
        self.composite = None

        document.ast.set_cursor_state([[0], [0]])
        document.set_scroll_insert_on_screen_after_layout_update()

    def handle_starttag(self, tag, attrs):
        self.open_tags.append(tag)

        if tag == 'br':
            self.composite.append(Node('EOL', '\n'))

        if tag == 'strong': self.tags.add('bold')
        if tag == 'em': self.tags.add('italic')
        if tag == 'a':
            for name, value in attrs:
                if name == 'href':
                    self.link_target = urllib.parse.unquote_plus(value)

    def handle_endtag(self, tag):
        self.open_tags.pop()

        if tag == 'strong': self.tags.remove('bold')
        if tag == 'em': self.tags.remove('italic')
        if tag == 'a': self.link_target = None

    def handle_data(self, data):
        if 'title' in self.open_tags:
            self.document.title = data

        elif 'math' in self.open_tags:
            for char in data:
                self.composite.append(Node('mathsymbol', char))

        else:
            for char in data:
                if char != '\n':
                    node = Node('char', char)
                    node.tags = self.tags.copy()
                    if self.link_target != None:
                        node.link = Link(self.link_target)
                    self.composite.append(node)

    def undo(self, document):
        pass


