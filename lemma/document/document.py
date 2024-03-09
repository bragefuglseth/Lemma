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

import time

import lemma.ast.node as ast
from lemma.cursor.cursor import Cursor
from lemma.document.layouter.layouter import Layouter
from lemma.document.markdown_scanner.markdown_scanner import MarkdownScanner
from lemma.document.plaintext_scanner.plaintext_scanner import PlaintextScanner
from lemma.helpers.observable import Observable
from lemma.commands.command_processor import CommandProcessor


class Document(Observable):

    def __init__(self, workspace, id):
        Observable.__init__(self)
        self.workspace = workspace

        self.last_modified = time.time()
        self.command_processor = CommandProcessor(self)

        self.id = id
        self.title = ''
        self.lines = ast.Root()
        self.lines.insert(0, ast.Line())
        self.insert = Cursor(self, self.lines.get_child(0).get_child(0))
        self.implicit_x_position = 0
        self.scroll_insert_on_screen_after_layout_update = False
        self.layout = None
        self.markdown = None
        self.plaintext = None

        self.layouter = Layouter(self)
        self.markdown_scanner = MarkdownScanner(self)
        self.plaintext_scanner = PlaintextScanner(self)
        self.update() # this will create an empty layout, markdown string, ...

    def update(self):
        self.layouter.update()
        self.markdown_scanner.update()
        self.plaintext_scanner.update()
        self.update_implicit_x_position()

        self.last_modified = time.time()
        self.add_change_code('changed')

    def update_implicit_x_position(self):
        last_command = self.command_processor.get_last_command()
        if last_command != None and last_command.update_implicit_x_position:
            x, y = self.get_xy_at_node(self.insert.get_node())
            self.implicit_x_position = x

    def set_scroll_insert_on_screen_after_layout_update(self, animate=False):
        self.scroll_insert_on_screen_after_layout_update = True

    def get_xy_at_node(self, node):
        box = node.box
        x, y = (0, 0)

        while not box == self.layout:
            new_x, new_y = box.parent.get_xy_at_child(box)
            x += new_x
            y += new_y
            box = box.parent

        return x, y

    def get_node_at_xy(self, x, y):
        box = self.layout
        x = max(0, min(box.width, x))
        y = max(0, y)
        if y > box.height: x, y = (box.width, box.height)

        while not box.is_leaf():
            box = box.get_child_at_xy(x, y)
        return box.get_node()

    def move_cursor_by_offset(self, offset):
        offset_moved = 0
        iterator = self.insert.get_node().get_iterator()

        if offset < 0:
            while offset < offset_moved:
                if iterator.prev() == False:
                    break
                offset_moved -= 1
        else:
            while offset > offset_moved:
                if iterator.next() == False:
                    break
                offset_moved += 1
        self.insert.set_node(iterator.get_node())

        return offset_moved

    def insert_node_at_cursor(self, node):
        if isinstance(node, ast.EndOfLine):
	        self.insert_linebreak()
        elif isinstance(node, ast.UnicodeCharacter):
	        self.insert_character(node.content)
        elif isinstance(node, ast.MathSymbol):
	        self.insert_math_symbol(node.name)

    def insert_text_at_cursor(self, text):
        for char in text:
            if char == '\n':
    	        self.insert_linebreak()
            else:
    	        self.insert_character(char)

    def insert_character(self, char):
        character = ast.UnicodeCharacter(char)
        line = self.insert.get_node().get_iterator().get_line()
        index = line.get_index(self.insert.get_node())
        line.insert(index, character)

    def insert_linebreak(self):
        orig_line = self.insert.get_node().get_iterator().get_line()
        line_1, line_2 = orig_line.split(self.insert.get_node())
        index = self.lines.get_index(orig_line)
        self.lines.remove(orig_line)
        self.lines.insert(index, line_2)
        self.lines.insert(index, line_1)
        self.insert.set_node(line_2.get_child(0))

    def insert_math_symbol(self, name):
        symbol = ast.MathSymbol(name)
        line = self.insert.get_node().get_iterator().get_line()
        index = line.get_index(self.insert.get_node())
        line.insert(index, symbol)

    def delete_char_at_cursor(self):
        deleted_node = None

        line = self.insert.get_node().get_iterator().get_line()
        if self.insert.get_node() == line.get_child(-1):
            if self.lines.get_child(-1) != line:
                deleted_node = self.insert.get_node()

                line_1 = self.insert.get_node().get_iterator().get_line()
                line_2 = self.lines.get_child(self.lines.get_index(line_1) + 1)
                new_line = ast.Line()
                new_line.add(line_1)
                new_line.add(line_2)
                index = self.lines.get_index(line_1)
                self.lines.insert(index, new_line)
                self.lines.remove(line_1)
                self.lines.remove(line_2)
                self.insert.set_node(new_line.get_child(line_1.length() - 1))
        else:
            deleted_node = self.insert.get_node()

            line = self.insert.get_node().get_iterator().get_line()
            index = line.get_index(self.insert.get_node())
            line.remove(self.insert.get_node())
            self.insert.set_node(line.get_child(index))

        return deleted_node


