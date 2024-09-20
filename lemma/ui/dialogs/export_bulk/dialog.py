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
from gi.repository import GLib, Gio

import zipfile
import html2text
import os.path

import lemma.ui.dialogs.export_bulk.export_bulk_viewgtk as view
from lemma.infrastructure.service_locator import ServiceLocator


class Dialog(object):

    def __init__(self, main_window):
        self.main_window = main_window
        self.workspace = None
        self.current_values = dict()

    def run(self, workspace):
        self.workspace = workspace

        self.init_current_values()
        self.view = view.ExportBulkView(self.main_window)
        self.populate_view()
        self.observe_view()
        self.validate()
        self.view.present()

    def init_current_values(self):
        self.current_values['filename'] = None
        self.current_values['format'] = 'html'
        self.current_values['documents'] = set(self.workspace.documents)

    def populate_view(self):
        last_export_folder = ServiceLocator.get_settings().get_value('app_state', 'last_bulk_export_folder')
        if last_export_folder == None or not os.path.exists(last_export_folder) or not os.path.isdir(last_export_folder):
            last_export_folder = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS)
        if last_export_folder != None:
            self.view.file_chooser_button.dialog.set_initial_folder(Gio.File.new_for_path(last_export_folder))

        self.view.file_format_buttons[self.current_values['format']].set_active(True)

        for i, document in enumerate(self.workspace.documents):
            row = view.Row(document)
            row.button.set_active(document in self.current_values['documents'])
            self.view.list.append(row)
        self.view.select_all_button.set_active(True)

    def observe_view(self):
        self.view.file_chooser_button.connect('file-set', self.on_file_chosen)

        for value, button in self.view.file_format_buttons.items():
            button.connect('toggled', self.on_checkbutton_toggled, 'format', value)

        for row in self.view.list:
            row.button.connect('toggled', self.on_document_button_toggled, row.document)
        self.view.select_all_button.connect('toggled', self.on_select_all_button_toggled)

        self.view.cancel_button.connect('clicked', self.on_cancel_button_clicked)
        self.view.submit_button.connect('clicked', self.on_submit_button_clicked)

    def validate(self):
        is_valid = self.current_values['filename'] != None and len(self.current_values['documents']) > 0
        self.view.submit_button.set_sensitive(is_valid)

        if len(self.current_values['documents']) == len(self.workspace.documents):
            self.view.select_all_button.set_active(True)
        elif len(self.current_values['documents']) == 0:
            self.view.select_all_button.set_active(False)

    def on_document_button_toggled(self, button, document):
        if button.get_active():
            self.current_values['documents'].add(document)
        else:
            self.current_values['documents'].discard(document)
        self.validate()

    def on_select_all_button_toggled(self, button):
        is_active = button.get_active()
        for row in self.view.list:
            row.button.set_active(is_active)

    def on_checkbutton_toggled(self, button, name, value):
        if button.get_active():
            self.current_values[name] = value
        self.validate()

    def on_file_chosen(self, chooser_button):
        self.current_values['filename'] = chooser_button.get_filename()
        self.validate()

    def on_cancel_button_clicked(self, button):
        self.view.close()

    def on_submit_button_clicked(self, button):
        filename = self.current_values['filename']
        ServiceLocator.get_settings().set_value('app_state', 'last_bulk_export_folder', os.path.dirname(filename))

        with zipfile.ZipFile(filename, 'x') as file:
            if self.current_values['format'] == 'html':
                for document in self.current_values['documents']:
                    html = document.html.replace('<body>', '<body><h1>' + document.title + '</h1>')
                    file.writestr(str(document.id) + '.html', html)

            if self.current_values['format'] == 'markdown':
                for document in self.current_values['documents']:
                    markdown = '# ' + document.title + '\n'
                    markdown += html2text.html2text(document.html)
                    file.writestr(str(document.id) + '.md', markdown)

        self.view.close()


