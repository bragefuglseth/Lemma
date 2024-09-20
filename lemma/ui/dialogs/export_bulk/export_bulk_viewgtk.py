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
from gi.repository import Gtk, Pango

from lemma.ui.dialogs.helpers.dialog_view_action import DialogViewAction


class ExportBulkView(DialogViewAction):

    def __init__(self, main_window):
        DialogViewAction.__init__(self, main_window, _('Bulk Export'), 500, 'export-bulk-dialog', _('Export'))

        self.add_header_label('<b>' + _('Filename') + '</b>')
        self.file_chooser_button = self.add_file_chooser_button_save()
        self.file_chooser_button.dialog.set_initial_name('.zip')
        self.file_chooser_button.dialog.set_title(_('Choose File'))

        self.add_header_label('<b>' + _('Format') + '</b>')
        self.file_format_buttons = self.add_radio_group({'html': _('HTML (recommended)'), 'markdown': _('Markdown')})

        self.add_header_label('<b>' + _('Documents to export') + '</b>')

        self.list = Gtk.ListBox()
        self.list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_child(self.list)
        self.scrolled_window.set_propagate_natural_height(True)
        self.scrolled_window.set_max_content_height(250)
        self.content.append(self.scrolled_window)


class Row(Gtk.ListBoxRow):

    def __init__(self, document):
        Gtk.ListBoxRow.__init__(self)
        self.set_activatable(False)

        self.document = document
        label = Gtk.Label.new(document.title)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_margin_end(18)
        self.button = Gtk.CheckButton()
        self.button.set_child(label)

        box = Gtk.CenterBox()
        box.set_orientation(Gtk.Orientation.HORIZONTAL)
        box.set_start_widget(self.button)
        box.set_end_widget(Gtk.Label.new(document.get_last_modified_string()))
        self.set_child(box)


