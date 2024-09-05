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
from gi.repository import Gio, GLib, GObject, Gdk

import pickle
from urllib.parse import urlparse

from lemma.infrastructure.service_locator import ServiceLocator
from lemma.ui.dialogs.dialog_locator import DialogLocator
from lemma.ui.popovers.popover_manager import PopoverManager


class Actions(object):

    def __init__(self, workspace, main_window, application):
        self.workspace = workspace
        self.main_window = main_window
        self.application = application
        self.settings = ServiceLocator.get_settings()

        self.actions = dict()
        self.add_simple_action('add-document', self.add_document)
        self.add_simple_action('import-markdown-files', self.import_markdown_files)
        self.add_simple_action('delete-document', self.delete_document)
        self.add_simple_action('rename-document', self.rename_document)
        self.add_simple_action('export-markdown', self.export_markdown)
        self.add_simple_action('export-html', self.export_html)

        self.add_simple_action('go-back', self.go_back)
        self.add_simple_action('go-forward', self.go_forward)

        self.add_simple_action('undo', self.undo)
        self.add_simple_action('redo', self.redo)
        self.add_simple_action('cut', self.cut)
        self.add_simple_action('copy', self.copy)
        self.add_simple_action('paste', self.paste)
        self.add_simple_action('delete', self.delete_selection)
        self.add_simple_action('select-all', self.select_all)

        self.add_simple_action('insert-link', self.insert_link)
        self.add_simple_action('remove-link', self.remove_link)
        self.add_simple_action('edit-link', self.edit_link)
        self.add_simple_action('insert-symbol', self.insert_symbol, GLib.VariantType('as'))

        self.add_simple_action('set-paragraph-style', self.set_paragraph_style, GLib.VariantType('s'))
        self.add_simple_action('toggle-bold', self.toggle_bold)
        self.add_simple_action('toggle-italic', self.toggle_italic)

        self.add_simple_action('toggle-math-sidebar', self.toggle_math_sidebar)
        self.add_simple_action('show-paragraph-style-menu', self.show_paragraph_style_menu)
        self.add_simple_action('show-edit-menu', self.show_edit_menu)
        self.add_simple_action('show-document-menu', self.show_document_menu)
        self.add_simple_action('show-hamburger-menu', self.show_hamburger_menu)
        self.add_simple_action('show-preferences-dialog', self.show_preferences_dialog)
        self.add_simple_action('show-shortcuts-dialog', self.show_shortcuts_dialog)
        self.add_simple_action('show-about-dialog', self.show_about_dialog)

        self.actions['quit'] = Gio.SimpleAction.new('quit', None)
        self.main_window.add_action(self.actions['quit'])

        Gdk.Display.get_default().get_clipboard().connect('changed', self.on_clipboard_changed)
        self.workspace.history.connect('changed', self.on_history_change)
        self.workspace.connect('new_document', self.on_new_document)
        self.workspace.connect('document_removed', self.on_document_removed)
        self.workspace.connect('new_active_document', self.on_new_active_document)
        self.workspace.connect('document_changed', self.on_document_change)
        self.workspace.connect('mode_set', self.on_mode_set)
        self.update()

    def add_simple_action(self, name, callback, parameter=None):
        self.actions[name] = Gio.SimpleAction.new(name, parameter)
        self.main_window.add_action(self.actions[name])
        self.actions[name].connect('activate', callback)

    def on_clipboard_changed(self, clipboard): self.update()
    def on_history_change(self, history): self.update()
    def on_new_document(self, workspace, document=None): self.update()
    def on_document_removed(self, workspace, document=None): self.update()
    def on_new_active_document(self, workspace, document=None): self.update()
    def on_document_change(self, workspace, document): self.update()
    def on_mode_set(self, workspace): self.update()

    def update(self):
        active_document = self.workspace.active_document
        has_active_doc = (self.workspace.mode == 'documents' and active_document != None)

        prev_doc = self.workspace.history.get_previous_if_any(active_document)
        next_doc = self.workspace.history.get_next_if_any(active_document)
        can_undo = has_active_doc and active_document.can_undo()
        can_redo = has_active_doc and active_document.can_redo()
        insert_in_line = has_active_doc and active_document.cursor.get_insert_node().parent.is_root()
        has_selection = has_active_doc and active_document.cursor.has_selection()
        clipboard_formats = Gdk.Display.get_default().get_clipboard().get_formats().to_string()
        text_in_clipboard = 'text/plain;charset=utf-8' in clipboard_formats
        subtree_in_clipboard = 'lemma/ast' in clipboard_formats
        links_inside_selection = has_active_doc and len([node for node in active_document.ast.get_subtree(*active_document.cursor.get_state()) if node.link != None]) > 0
        cursor_inside_link = has_active_doc and active_document.cursor.get_insert_node().is_inside_link()

        self.actions['add-document'].set_enabled(True)
        self.actions['import-markdown-files'].set_enabled(True)
        self.actions['delete-document'].set_enabled(has_active_doc)
        self.actions['rename-document'].set_enabled(has_active_doc)
        self.actions['export-markdown'].set_enabled(has_active_doc)
        self.actions['export-html'].set_enabled(has_active_doc)
        self.actions['go-back'].set_enabled(self.workspace.mode == 'draft' or prev_doc != None)
        self.actions['go-forward'].set_enabled(next_doc != None)
        self.actions['undo'].set_enabled(has_active_doc and can_undo)
        self.actions['redo'].set_enabled(has_active_doc and can_redo)
        self.actions['cut'].set_enabled(has_active_doc and has_selection)
        self.actions['copy'].set_enabled(has_active_doc and has_selection)
        self.actions['paste'].set_enabled(has_active_doc and (text_in_clipboard or subtree_in_clipboard))
        self.actions['delete'].set_enabled(self.workspace.mode == 'documents' and has_selection)
        self.actions['select-all'].set_enabled(has_active_doc)
        self.actions['insert-link'].set_enabled(has_active_doc and insert_in_line)
        self.actions['remove-link'].set_enabled(has_active_doc and (links_inside_selection or ((not has_selection) and cursor_inside_link)))
        self.actions['edit-link'].set_enabled(has_active_doc and ((not has_selection) and cursor_inside_link))
        self.actions['insert-symbol'].set_enabled(has_active_doc)
        self.actions['set-paragraph-style'].set_enabled(has_active_doc)
        self.actions['toggle-bold'].set_enabled(has_active_doc)
        self.actions['toggle-italic'].set_enabled(has_active_doc)
        self.actions['toggle-math-sidebar'].set_enabled(True)
        self.actions['show-paragraph-style-menu'].set_enabled(has_active_doc)
        self.actions['show-edit-menu'].set_enabled(has_active_doc)
        self.actions['show-document-menu'].set_enabled(has_active_doc)
        self.actions['show-hamburger-menu'].set_enabled(True)
        self.actions['show-preferences-dialog'].set_enabled(True)
        self.actions['show-shortcuts-dialog'].set_enabled(True)
        self.actions['show-about-dialog'].set_enabled(True)

    def add_document(self, action=None, paramenter=''):
        self.workspace.enter_draft_mode()

    def import_markdown_files(self, action=None, paramenter=''):
        DialogLocator.get_dialog('import_documents').run(self.workspace)

    def delete_document(self, action=None, parameter=''):
        self.workspace.delete_document(self.workspace.active_document)

    def rename_document(self, action=None, parameter=''):
        self.application.document_view.init_renaming()

    def export_markdown(self, action=None, parameter=''):
        DialogLocator.get_dialog('export_markdown').run(self.workspace.active_document)

    def export_html(self, action=None, parameter=''):
        DialogLocator.get_dialog('export_html').run(self.workspace.active_document)

    def go_back(self, action=None, parameter=''):
        if self.workspace.mode == 'draft':
            self.workspace.leave_draft_mode()
        else:
            prev_doc = self.workspace.history.get_previous_if_any(self.workspace.active_document)
            if prev_doc != None:
                self.workspace.set_active_document(prev_doc, update_history=False)

    def go_forward(self, action=None, parameter=''):
        next_doc = self.workspace.history.get_next_if_any(self.workspace.active_document)
        if next_doc != None:
            self.workspace.set_active_document(next_doc, update_history=False)

    def undo(self, action=None, parameter=''):
        self.workspace.active_document.undo()

    def redo(self, action=None, parameter=''):
        self.workspace.active_document.redo()

    def cut(self, action=None, parameter=''):
        self.copy()
        self.delete_selection()

    def copy(self, action=None, parameter=''):
        clipboard = Gdk.Display.get_default().get_clipboard()
        ast = self.workspace.active_document.ast
        cursor = self.workspace.active_document.cursor
        subtree = ast.get_subtree(*cursor.get_state())
        chars = ''.join([node.value for node in subtree if node.is_char()])

        cp_text = Gdk.ContentProvider.new_for_bytes('text/plain;charset=utf-8', GLib.Bytes(chars.encode()))
        cp_internal = Gdk.ContentProvider.new_for_bytes('lemma/ast', GLib.Bytes(pickle.dumps(subtree)))
        cp_union = Gdk.ContentProvider.new_union([cp_text, cp_internal])

        clipboard.set_content(cp_union)

    def paste(self, action=None, parameter=''):
        Gdk.Display.get_default().get_clipboard().read_async(['text/plain', 'lemma/ast'], 0, None, self.on_paste)

    def on_paste(self, clipboard, result):
        result = clipboard.read_finish(result)

        if result[1].startswith('lemma/ast'):
            subtree = pickle.loads(result[0].read_bytes(8192 * 8192, None).get_data())
            self.workspace.active_document.add_command('insert_subtree', subtree)

        elif result[1] == 'text/plain':
            text = result[0].read_bytes(8192 * 8192, None).get_data().decode('utf-8')

            if len(text) < 2000:
                parsed_url = urlparse(text.strip())
                if parsed_url.scheme in ['http', 'https'] and '.' in parsed_url.netloc:
                    self.workspace.active_document.add_command('insert_text', text.strip(), text.strip())
                    return
            self.workspace.active_document.add_command('insert_text', text)

    def delete_selection(self, action=None, parameter=''):
        self.workspace.active_document.add_command('delete')

    def select_all(self, action=None, parameter=''):
        self.workspace.active_document.add_command('select_all')

    def insert_symbol(self, action=None, parameter=None):
        if parameter == None: return

        name = parameter[0]
        self.workspace.active_document.add_command('insert_symbol', name)

    def set_paragraph_style(self, action=None, parameter=None):
        name = parameter.get_string()
        self.workspace.active_document.add_command('set_paragraph_style', name)

    def toggle_bold(self, action=None, parameter=''):
        self.toggle_tag('bold')

    def toggle_italic(self, action=None, parameter=''):
        self.toggle_tag('italic')

    def toggle_tag(self, tagname):
        document = self.workspace.active_document

        char_nodes = [node for node in document.ast.get_subtree(*document.cursor.get_state()) if node.is_char()]
        all_tagged = True
        for node in char_nodes:
            if tagname not in node.tags: all_tagged = False

        if len(char_nodes) > 0:
            if all_tagged:
                document.add_command('remove_tag', tagname)
            else:
                document.add_command('add_tag', tagname)
        else:
            self.application.document_view.set_tags_at_cursor(self.application.document_view.tags_at_cursor ^ {tagname})

    def insert_link(self, action=None, parameter=''):
        DialogLocator.get_dialog('insert_link').run(self.workspace, self.workspace.active_document)

    def remove_link(self, action=None, parameter=''):
        self.workspace.active_document.add_command('remove_link')

    def edit_link(self, action=None, parameter=''):
        DialogLocator.get_dialog('insert_link').run(self.workspace, self.workspace.active_document)

    def toggle_math_sidebar(self, action=None, parameter=''):
        toggle = self.main_window.toolbar.math_sidebar_toggle
        toggle.set_active(not toggle.get_active())

    def show_paragraph_style_menu(self, action=None, parameter=''):
        PopoverManager.popup_at_button('paragraph_style')

    def show_edit_menu(self, action=None, parameter=''):
        PopoverManager.popup_at_button('edit_menu')

    def show_document_menu(self, action=None, parameter=''):
        PopoverManager.popup_at_button('document_menu')

    def show_hamburger_menu(self, action=None, parameter=''):
        PopoverManager.popup_at_button('hamburger_menu')
        return True

    def show_preferences_dialog(self, action=None, parameter=''):
        DialogLocator.get_dialog('preferences').run()

    def show_shortcuts_dialog(self, action=None, parameter=''):
        DialogLocator.get_dialog('keyboard_shortcuts').run()

    def show_about_dialog(self, action=None, parameter=''):
        DialogLocator.get_dialog('about').run()


