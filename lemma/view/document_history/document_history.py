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
from gi.repository import Gdk, Pango, PangoCairo

import lemma.helpers.helpers as helpers
from lemma.app.color_manager import ColorManager


class DocumentHistory(object):

    def __init__(self, workspace, main_window):
        self.workspace = workspace
        self.view = main_window.history_view

        self.layout = Pango.Layout(self.view.get_pango_context())
        self.layout.set_ellipsize(Pango.EllipsizeMode.END)
        self.layout.set_alignment(Pango.Alignment.CENTER)
        self.font_desc_normal = self.layout.get_context().get_font_description()
        self.font_desc_bold = self.layout.get_context().get_font_description()
        self.font_desc_bold.set_weight(Pango.Weight.BOLD)

        self.items = list()

        self.view.content.set_draw_func(self.draw)
        self.update()

    def update(self):
        self.update_size()
        self.scroll_active_document_on_screen()
        self.view.content.queue_draw()

    def update_size(self):
        width = 0
        self.items = list()
        for i, document in enumerate(self.workspace.history.documents):
            self.items.append((i, document, width))
            width += self.get_item_extents(document.title).width / Pango.SCALE
            width += 37
            if i == self.workspace.history.active_document_index and self.workspace.mode == 'draft':
                break
        if self.workspace.mode == 'draft':
            width += self.get_item_extents('New Document').width / Pango.SCALE
            width += 37
        width += 72
        self.view.scrolling_widget.set_size(width, 1)

    def scroll_active_document_on_screen(self):
        if self.view.scrolling_widget.adjustment_x.get_upper() < self.view.scrolling_widget.scrolling_offset_x + self.view.scrolling_widget.width or self.workspace.history.active_document_index == len(self.items) - 1:
            self.view.scrolling_widget.scroll_to_position((self.view.scrolling_widget.adjustment_x.get_upper(), 0))
            return

        if self.workspace.history.active_document_index != None:
            i, document, document_offset = self.items[self.workspace.history.active_document_index]
            if document_offset < self.view.scrolling_widget.scrolling_offset_x:
                self.view.scrolling_widget.scroll_to_position((document_offset, 0))
                return

            i, document, document_offset = self.items[self.workspace.history.active_document_index + 1]
            if document_offset > self.view.scrolling_widget.scrolling_offset_x + self.view.scrolling_widget.width:
                self.view.scrolling_widget.scroll_to_position((document_offset - self.view.scrolling_widget.width - 1, 0))
                return

    def draw(self, widget, ctx, width, height):
        offset = -1 - int(self.view.scrolling_widget.scrolling_offset_x)
        for i, document, document_offset in self.items:
            is_active = (i == self.workspace.history.active_document_index)
            extents = self.get_item_extents(document.title)

            ctx.move_to(offset + 18, int((height - extents.height / Pango.SCALE) / 2) - 1)
            self.layout.set_font_description(self.font_desc_bold if (is_active and self.workspace.mode != 'draft') else self.font_desc_normal)
            self.layout.set_width(extents.width)
            self.layout.set_text(document.title)
            Gdk.cairo_set_source_rgba(ctx, ColorManager.get_ui_color('fg'))
            PangoCairo.show_layout(ctx, self.layout)
            self.draw_divider(ctx, offset, height)

            offset += extents.width / Pango.SCALE + 37

            if is_active and self.workspace.mode == 'draft':
                break

        if self.workspace.mode == 'draft':
            extents = self.get_item_extents('New Document')
            ctx.move_to(offset + 18, int((height - extents.height / Pango.SCALE) / 2) - 1)
            self.layout.set_font_description(self.font_desc_bold)
            self.layout.set_width(extents.width)
            self.layout.set_text('New Document')
            Gdk.cairo_set_source_rgba(ctx, ColorManager.get_ui_color('fg'))
            PangoCairo.show_layout(ctx, self.layout)
            self.draw_divider(ctx, offset, height)

    def draw_divider(self, ctx, offset, height):
        Gdk.cairo_set_source_rgba(ctx, ColorManager.get_ui_color('border_1'))
        ctx.rectangle(offset, 9, 1, height - 18)
        ctx.fill()

    def get_item_extents(self, text):
        self.layout.set_font_description(self.font_desc_bold)
        self.layout.set_width(-1)
        self.layout.set_text(text)
        return self.layout.get_extents()[1]


