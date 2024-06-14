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
from gi.repository import Gtk, Gdk, Pango, PangoCairo

import datetime

import lemma.helpers.helpers as helpers
from lemma.infrastructure.service_locator import ServiceLocator
from lemma.infrastructure.color_manager import ColorManager
import lemma.helpers.helpers as helpers
from lemma.ui.context_menus.document_list import ContextMenuDocumentList


class DocumentList(object):

    def __init__(self, workspace, main_window):
        self.workspace = workspace
        self.view = main_window.document_list

        self.selected_index = None

        self.view.scrolling_widget.connect('primary_button_press', self.on_primary_button_press)
        self.view.scrolling_widget.connect('primary_button_release', self.on_primary_button_release)

        self.context_menu = ContextMenuDocumentList(self)

        self.view.content.set_draw_func(self.draw)
        self.update()

    def update(self):
        self.view.scrolling_widget.set_size(1, max(len(self.workspace.documents) * self.view.line_height, 1))
        self.view.scrolling_widget.queue_draw()

    def set_selected_index(self, index):
        if index != self.selected_index:
            self.selected_index = index
            self.view.content.queue_draw()

    def activate_item(self, index):
        self.workspace.set_active_document(self.workspace.documents[index])

    def on_primary_button_press(self, scrolling_widget, data):
        x_offset, y_offset, state = data

        if state == 0:
            item_num = self.view.get_item_at_cursor()
            if item_num != None and item_num < len(self.workspace.documents):
                self.set_selected_index(item_num)

    def on_primary_button_release(self, scrolling_widget, data):
        x_offset, y_offset, state = data

        item_num = self.view.get_item_at_cursor()
        if item_num != None and item_num == self.selected_index:
            self.activate_item(item_num)
        self.set_selected_index(None)

    #@helpers.timer
    def draw(self, widget, ctx, width, height):
        sidebar_fg_1 = ColorManager.get_ui_color('sidebar_fg_1')
        sidebar_fg_2 = ColorManager.get_ui_color('sidebar_fg_2')
        bg_color = ColorManager.get_ui_color('sidebar_bg_1')
        hover_color = ColorManager.get_ui_color('sidebar_hover')
        selected_color = ColorManager.get_ui_color('sidebar_selection')
        active_bg_color = ColorManager.get_ui_color('sidebar_active_bg')
        active_fg_color = ColorManager.get_ui_color('sidebar_active_fg')

        scrolling_offset = self.view.scrolling_widget.adjustment_y.get_value()

        self.view.layout_header.set_width((width - 80) * Pango.SCALE)
        self.view.layout_date.set_width((width - 30) * Pango.SCALE)
        self.view.layout_teaser.set_width((width - 30) * Pango.SCALE)

        Gdk.cairo_set_source_rgba(ctx, bg_color)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()
        Gdk.cairo_set_source_rgba(ctx, sidebar_fg_1)

        for i, document in enumerate(self.workspace.documents):
            highlight_active = (document == self.workspace.active_document and self.workspace.mode == 'documents')
            if highlight_active:
                title_color = active_fg_color
                teaser_color = active_fg_color
                date_color = active_fg_color
            else:
                title_color = sidebar_fg_1
                teaser_color = sidebar_fg_1
                date_color = sidebar_fg_1

            if i == self.selected_index:
                Gdk.cairo_set_source_rgba(ctx, selected_color)
                ctx.rectangle(0, self.view.line_height * i - scrolling_offset, width, self.view.line_height)
                ctx.fill()
            elif not highlight_active and i == self.view.get_item_at_cursor():
                Gdk.cairo_set_source_rgba(ctx, hover_color)
                ctx.rectangle(0, self.view.line_height * i - scrolling_offset, width, self.view.line_height)
                ctx.fill()
            if highlight_active:
                Gdk.cairo_set_source_rgba(ctx, active_bg_color)
                ctx.rectangle(0, self.view.line_height * i - scrolling_offset, width, self.view.line_height)
                ctx.fill()

            title_text = document.title
            if len(document.plaintext) == 0:
                teaser_text = '(' + _('empty') + ')'
                teaser_color = sidebar_fg_2
            else:
                teaser_text = ' '.join(document.plaintext.splitlines())[:100]
            date_text = self.get_last_modified_string(document)

            Gdk.cairo_set_source_rgba(ctx, title_color)
            ctx.move_to(15, self.view.line_height * i + 12 - scrolling_offset)
            self.view.layout_header.set_text(title_text)
            PangoCairo.show_layout(ctx, self.view.layout_header)

            Gdk.cairo_set_source_rgba(ctx, date_color)
            ctx.move_to(15, self.view.line_height * i + 12 - scrolling_offset)
            self.view.layout_date.set_text(date_text)
            PangoCairo.show_layout(ctx, self.view.layout_date)

            Gdk.cairo_set_source_rgba(ctx, teaser_color)
            ctx.move_to(15, self.view.line_height * i + 35 - scrolling_offset)
            self.view.layout_teaser.set_text(teaser_text)
            PangoCairo.show_layout(ctx, self.view.layout_teaser)

    def get_last_modified_string(self, document):
        datetime_today, datetime_this_week, datetime_this_year = ServiceLocator.get_datetimes_today_week_year()
        datetime_last_modified = datetime.datetime.fromtimestamp(document.last_modified)
        if document.last_modified >= datetime_today.timestamp():
            return '{datetime.hour}:{datetime.minute:02}'.format(datetime=datetime_last_modified)
        elif document.last_modified >= datetime_this_week.timestamp():
            return '{datetime:%a}'.format(datetime=datetime_last_modified)
        elif document.last_modified >= datetime_this_year.timestamp():
            return '{datetime.day} {datetime:%b}'.format(datetime=datetime_last_modified)
        else:
            return '{datetime.day} {datetime:%b} {datetime.year}'.format(datetime=datetime_last_modified)


