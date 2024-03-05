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

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, cairo, PangoCairo

import datetime

from lemma.app.font_manager import FontManager
from lemma.app.color_manager import ColorManager
from lemma.layout.layout import *


class DocumentViewPresenter():

    def __init__(self, model):
        self.model = model
        self.view = self.model.view
        self.content = self.view.content
        self.cursor_coords = None

        self.content.set_draw_func(self.draw)

        self.model.connect('changed', self.on_change)

    def on_change(self, model):
        if self.model.document == None: return

        self.update_size()
        self.update_scrolling_destination()
        self.view.scrolling_widget.queue_draw()

    def update_size(self):
        height = self.model.document.layout.height + self.view.padding_bottom + self.view.padding_top + self.view.title_height + self.view.subtitle_height + self.view.title_buttons_height

        self.view.scrolling_widget.adjustment_x.set_upper(1)
        self.view.scrolling_widget.adjustment_y.set_upper(height)

    def update_scrolling_destination(self):
        if self.model.document.scroll_insert_on_screen_after_layout_update:
            self.model.document.scroll_insert_on_screen_after_layout_update = False
            self.scroll_insert_on_screen()

    def scroll_insert_on_screen(self, animate=False):
        document = self.model.document
        insert_position = document.get_xy_at_node(document.insert.get_node())
        content_offset = self.view.padding_top + self.view.title_height + self.view.subtitle_height
        insert_y = insert_position[1] + content_offset
        insert_height = self.view.insert_height
        window_height = self.view.get_allocated_height()
        scrolling_offset_y = self.view.scrolling_widget.scrolling_offset_y

        if window_height <= 0: return

        if insert_y < scrolling_offset_y:
            if insert_y == content_offset:
                self.view.scrolling_widget.scroll_to_position((0, 0))
            else:
                self.view.scrolling_widget.scroll_to_position((0, insert_y + self.view.insert_drawing_offset))
        elif insert_y > scrolling_offset_y - insert_height + window_height:
            if insert_position[1] == self.model.document.layout.height - self.model.document.layout.children[-1].height:
                self.view.scrolling_widget.scroll_to_position((0, self.model.document.layout.height + content_offset + self.view.padding_bottom - window_height))
            else:
                self.view.scrolling_widget.scroll_to_position((0, insert_y - window_height + insert_height + self.view.insert_drawing_offset))

    def draw(self, widget, ctx, width, height):
        if self.model.document == None: return

        self.cursor_coords = None
        scrolling_offset_y = self.view.scrolling_widget.scrolling_offset_y

        self.draw_title(ctx, self.view.padding_left, self.view.padding_top - scrolling_offset_y)

        self.draw_box(ctx, self.model.document.layout, self.view.padding_left, self.view.padding_top + self.view.title_height + self.view.subtitle_height + self.view.title_buttons_height - scrolling_offset_y)

        self.draw_cursor(ctx)

    def draw_title(self, ctx, offset_x, offset_y):
        ctx.move_to(offset_x, offset_y)
        Gdk.cairo_set_source_rgba(ctx, ColorManager.get_ui_color('title_color'))
        self.view.layout_title.set_text(self.model.document.title)
        PangoCairo.show_layout(ctx, self.view.layout_title)

        ctx.move_to(offset_x, offset_y + self.view.title_height + 8)
        Gdk.cairo_set_source_rgba(ctx, ColorManager.get_ui_color('description'))

        datetime_last_modified = datetime.datetime.fromtimestamp(self.model.document.last_modified)
        self.view.layout_subtitle.set_text('{datetime:%a}, {datetime.day} {datetime:%b} {datetime.year} - {datetime.hour}:{datetime.minute:02}'.format(datetime=datetime_last_modified))
        PangoCairo.show_layout(ctx, self.view.layout_subtitle)

        Gdk.cairo_set_source_rgba(ctx, ColorManager.get_ui_color('border_1'))
        ctx.rectangle(offset_x, offset_y + self.view.title_height, self.view.title_width, 1)
        ctx.fill()

    def draw_box(self, ctx, box, offset_x, offset_y):
        if isinstance(box, BoxVContainer):
            for child in box.children:
                self.draw_box(ctx, child, offset_x, offset_y)
                offset_y += child.height

        elif isinstance(box, BoxHContainer):
            for child in box.children:
                self.draw_box(ctx, child, offset_x, offset_y)
                offset_x += child.width

        elif isinstance(box, BoxGlyph):
            if box.is_selected:
                ctx.set_source_rgb(0, 0, 1)
                ctx.rectangle(offset_x, offset_y, box.width, box.height)
                ctx.fill()

            surface = FontManager.get_surface(box.char)
            if surface != None:
                ctx.set_source_surface(surface, offset_x + box.left, offset_y + box.height + box.top)
                pattern = ctx.get_source()
                pattern.set_filter(cairo.Filter.BEST)
                Gdk.cairo_set_source_rgba(ctx, ColorManager.get_ui_color('text'))
                ctx.mask(pattern)
                ctx.fill()

        if box == self.model.document.insert.get_node().box:
            self.cursor_coords = (offset_x, offset_y + self.view.insert_drawing_offset, 1, self.view.insert_height)

    def draw_cursor(self, ctx):
        if self.cursor_coords == None: return
        if not self.content.has_focus(): return

        Gdk.cairo_set_source_rgba(ctx, ColorManager.get_ui_color('cursor'))
        ctx.rectangle(*self.cursor_coords)
        ctx.fill()


