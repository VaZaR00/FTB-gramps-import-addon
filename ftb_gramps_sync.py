#------------------------------------------------------------------------
#
# python modules
#
#------------------------------------------------------------------------
from functools import partial
import mimetypes
import copy
from typing import Optional
from constants import *
from ftb_dto import *
import sqlite3
import re
import os
import shutil
from datetime import datetime
from PIL import Image
from collections.abc import Iterable
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

#------------------------------------------------------------------------
#
# gramps modules
#
#------------------------------------------------------------------------
from gramps.gen.db import DbTxn
from gramps.gen.db.base import DbWriteBase
from gramps.gui.managedwindow import ManagedWindow
from gramps.gen.lib import *
from gramps.gen.utils.id import create_id
from gramps.gui.plug.tool import BatchTool, ToolOptions
from gramps.gen.config import config
from gramps.gen.lib.refbase import RefBase

DEV_TEST_BD_PATH = ''

CHANGES_COMMIT_MAIN_CLASSES = (Person, Family, Repository, Media, Source, Place)

"""
TODO:
1. Translation
"""

#region Helpers
def isEmptyOrWhitespace(s) -> bool:
    return not s or s.strip() == ""

def getValFromMap(data_map, search_key, indx):
    for tupl in data_map:
        if tupl[0] == search_key:
            return tupl[indx]
    return None

def formatMHid(id, pfx) -> str:
        return f"MH:{pfx}{id:0{DEFAULT_NUM_OF_ZEROS_ID_MH}}"

def forLog(data):
    try:
        data = toTuple(data)
        return data[0].hintKey()
    except:
        return "null"

def clsName(obj) -> str:
    return type(obj).__name__.lower()

def clearNones(arr):
    return [el for el in arr if el is not None]

def createCleanList(arr, func, *funcargs):
    """Create list from array without duplicates and Nones"""
    res = []
    for obj in arr:
        new = func(obj, *funcargs)
        if new and not (new in res):
            res.append(new)
    
    return res

def toArr(s):
    if not isinstance(s, (list, tuple)):
        return [s]
    return s

def getFromListByKey(arr, key, default=-1, returnIndex=0, findIndex=0, returnAll=False):
    for el in arr:
        if el[findIndex] == key:
            if returnAll:
                return el
            return el[returnIndex]

    return default

def getReferencedObjectsCommited(obj, func=lambda a: a):
    genTypes = ("note", "citation", "attribute", "media", "address", "url", "event_ref", "surname", "reporef")
    methodNames = ["get_alternate_names", "get_reference_handle"]
    resList = []

    for typ in genTypes:
        methodNames.append("get_" + typ + "_list")

    for methodName in methodNames:
        try:
            method = BaseDTO.method(obj, methodName)
            
            if not method: continue

            refs = toArr(method())
            # print(f'\n++{methodName.upper()}: {refs}\n method: {method}\n')
            
            for ref in refs:
                resList.append(func(ref))
        except Exception as e:
            pass
            # print(f"GET SECONDARY: {e}")

    return resList

def classSortVal(clsname):
    values = {
        "person": 0,
        "family": 1,
        "event": 2,
        "media": 3
    }
    return values.get(clsname, ord(clsname[0]))

def toTuple(v):
    if isinstance(v, tuple):
        return v
    else: 
        return (v, )

class ToConnectReferenceObjects(BaseDTO):
    # obj: object = None
    notes: list = []
    attributes: list = []
    medias: list = []
    events: list = []
    citations: list = []
    urls: list = []
    addresses: list = []
    names: list = []
    surnames: list = []
    repositories: list = []
    source: object = None
    primaryName: object = None
    place: object = None

class ObjectSettings(BaseDTO):
    makeReplaceOption: bool = True
    doReplace: bool = True
    doFilter: bool = False

class FilterOptions(BaseDTO):
    upd_stamp: int
#endregion

#------------------------------------------------------------------------
#
#region GUI

class Page(Gtk.Box):
    """Page base class."""

    def __init__(self, assistant: Gtk.Assistant):
        """Initialize self."""
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self.assistant = assistant
        self._complete = False

    def set_complete(self):
        """Set as complete."""
        self._complete = True
        self.update_complete()

    @property
    def complete(self):
        return self._complete

    def update_complete(self):
        """Set the current page's complete status."""
        page_number = self.assistant.get_current_page()
        current_page = self.assistant.get_nth_page(page_number)
        self.assistant.set_page_complete(current_page, self.complete)

class IntroductionPage(Page):
    """A page containing introductory text."""

    def __init__(self, assistant):
        super().__init__(assistant)
        label = Gtk.Label(label=MENU_LBL_INTRO_TEXT)
        label.set_line_wrap(True)
        label.set_use_markup(True)
        label.set_max_width_chars(60)

        self.pack_start(label, False, False, 0)
        self._complete = True

class FileSelectorPage(Page):
    def __init__(self, assistant, cfg):
        super().__init__(assistant)
        
        self.cfg = cfg
        self.tryConnect = cfg.tryConnectSQLdb
        self.objectSettings: dict = cfg.objectSettings
        self.checkboxes = []

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)

        label = Gtk.Label(label=MENU_LBL_PATH_TEXT)
        label.set_line_wrap(True)
        label.set_use_markup(True)
        label.set_max_width_chars(60)
        main_box.pack_start(label, False, False, 0)

        self.file_chooser = Gtk.FileChooserButton(
            title=MENU_LBL_CHOOSE_FILE,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        self.file_chooser.set_width_chars(50)
        self.file_chooser.connect("file-set", self.on_file_selected)
        main_box.pack_start(self.file_chooser, False, False, 5)

        self.file_path_label = Gtk.Label(label="")
        main_box.pack_start(self.file_path_label, False, False, 5)

        self.folder_error = Gtk.Label(label="")
        main_box.pack_start(self.folder_error, False, False, 5)

        # copy media
        self.doCopyChk = Gtk.CheckButton(label=MENU_LBL_CHK_COPYMEDIA)
        self.doCopyChk.set_tooltip_text(MENU_LBL_TIP_COPYMEDIA)
        self.doCopyChk.connect("toggled", partial(self.onChkToggle, cfg.setCopyMedia))
        self.doCopyChk.set_active(cfg._doCopyMedia)
        main_box.pack_start(self.doCopyChk, False, False, 5)

        # do handling
        self.doHndlChk = Gtk.CheckButton(label=MENU_LBL_CHK_DOHANDLE)
        self.doHndlChk.set_tooltip_text(MENU_LBL_TIP_DOHANDLE)
        self.doHndlChk.connect("toggled", partial(self.onChkToggle, cfg.setHandling))
        self.doHndlChk.set_active(cfg._doHandling)
        main_box.pack_start(self.doHndlChk, False, False, 5)

        # object options
        for key, option in self.objectSettings.items():
            if not option.makeReplaceOption: continue
            checkbox = Gtk.CheckButton(label=MENU_LBL_CHK_REPLACE.format(key.__name__))
            checkbox.set_tooltip_text(MENU_LBL_TIP_REPLACE.format(key.__name__))
            checkbox.connect("toggled", partial(self.on_checkbox_toggled, option))
            checkbox.set_active(option.doReplace)
            main_box.pack_start(checkbox, False, False, 5)
            self.checkboxes.append(checkbox)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_height(200)
        scrolled_window.set_max_content_height(400)
        scrolled_window.add(main_box)

        self.pack_start(scrolled_window, True, True, 0)

        self.selected_file_path = None
        self._complete = False

        if DEV_TEST_BD_PATH:
            self.set_complete()

        self.show_all()

    def onChkToggle(self, var, widget):
        state = widget.get_active()
        var(state)

    def on_checkbox_toggled(self, sett: ObjectSettings, widget):
        state = widget.get_active()  
        sett.doReplace = state

    def on_file_selected(self, widget):
        """File selector handler."""
        self.show_folder_error(False)
        path = widget.get_filename() 
        self.selected_file_path = path
        self.file_path_label.set_text(MENU_LBL_PATH_SELECTED.format(path))
        
        if self.tryConnect(path):
            self.set_complete()
        else:
            self.show_folder_error()

    def get_selected_file_path(self):
        """Return selected file path."""
        return self.selected_file_path
    
    def show_folder_error(self, show=True):
        """Show folder error."""
        if show:
            self.folder_error.set_text(MENU_LBL_HIDDEN_CONT_ERROR_FILE_SEL)
            return
        self.folder_error.set_text("")

class ProgressPage(Page):
    """A progress page with a log window."""

    def __init__(self, assistant):
        super().__init__(assistant)
        
        label = Gtk.Label(label="")
        label.set_line_wrap(True)
        label.set_use_markup(True)
        label.set_max_width_chars(60)
        self.label = label
        self.pack_start(self.label, False, False, 0)

        # Text field for logs
        self.log_text_view = Gtk.TextView()
        self.log_text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.log_text_view.set_editable(False)  
        
        # Scroll for text field
        self.scroll_window = Gtk.ScrolledWindow()
        self.scroll_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.scroll_window.set_min_content_height(150)
        self.scroll_window.add(self.log_text_view)
        
        self.pack_start(self.scroll_window, True, True, 10)
        self.show_all()

class HandleChanges(Page):
    """A page to handle Gramps changes."""

    def __init__(self, assistant):
        super().__init__(assistant)
        self.commitChkboxes = []
        self.expanders = []

        self.set_border_width(10)

        title_lbl = Gtk.Label(label=MENU_LBL_HDNLCHNG_TEXT)
        title_lbl.set_xalign(0)
        self.pack_start(title_lbl, False, False, 0)

        self.create_buttons()
        self.create_header_row()
        self.data_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_height(200)
        scrolled_window.set_max_content_height(400)
        scrolled_window.add(self.data_area)

        self.loading_lbl = Gtk.Label(label=MENU_LBL_LOADING)
        self.loading_lbl.set_xalign(0)
        self.data_area.pack_start(self.loading_lbl, False, False, 0)

        self.pack_start(self.data_area, True, True, 0)
        self.pack_start(scrolled_window, True, True, 0)

    def create_object_block(self, obj: ObjectHandle = ObjectHandle(), level=0):
        """Create a block to display an ObjectHandle with nested attributes and objects."""
        # Main frame for the block with rounded edges
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)
        frame.set_margin_start(20 * level)  # Indent based on nesting level
        frame.set_margin_top(2)
        frame.set_margin_bottom(2)

        # Vertical box inside the frame
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        frame.add(main_vbox)

        # Header box for the object name and commit checkbox
        header_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        header_hbox.set_margin_start(5)
        header_hbox.set_margin_end(5)

        # Expander for toggle
        expander_toggle = Gtk.Expander(label=obj.name)
        expander_toggle.set_expanded(False)  # Start unexpanded
        expander_toggle.set_hexpand(False)  # Prevent expanding unnecessarily
        self.expanders.append(expander_toggle)

        # Commit checkbox
        commit_checkbox = Gtk.CheckButton()
        commit_checkbox.set_active(obj.commited)
        commit_checkbox.set_halign(Gtk.Align.END)
        commit_checkbox.set_valign(Gtk.Align.START)
        commit_checkbox.connect("toggled", partial(self.onCommitCheck, obj))
        self.linkCheckboxes(obj, commit_checkbox)

        # Pack the expander and checkbox into the header
        header_hbox.pack_start(expander_toggle, True, True, 0)
        header_hbox.pack_end(commit_checkbox, False, False, 0)
        main_vbox.pack_start(header_hbox, False, False, 0)

        # Content box for attributes and secondary objects
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)

        # Attributes table
        attr_listbox = Gtk.ListBox()
        for attr in obj.attributes:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            name_label = Gtk.Label(label=attr.name)
            new_value_label = Gtk.Label(label=attr.newValue)
            old_value_label = Gtk.Label(label=attr.oldValue)

            name_label.set_xalign(0)
            new_value_label.set_xalign(0.5)
            old_value_label.set_xalign(1)

            row.pack_start(name_label, True, True, 0)
            row.pack_start(new_value_label, True, True, 0)
            row.pack_start(old_value_label, True, True, 0)
            attr_listbox.add(row)

        attr_listbox.show_all()
        content_box.pack_start(attr_listbox, False, False, 0)

        # Secondary objects
        if obj.secondaryObjects:
            for secondary in obj.secondaryObjects:
                secondary_block = self.create_object_block(secondary, level=level + 1)
                content_box.pack_start(secondary_block, False, False, 0)

        # Add the content box to the expander
        expander_toggle.add(content_box)
        expander_toggle.show_all()

        # Add the expander content to the main vertical box
        main_vbox.pack_start(content_box, False, False, 0)

        # Return the entire frame
        frame.show_all()
        return frame

    def create_buttons(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        fold_all_btn = Gtk.Button(label=MENU_LBL_HDNLCHNG_TABLE_FOLD_ALL)
        fold_all_btn.connect("clicked", self.foldAll)

        unfold_all_btn = Gtk.Button(label=MENU_LBL_HDNLCHNG_TABLE_UNFOLD_ALL)
        unfold_all_btn.connect("clicked", self.unfoldAll)

        commit_all_button = Gtk.Button(label=MENU_LBL_HDNLCHNG_TABLE_COMMIT_ALL)
        commit_all_button.set_halign(Gtk.Align.END)
        commit_all_button.set_valign(Gtk.Align.START)
        commit_all_button.connect("clicked", partial(self.commit_all, True))
        
        uncommit_all_button = Gtk.Button(label=MENU_LBL_HDNLCHNG_TABLE_UNCOMMIT_ALL)
        uncommit_all_button.set_halign(Gtk.Align.END)
        uncommit_all_button.set_valign(Gtk.Align.START)
        uncommit_all_button.connect("clicked", partial(self.commit_all, False))

        box.pack_start(fold_all_btn, False, False, 0)
        box.pack_start(unfold_all_btn, False, False, 0)
        box.pack_start(commit_all_button, False, False, 0)
        box.pack_start(uncommit_all_button, False, False, 0)
        self.pack_start(box, False, False, 0)

    def foldAll(self, widget):
        self.setFoldState(False)

    def unfoldAll(self, widget):
        self.setFoldState(True)

    def setFoldState(self, state):
        for exp in self.expanders:
            exp.set_expanded(state)

    def create_header_row(self):
        """Create a global header row for the page."""
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        name_label = Gtk.Label(label=MENU_LBL_HDNLCHNG_TABLE_NAME)
        new_value_label = Gtk.Label(label=MENU_LBL_HDNLCHNG_TABLE_NEW)
        old_value_label = Gtk.Label(label=MENU_LBL_HDNLCHNG_TABLE_OLD)
        commit_label = Gtk.Label(label=MENU_LBL_HDNLCHNG_TABLE_COMMIT)
        
        name_label.set_xalign(0.1)
        new_value_label.set_xalign(0.45)
        old_value_label.set_xalign(0.85)
        commit_label.set_xalign(1)
        
        header.pack_start(name_label, True, True, 0)
        header.pack_start(new_value_label, True, True, 0)
        header.pack_start(old_value_label, True, True, 0)
        header.pack_start(commit_label, True, True, 0)
        header.show_all()
        self.pack_start(header, False, False, 0)
        return header

    def display_changes(self, objects: list[ObjectHandle]):
        """Display all objects and their changes."""
        self.loading_lbl.destroy()
        for obj in objects:
            obj_block = self.create_object_block(obj)
            self.data_area.pack_start(obj_block, False, False, 0)
        self.data_area.show_all()

    def onCommitCheck(self, obj: ObjectHandle, widget):
        chk = widget.get_active()
        obj.commited = chk
        self.checkLinkedChkboxes(obj, chk)
        for sobj in obj.secondaryObjects:
            if not isinstance(sobj.objRef, CHANGES_COMMIT_MAIN_CLASSES):
                self.checkLinkedChkboxes(sobj, chk)

    def commit_all(self, state, widget):
        for obj, *chks in self.commitChkboxes:
            for chk in chks:
                chk.set_active(state)

    def linkCheckboxes(self, obj, chkbox):
        exist = getFromListByKey(self.commitChkboxes, obj, None, returnAll=True)
        if exist:
            i = self.commitChkboxes.index(exist)
            self.commitChkboxes[i] = (*exist, chkbox)
        else:
            self.commitChkboxes.append((obj, chkbox))

    def checkLinkedChkboxes(self, obj, state):
        chks = getFromListByKey(self.commitChkboxes, obj, None, returnAll=True)
        if chks:
            _, *chkboxes = chks
            for chk in chkboxes:
                chk.set_active(state)

class FinishPage(Page):
    """The finish page."""

    def __init__(self, assistant):
        super().__init__(assistant)
        self.error = False
        self.unchanged = False
        label = Gtk.Label(label=MENU_LBL_FINISH_TEXT)
        label.set_line_wrap(True)
        label.set_use_markup(True)
        label.set_max_width_chars(60)
        self.label = label
        self.pack_start(self.label, False, False, 0)

#endregion
#
#------------------------------------------------------------------------

class FTB_Gramps_sync(BatchTool, ManagedWindow):
    def __init__(self, dbstate, user, options_class, name, *args, **kwargs):
        BatchTool.__init__(self, dbstate, user, options_class, name)
        ManagedWindow.__init__(self, user.uistate, [], self.__class__)
        self.dbState = dbstate 
        self.db = dbstate.db # Access to Gramps DB object
        self.dbHandler = None # Access to FTB SQL db
        self.connectedToFTBdb = False
        self.path = DEV_TEST_BD_PATH # File path chosen by user
        self.logs = []  
        self.toCommit = [] 
        self.compares = []
        self.referencesToConnect: list[ToConnectReferenceObjects] = []
        self.familyToConnect = []
        self.processing_complete = False
        self.succesfuly = True
        self._doCopyMedia = False
        self._doHandling = True
        self._doFilter = False

        if DEV_TEST_BD_PATH:
            self.tryConnectSQLdb(self.path)

        self.getConfigs()
        self.createGUI()

    #region Properties
    def setHandling(self, val):
        self._doHandling = val

    def setCopyMedia(self, val):
        self._doCopyMedia = val
    #endregion

    #------------------------------------------------------------------------
    #
    #region GUI

    def createGUI(self):
        """Initialize GUI."""
        self.assistant = Gtk.Assistant()
        self.set_window(self.assistant, None, MENU_TITLE)
        self.setup_configs("interface.ftbgrampssync", 780, 600)
        
        self.assistant.connect("close", self.do_close)
        self.assistant.connect("cancel", self.do_close)
        self.assistant.connect("prepare", self.prepare)
        self.assistant.connect("apply", self.apply)

        self.intro_page = IntroductionPage(self.assistant)
        self.add_page(self.intro_page, Gtk.AssistantPageType.INTRO, MENU_LBL_INTRO_TITLE)

        self.file_sel_page = FileSelectorPage(self.assistant, self)
        self.add_page(self.file_sel_page, Gtk.AssistantPageType.CONTENT, MENU_LBL_PATH_TITLE)

        self.progress_page = ProgressPage(self.assistant)
        self.add_page(self.progress_page, Gtk.AssistantPageType.PROGRESS, MENU_LBL_PROGRESS_TITLE)

        self.handle_change_page = HandleChanges(self.assistant)
        self.add_page(self.handle_change_page, Gtk.AssistantPageType.CONFIRM, MENU_LBL_HDNLCHNG_TITLE)
        
        self.finish_page = FinishPage(self.assistant)
        self.add_page(self.finish_page, Gtk.AssistantPageType.SUMMARY, MENU_LBL_FINISH_TITLE)
    
        self.show()
        self.assistant.set_forward_page_func(self.forward_page, None)

    def prepare(self, assistant, page: Page):
        """Run page preparation code."""

        page.update_complete()
        if page == self.progress_page:
            if self.connectedToFTBdb:
                self.log(HINT_PROCCESING)
                GLib.idle_add(self.start_processing)
                self.progress_page.set_complete()
            else:
                if self.processing_complete:
                    self.assistant.next_page()
                else:
                    self.assistant.previous_page()
        elif page == self.file_sel_page:
            if self.processing_complete:
                self.assistant.set_current_page(3)
        elif page == self.handle_change_page:
            if not self._doHandling: 
                page.set_complete()
                self.apply(self.assistant)
                self.assistant.next_page()
            
            if page.complete: return

            # t = threading.Thread(target=self.prepareHandleChangesAsync)
            # t.start()
            GLib.idle_add(self.prepareHandleChangesAsync)
            
            page.set_complete()
        else:
            page.set_complete()

    def prepareHandleChangesAsync(self):
        self.objectsList = self.createCompareObjectsList()
        self.handle_change_page.display_changes(self.objectsList)

    def add_page(self, page, page_type, title=""):
        """Add a page to the assistant."""
        page.show_all()
        self.assistant.append_page(page)
        self.assistant.set_page_title(page, title)
        self.assistant.set_page_type(page, page_type)

    def do_close(self, assistant):
        """Close the assistant."""
        position = self.window.get_position()  # crock
        self.assistant.hide()
        self.window.move(position[0], position[1])
        self.close()
    
    def apply(self, assistant):
        """Apply the changes."""
        page_number = assistant.get_current_page()
        page = assistant.get_nth_page(page_number)
        if page == self.handle_change_page:
            try:
                self.createCommitList()
                self.commitChanges()
            except Exception as e:
                self.log(f"ERROR WHILE APPLYING: {e}")
                # raise e

    def forward_page(self, pageN, data):
        """Specify the next page to be displayed."""

        return pageN + 1

    def log(self, s):
        buffer = self.progress_page.log_text_view.get_buffer()
        end_iter = buffer.get_end_iter()
        buffer.insert(end_iter, f"{s}\n")
        print(s)
    
    #endregion
    #
    #------------------------------------------------------------------------


    #------------------------------------------------------------------------
    #
    #region BACKEND

    #region main
    def getConfigs(self):
        self.objectSettings = {
            # if set to False it will always create new object (might duplicate)
            # else it will try to find if it exists already
            Person: ObjectSettings(False),
            Event: ObjectSettings(),
            Name: ObjectSettings(),
            Surname: ObjectSettings(),
            Attribute: ObjectSettings(),
            Note: ObjectSettings(),
            Citation: ObjectSettings(),
            Media: ObjectSettings(),
            Source: ObjectSettings(),
            Repository: ObjectSettings(),
            Date: ObjectSettings(),
            Url: ObjectSettings(),
            Address: ObjectSettings(),
            Place: ObjectSettings(),
        }
        # self.objectSettings[Person].filterByUPDstr = f"last_update = ?, {individual_main_data_DTO.key} = ?"

        self.filterOptions = FilterOptions()

        self.userMediaFolder = self.db.get_mediapath()
        self.getPrefixesFromConfig()

    def start_processing(self):
        """Start the backend processing."""
        try:
            self.log(HINT_PROCCES_CONNTODB.format(self.path))
            with DbTxn(f"FTB:GRAMPS:SYNC", self.db) as trans:
                self.trans = trans
                self.run()
        except Exception as e:
            self.log(HINT_PROCCES_ERROR.format(e))
            self.cancelChanges()
            raise e

    def run(self):
        self.find_photos_folder()

        allPersonsIds = self.dbHandler.fetchDbData(["individual_id"], "individual_main_data")
        allFamiliesIds = self.dbHandler.fetchDbData(["family_id"], "family_main_data")

        for id in allPersonsIds:
            self.handleObject(self.findPerson, id, False, False)

        for id in allFamiliesIds:
            self.handleObject(self.findFamily, id, False, False)

        if self.succesfuly:
            self.log(HINT_PROCCES_DONE_S)
        else:
            self.log(HINT_PROCCES_DONE_W)
        self.processing_complete = True
        self.connectedToFTBdb = False

    def tryConnectSQLdb(self, path):
        try:
            self.dbHandler = FTBDatabaseHandler(path)
            self.path = path
            self.connectedToFTBdb = True
            return True
        except Exception as e:
            return False

    def handleObject(self, find, arg=None, returnObj=False, keepEmpty=True):
        obj, modify, objClass, data = find(arg)
        if not self.checkFilter(data): return None
        name = objClass.__name__.lower()
        old = None
        exists = bool(obj)
        if not exists:
            obj = objClass()
            self.log(HINT_HANDLEOBJ_DONTEXISTS.format(name, forLog(data)))
            try:
                obj.set_handle(create_id())
            except:
                pass
        else:
            pass
            self.log(HINT_HANDLEOBJ_EXIST.format(name, forLog(data), obj))
            old = copy.deepcopy(obj)
        
        try:
            new = modify(obj, data)
        except Exception as e:
            new = None
            self.log(HINT_HANDLEOBJ_ERROR.format(name, obj, data, e))
            self.succesfuly = False

        if not new:
            if not keepEmpty: return None 
            new = obj

        self.clearEmptyAttributes(new)
        self.addCompare((new, old))
        
        # self.log(HINT_HANDLEOBJ_COMMIT.format(name, obj, datetime.now()))

        if not exists or returnObj:
            return new
        else:
            return None

    def unpackFacts(self, id, type, parent):
        events = []
        attributes = []
        urls = []
        addresses = []
        notes = []

        if type == FAMILY_ID_PFX:
            mainDto, langDto = family_fact_main_data_DTO, family_fact_lang_data_DTO
            id_name = "family_fact_id"
        else: 
            mainDto, langDto = individual_fact_main_data_DTO, individual_fact_lang_data_DTO
            id_name = "individual_fact_id"

        factsMain = self.formatFetchData(mainDto, id, self.findEvent)

        for _, fact in factsMain:
            token = fact.token
            factType = fact.fact_type
            factId = getattr(fact, id_name)

            langData = self.fetchData(((factId, ), langDto, False))
            if not langData:
                langData = [langDto("")]
            
            if fact.token == DEAT_TOKEN:
                # DEAT token has duplicate fact_lang data with Y value for some reason
                langData = [obj for obj in langData if obj.header != DEAT_TOKEN_FILTER_VAL]
                if not langData:
                    langData = [langDto("")]
            
            langData = langData[0]

            factName = self.defineEventType(token, factType)
            text = self.removeControlChars(langData.header)

            if factType: token = factType
            
            if token in ATTRIBUTE_TYPES:
                attributes.append((0, factName, text))
            elif token in ADDRESS_TYPES:
                address = self.parse_address(langData.header)
                setattr(address, "parent", parent)
                addresses.append((self.findAddress, address))
            elif token in URL_TYPES:
                urls.append((self.findURL, UrlDTO(factName, text, "", 0, parent)))
            elif token in NOTE_TYPES:
                if token == DSCR_TOKEN: 
                    obj: MHAddress = self.parse_address(langData.header)
                    text = NOTE_PHYS_DESCR.format(obj.address, obj.address2, obj.city, obj.state, obj.zip, obj.country)
                noteMain = note_main_data_DTO(factId, fact.guid, fact.privacy_level)
                noteLang = note_lang_data_DTO(text)
                setattr(noteMain, "parent", parent)
                notes.append((self.findNote, (factId, (noteMain, noteLang))))
            else: 
                events.append((self.findEvent, (fact, langData)))

        return events, attributes, urls, addresses, notes

    def fetchData(self, *args: tuple):
        if len(args) == 1: return self.dbHandler.fetchDbDataDto(*(args[0]))
        return tuple(self.dbHandler.fetchDbDataDto(*arg) for arg in args)

    def grampsDbMethod(self, obj, name, command="commit_%s"):
        method = self.db.method(command, name)
        if method:
            return method(obj, self.trans)

    def addFamilyConn(self, family, id):
        self.familyToConnect.append((family, id))

    def connectFamilies(self):
        for family, id in self.familyToConnect:
            if family in self.toCommit:
                try:
                    self.setFamilyMembers(family, id)
                except: pass

    def setFamilyMembers(self, family: Family, familyId):
        membersConnections: tuple[family_individual_connection_DTO] = self.fetchData((familyId, family_individual_connection_DTO, False))
        for member in membersConnections:
            id = member.individual_id
            role = member.individual_role_type
            person = self.findByIdsAttributes(formatMHid(id, "I"), "person", RIN, True)

            if not person: continue

            handle = person.get_handle()
            if role == 2:
                family.set_father_handle(handle)
                self.setPersonFamilyList(person, family.get_handle(), 1)
            elif role == 3:
                family.set_mother_handle(handle)
                self.setPersonFamilyList(person, family.get_handle(), 1)
            else:
                childList = [self.db.get_person_from_handle(child.ref) for child in family.get_child_ref_list()]
                child = self.findObjectByAttributes(
                    childList,
                    {"handle": person.get_handle()}
                )
                if child:
                    childRef = self.findObjectByAttributes(
                        family.get_child_ref_list(),
                        {"ref": child.get_handle()}
                    )
                else:
                    childRef = ChildRef()
                    childRef.set_reference_handle(person.get_handle())
                
                relType = ChildRefType.BIRTH
                if role == 6:
                    relType = ChildRefType.ADOPTED
                elif role == 7:
                    relType = ChildRefType.FOSTER

                childRef.set_father_relation(relType)
                childRef.set_mother_relation(relType)
                if not child:
                    family.add_child_ref(childRef)

                self.setPersonFamilyList(person, family.get_handle(), 0)

            # self.addCompare((person, None))
            self.grampsDbMethod(person, "person")
            self.grampsDbMethod(family, "family")

    def cancelChanges(self):
        self.db.undo()
    
    def createCompareObjectsList(self) -> list[ObjectHandle]:
        objects = []
        self.allObjectHandles: list[ObjectHandle] = []

        self.compareDto = CompareDTO()
        
        # print(f"--COMPARE\n{self.compares}\n--\n")

        for new, old in self.compares:
            if isinstance(new, CHANGES_COMMIT_MAIN_CLASSES):
                obj = self.createObjectHandle(new, old)
                if obj:
                    objects.append(obj)

        # print(objects)
        objects.sort(key=lambda x: x.sortval)
        return objects
    
    def createObjectHandle(self, new, old):
        exists = self.objectHandleExists(new)
        if exists: return exists

        attrsNew = self.compareDto.getAttributes(new)
        attrsOld = self.compareDto.getAttributes(old)

        if not attrsNew: return None
        if not attrsOld: attrsOld = dict()

        attHandlesList = [AttributeHandle(key, val, attrsOld.get(key, None)) for key, val in attrsNew.items()]
        func = lambda obj, self: self.createObjectHandle(obj, self.getFromCompareList(obj, None))
        secondaryObjs = createCleanList(self.getSecondaryObjects(new), func, self)
        secondaryObjs.sort(key=lambda x: x.sortval)

        # print(f"OBJECT_TYPE: {type(new)}\nSECOND: {self.getSecondaryObjects(new)}\nSECOND_made: {secondaryObjs}\n")

        res = ObjectHandle(
            clsName(new).title(),
            True,
            attHandlesList,
            secondaryObjs,
            new,
            classSortVal(clsName(new))
        )
        self.allObjectHandles.append(res)
        return res

    def objectHandleExists(self, obj):
        for o in self.allObjectHandles:
            if o.objRef == obj:
                return o
        return None

    def getSecondaryObjects(self, obj) -> list:
        # def do(ref):
        #     if isinstance(ref, RefBase):
        #         return self.getTempObj(ref.get_reference_handle())
        #     elif isinstance(ref, str):
        #         return self.getTempObj(ref)
        #     return ref

        return self.getReferencedObjects(obj)

    def addCompare(self, c):
        new, old = c

        if self.getFromCompareList(new) != -1: return

        self.compares.append((new, old))
    
    def getFromCompareList(self, key, default=-1):
        return getFromListByKey(self.compares, key, default)

    def createCommitList(self):
        if self._doHandling:
            for obj in self.objectsList:
                if obj.commited:
                    for sobj in obj.secondaryObjects:
                        if sobj.commited:
                            self.toCommit.append(sobj.objRef)
                    self.toCommit.append(obj.objRef)
        else:
            for new, old in self.compares:
                self.toCommit.append(new)

    def addConnectReferences(self, obj, *args, **kwargs):
        self.temp_i = 0
        def getv(name, default=[]):
            val = default
            try:
                val = kwargs.get(name, default)
                if not val:
                    val = args[self.temp_i]
            except: pass
            self.temp_i += 1
            return val

        self.referencesToConnect.append(
            (
                obj,
                ToConnectReferenceObjects(
                    notes=getv('notes'),
                    attributes=getv('attributes'),
                    medias=getv('medias'),
                    events=getv('events'),
                    citations=getv('citations'),
                    urls=getv('urls'),
                    addresses=getv('addresses'),
                    names=getv('names'),
                    surnames=getv('surnames'),
                    repositories=getv('repositories'),
                    source=getv('source', None),
                    primaryName=getv('primaryName', None),
                    place=getv('place', None)
                )
            )
        )
    
    def clearConRefFromNonCommit(self, cref):
        def check(o, att, isList=True):
            if o in self.toCommit:
                if isList:
                    getattr(cref, att, []).remove(o)
                else:
                    setattr(cref, att, None)

        for att, val in cref.__dict__.items():
            if isinstance(val, list):
                for el in val:
                    check(el, att)
            else:
                check(val, att, False)

    def connectRefs(self, obj):
        conRef = getFromListByKey(self.referencesToConnect, obj, None, 1)
        
        if not conRef: return

        # self.clearConRefFromNonCommit(conRef)

        for name in conRef.names:
            obj.add_alternate_name(name)
        for attribute in conRef.attributes:
            obj.add_attribute(attribute)
        for event in conRef.events:
            if event in self.toCommit:
                obj.add_event_ref(self.addObjRef(EventRef, event))
        for citation in conRef.citations:
            if citation in self.toCommit:
                obj.add_citation(citation.get_handle())
        for media in conRef.medias:
            if media in self.toCommit:
                obj.add_media_reference(self.addObjRef(MediaRef, media))
        for note in conRef.notes:
            if note in self.toCommit:
                obj.add_note(note.get_handle())
        for url in conRef.urls:
            obj.add_url(url)
        for address in conRef.addresses:
            obj.add_address(address)
        for surname in conRef.surnames:
            if not isEmptyOrWhitespace(surname.get_surname()):
                obj.add_surname(surname)
        for repo in conRef.repositories:
            if repo in self.toCommit:
                newRepoRef = self.addObjRef(RepoRef, repo)
                repoRefs = obj.get_reporef_list()
                if not any(rr.ref == newRepoRef.ref for rr in repoRefs):
                    obj.add_repo_reference(newRepoRef)
        if conRef.source:
            if conRef.source in self.toCommit:
                obj.set_reference_handle(conRef.source.get_handle())
        if conRef.primaryName:
            obj.set_primary_name(conRef.primaryName)
        if conRef.place:
            if conRef.place in self.toCommit:
                if conRef.place.get_name(): 
                    obj.set_place_handle(conRef.place.get_handle())

    def commitChanges(self):
        for obj in self.toCommit:
            name = clsName(obj)
            self.connectRefs(obj)
            self.grampsDbMethod(obj, name, "add_%s")
            self.grampsDbMethod(obj, name)
            # self.clearEmptyRefs(obj)
            # self.grampsDbMethod(obj, name)

        self.connectFamilies()
        self.db.transaction_commit(self.trans)
        self.dbState.signal_change()

    def doReplace(self, type):
        setting: ObjectSettings = self.objectSettings.get(type, None)
        if setting:
            return setting.doReplace
        else:
            return False
    
    def getReferencedObjects(self, obj, func=lambda a: a):
        conRef = getFromListByKey(self.referencesToConnect, obj, None, 1)
        
        if not conRef: return []

        resList = []

        for att in conRef.__dict__.values():
            try:
                if not att: continue
                if isinstance(att, list):
                    for el in att:
                        resList.append(func(el))
                else:
                    resList.append(func(att))
            except Exception as e:
                pass

        return resList
    
    def getFilter(self, cls, mainKey, filterType=None) -> tuple[tuple, str]:
        mainKey = toTuple(mainKey)
        filterType = "filterByUPD"
        try:
            sett = self.objectSettings[cls]
            if sett.doFilter:
                filtStr = getattr(sett, filterType + "str", "")
                keys = getattr(sett, filterType + "keys", ("", ))
                return ((*mainKey, *keys), filtStr)
            else: return (mainKey, "")
        except Exception as e:
            self.log(f"ERROR while getting filter {e}")
            return (mainKey, "")
    
    def checkFilter(self, data):
        if not self._doFilter: return True

        if not isinstance(data, (individual_main_data_DTO)): return True

        result = False
        opts = self.filterOptions

        if opts.upd_stamp:
            result = data.last_update > opts.upd_stamp

        return result
    #endregion

    #region Find objects in gramps
    def findPerson(self, id):
        if not id: return None, self.modifyPerson, Person, None
        mainData, dataSets = self.fetchData((id, individual_main_data_DTO), (id, individual_data_set_DTO, False))
        person = self.findByIdsAttributes(mainData.guid, "person")
        langData = [self.fetchData(((dataSet.individual_data_set_id, ), individual_lang_data_DTO)) for dataSet in dataSets]
        langData = [el for el in langData if el is not None]
        return person, self.modifyPerson, Person, (mainData, langData)

    def findFamily(self, id):
        data = self.fetchData((id, family_main_data_DTO))
        family = self.findByIdsAttributes(data.guid, "family")
        return family, self.modifyFamily, Family, data

    def findEvent(self, data):
        if not data: return None, self.modifyPerson, Person, None
        mainData, langData = data
        id = mainData.guid
        if isinstance(mainData, individual_fact_main_data_DTO):
            eventParentType = PERSON_ID_PFX
        else:
            eventParentType = FAMILY_ID_PFX

        
        if self.doReplace(Event):
            event = self.findByIdsAttributes(id, "event")

        mainData.__setattr__("parentType", eventParentType)

        return event, self.modifyEvent, Event, data

    def findName(self, data: individual_lang_data_DTO):
        name = None
        if self.doReplace(Name):
            parent = getattr(data, "parent", None)
            if parent:
                names = [parent.get_primary_name()] + parent.get_alternate_names()
                name = self.findObjectByAttributes(
                    names,
                    {"first_name": data.first_name}
                )

        return name, self.modifyName, Name, data

    def findSurname(self, data: SurnameDTO):
        surname = None
        if self.doReplace(Surname):
            parent = getattr(data, "parent", None)
            if parent:
                surname = self.findObjectByAttributes(
                    parent.get_surname_list(),
                    {"surname": data.surname}
                )

        return surname, self.modifySurname, Surname, data

    def findAttribute(self, data: AttributeDTO):
        attribute = None
        attClass = Attribute
        if self.doReplace(attClass):
            parent = getattr(data, "parent", None)
            if parent:
                attribute = self.findObjectByAttributes(
                    parent.get_attribute_list(),
                    {"type": data.type, "value": data.value}
                )
                if isinstance(parent, (Citation, Source)):
                    attClass = SrcAttribute

        return attribute, self.modifyAttribute, attClass, data

    def findNote(self, data: tuple[note_to_item_connection_DTO, tuple[note_main_data_DTO, note_lang_data_DTO]]):
        if not data: return None, self.modifyPerson, Person, None
        id, _data = data
        if not isinstance(id, int):
            id = id.note_id

        note = None
        if self.doReplace(Note):
            note = self.tryFind(self.db.get_note_from_gramps_id, NOTE_ID_PFX, id)
        if not _data:
            _data = self.fetchData((id, note_main_data_DTO, True), (id, note_lang_data_DTO))
        return note, self.modifyNote, Note, _data

    def findCitation(self, mainData: citation_main_data_DTO):
        citation = None
        if self.doReplace(Citation):
            citation = self.tryFind(self.db.get_citation_from_gramps_id, CITATION_ID_PFX, mainData.citation_id)
        langData = self.fetchData((mainData.citation_id, citation_lang_data_DTO))
        return citation, self.modifyCitation, Citation, (mainData, langData)

    def findMedia(self, id):
        if not id: return None, self.modifyPerson, Person, None
        id = id.media_item_id
        data = self.fetchData((id, media_item_main_data_DTO), (id, media_item_lang_data_DTO))
        guid = data[0].guid
        
        media = None
        if self.doReplace(Media):
            media = self.findByIdsAttributes(guid, "media")
        # media = self.tryFind(self.db.get_media_from_gramps_id, MEDIA_ID_PFX, id)
        return media, self.modifyMedia, Media, data

    def findSource(self, id):
        source = None
        if self.doReplace(Source):
            source = self.tryFind(self.db.get_source_from_gramps_id, SOURCE_ID_PFX, id)
        data = self.fetchData((id, source_main_data_DTO), (id, source_lang_data_DTO))
        return source, self.modifySource, Source, data

    def findRepository(self, id):
        repository = None
        if self.doReplace(Repository):
            repository = self.tryFind(self.db.get_repository_from_gramps_id, REPOSITORY_ID_PFX, id)
        data = self.fetchData((id, repository_main_data_DTO), (id, repository_lang_data_DTO))
        return repository, self.modifyRepository, Repository, data

    def findDate(self, data: DateDTO):
        date = None
        if self.doReplace(Date):
            parent = getattr(data, "parent", None)
            if parent:
                date = self.findObjectByAttributes(
                    [parent.date],
                    {"dateval": data.value}
                )

        return date, self.modifyDate, Date, data

    def findURL(self, data: UrlDTO):
        url = None
        if self.doReplace(Url):
            parent = getattr(data, "parent", None)
            if parent:
                url = self.findObjectByAttributes(
                    parent.get_url_list(),
                    {"type": data.type, "path": data.path}
                )
                
        return url, self.modifyURL, Url, data

    def findAddress(self, data: MHAddress):
        address = None
        if self.doReplace(Address):
            parent = getattr(data, "parent", None)
            if parent:
                address = self.findObjectByAttributes(
                    parent.get_address_list(),
                    {"street": data.address}
                )
                
        return address, self.modifyAddress, Address, data

    def findPlace(self, id):
        place = None
        if self.doReplace(Place):
            place = self.tryFind(self.db.get_place_from_gramps_id, PLACE_ID_PFX, id)
        data = self.fetchData((id, places_lang_data_DTO))
        return place, self.modifyPlace, Place, data
    #endregion

    #region Modify objects
    def modifyPerson(self, person: Person, data: tuple[individual_main_data_DTO, list[individual_lang_data_DTO]]):
        mainData, names = data
        if not (mainData and names): return None

        for name in names:
            setattr(name, "parent", person)
        
        privacy = bool(mainData.privacy_level)
        gender = self.convert_gender(mainData.gender)
        primary_name = self.handleObject(self.findName, names[0], True)

        defaultAttributes = [
            (privacy, UPD, mainData.last_update),
            (privacy, CRT, mainData.create_timestamp),
            (privacy, UID, mainData.guid.lower()),
            (privacy, RIN, formatMHid(mainData.individual_id, "I")),
            (privacy, RES_C, mainData.research_completed)
        ]
        
        events, attributes, urls, addresses, notes = self.unpackFacts(mainData.individual_id, PERSON_ID_PFX, person)
        attributes = defaultAttributes + attributes
        media = self.formatFetchData(media_item_to_item_connection_DTO, mainData.token_on_item_id, self.findMedia)
        citations = self.formatFetchData(citation_main_data_DTO, mainData.token_on_item_id, self.findCitation)
        
        newNames = self.createObjectsList(self.formatList(self.findName, names[1:]))
        newAttributes = self.createObjectsList(
            self.setupRefList(AttributeDTO, person, self.findAttribute, attributes)
        )
        newEvents = self.createObjectsList(events)
        newCitations = self.createObjectsList(citations)
        newMedia = self.createObjectsList(media)
        newNotes = self.createObjectsList(notes) + self.getNotes(mainData.token_on_item_id)
        newUrls = self.createObjectsList(urls)
        newAddresses = self.createObjectsList(addresses)

        self.trySetGrampsId(person, mainData.individual_id, PERSON_ID_PFX, True)
        person.set_privacy(privacy)
        person.set_gender(gender)
        person.set_primary_name(primary_name)
        
        self.addConnectReferences(person, newNotes, newAttributes, newMedia, newEvents, newCitations, newUrls, newAddresses, newNames, primaryName=primary_name)

        return person

    def modifyFamily(self, family: Family, data: family_main_data_DTO):
        mainData = data
        if not mainData: return None
        
        privacy = False

        defaultAttributes = [
            (privacy, UID, mainData.guid.lower()),
            (privacy, UID, formatMHid(mainData.family_id, "F")),
            (privacy, CRT, mainData.create_timestamp)
        ]
        
        events, attributes, urls, addresses, notes = self.unpackFacts(mainData.family_id, FAMILY_ID_PFX, family)
        attributes = defaultAttributes + attributes
        media = self.formatFetchData(media_item_to_item_connection_DTO, mainData.token_on_item_id, self.findMedia)
        citations = self.formatFetchData(citation_main_data_DTO, mainData.token_on_item_id, self.findCitation)
        
        newAttributes = self.createObjectsList(
            self.setupRefList(AttributeDTO, family, self.findAttribute, attributes)
        )
        newEvents = self.createObjectsList(events)
        newCitations = self.createObjectsList(citations)
        newMedia = self.createObjectsList(media)
        newNotes = self.createObjectsList(notes) + self.getNotes(mainData.token_on_item_id)

        self.trySetGrampsId(family, mainData.family_id, FAMILY_ID_PFX, True)
        family.set_privacy(privacy)
        
        self.addConnectReferences(family, newNotes, newAttributes, newMedia, newEvents, newCitations)
        self.addFamilyConn(family, mainData.family_id)
        
        return family

    def modifyEvent(self, event: Event, data: tuple):
        mainData, langData = data
        if not (mainData and langData): return None

        privacy = bool(mainData.privacy_level)
        eventParentType = getattr(mainData, "parentType")
        if eventParentType == PERSON_ID_PFX:
            attributes = [
                (privacy, PERSON_AGE, mainData.age),
                (privacy, CAUSE_DEAT, langData.cause_of_death)
            ]
            id = mainData.individual_fact_id
            pfx = PERSON_EVENT_ID_PFX
        else:
            attributes = [
                (privacy, SPOUSE_AGE, mainData.spouse_age)
            ]
            id = mainData.family_fact_id
            pfx = FAMILY_EVENT_ID_PFX

        attributes += [
            (privacy, UID, mainData.guid.lower()),
            (privacy, RIN, formatMHid(id, "E"))
        ]

        eventType = self.defineEventType(mainData.token, mainData.fact_type)
        date = self.extract_date(mainData)
        description = langData.header
        causeOfDeat = getattr(langData, "cause_of_death", None)
        if not isEmptyOrWhitespace(causeOfDeat) and causeOfDeat: 
            description = description + f" {CAUSE_DEAT}: " + causeOfDeat
        
        place = self.handleObject(self.findPlace, mainData.place_id, True, False)
        
        media = self.formatFetchData(media_item_to_item_connection_DTO, mainData.token_on_item_id, self.findMedia)
        newNotes = self.getNotes(mainData.token_on_item_id)
        newAttributes = self.createObjectsList(
            self.setupRefList(AttributeDTO, event, self.findAttribute, attributes)
        )
        newCitations = []
        newMedia = self.createObjectsList(media)

        self.trySetGrampsId(event, id, pfx, True)
        event.set_privacy(privacy)
        event.set_type(eventType)
        event.set_date_object(date)
        event.set_description(description)

        self.addConnectReferences(event, newNotes, newAttributes, newMedia, citations=newCitations, place=place)
        
        return event

    def modifyName(self, name: Name, data: individual_lang_data_DTO):
        if not data: return None

        surnames = self.createObjectsList(
            self.setupRefList(
                SurnameDTO, name, self.findSurname,
                [
                    (data.last_name, "", data.prefix),
                    (data.former_name, "Given", ""),
                    (data.married_surname, "Taken", ""),
                    (data.aka, "Pseudonym", ""),
                    (data.religious_name, "Religious")
                ]
            )
        )

        name.set_first_name(data.first_name)
        name.set_suffix(data.suffix)
        name.set_nick_name(data.nickname)
        name.set_call_name(data.aka)

        self.addConnectReferences(name, surnames=surnames)

    def modifySurname(self, surnameObj: Surname, data: SurnameDTO):
        if not data: return None
        if isEmptyOrWhitespace(data.surname): return None
        
        surnameObj.set_surname(data.surname)
        surnameObj.set_prefix(data.prefix)
        surnameObj.set_origintype(data.origin)
        return surnameObj

    def modifyAttribute(self, att: Attribute, data: AttributeDTO):
        if not data: return None
        if isEmptyOrWhitespace(data.value): return None
        
        att.set_privacy(data.privacy)
        att.set_type(data.type)
        att.set_value(data.value)
        return att
    
    def modifyNote(self, note: Note, data: tuple[note_main_data_DTO, note_lang_data_DTO]):
        mainData, langData = data
        if not (mainData and langData): return None

        self.trySetGrampsId(note, mainData.note_id, NOTE_ID_PFX)
        note.set_privacy(bool(mainData.privacy_level))
        note.set_styledtext(self.format_text(langData.note_text))
        return note

    def modifyMedia(self, media: Media, data: tuple[media_item_main_data_DTO, media_item_lang_data_DTO]):
        mainData, langData = data
        if not (mainData and langData): return None

        mediaId = mainData.media_item_id
        path = self.getMediaPath(mediaId)
        if not path: return None

        prvt = bool(mainData.is_privatized)
        notes = self.getNotes(mainData.token_on_item_id)
        attributes = self.createObjectsList(
            self.setupRefList(
                AttributeDTO, media, self.findAttribute,
                [
                    (prvt, UID, mainData.guid.lower()),
                    (prvt, DESCR, langData.description),
                    (prvt, RIN, formatMHid(mediaId, "M"))
                ]
            )
        )

        self.trySetGrampsId(media, mediaId, MEDIA_ID_PFX, True)
        media.set_path(path)
        media.set_privacy(prvt)
        media.set_date_object(self.extract_date(mainData))
        media.set_description(langData.title)
        # deal with mime types
        value = mimetypes.guess_type(media.get_path())
        if value and value[0]:  # found from filename
            media.set_mime_type(value[0])

        self.addConnectReferences(media, notes, attributes)

        return media

    def modifyCitation(self, citation: Citation, data: tuple[citation_main_data_DTO, citation_lang_data_DTO]):
        mainData, langData = data
        if not (mainData and langData): return None

        attributes = self.createObjectsList(
            self.setupRefList(
                AttributeDTO, citation, self.findAttribute,
                [
                    (False, DESCR, langData.description)
                ]
            )
        )
        notes = self.getNotes(mainData.token_on_item_id)

        self.trySetGrampsId(citation, mainData.citation_id, CITATION_ID_PFX)
        citation.set_page(mainData.page)
        citation.set_confidence_level(mainData.confidence)
        citation.set_date_object(self.extract_date(mainData))

        source = self.handleObject(self.findSource, mainData.source_id, True, False)

        self.addConnectReferences(citation, notes, attributes, source=source)

        return citation
    
    def modifySource(self, source: Source, data: tuple[source_main_data_DTO, source_lang_data_DTO]):
        mainData, langData = data
        if not (mainData and langData): return None

        notes = self.getNotes(mainData.token_on_item_id)
        attributes = self.createObjectsList(
            self.setupRefList(
                AttributeDTO, source, self.findAttribute,
                [
                    (False, CRT, mainData.create_timestamp),
                    (False, SRC_TEXT, langData.text),
                    (False, AGENCY, langData.agency)
                ]
            )
        )
        medias = self.createObjectsList(
            self.formatFetchData(media_item_to_item_connection_DTO, mainData.token_on_item_id, self.findMedia)
        )
        
        self.trySetGrampsId(source, mainData.source_id, SOURCE_ID_PFX)
        source.set_title(langData.title)
        source.set_abbreviation(langData.abbreviation)
        source.set_author(langData.author)
        source.set_publication_info(langData.publisher)

        repo = self.handleObject(self.findRepository, mainData.repository_id, True, False)
        
        self.addConnectReferences(source, notes, attributes, medias, repositories=[repo])

        return source

    def modifyRepository(self, repo: Repository, data: tuple[repository_main_data_DTO, repository_lang_data_DTO]):
        mainData, langData = data
        if not (mainData and langData): return None

        notes = self.getNotes(mainData.token_on_item_id)
        urls = self.createObjectsList(
            self.setupRefList(
                UrlDTO, repo, self.findURL,
                [
                    (PHON_NUM, mainData.phone1, "Phone 1"),
                    (PHON_NUM, mainData.phone2, "Phone 2"),
                    (EMAIL, mainData.email),
                    (FAX, mainData.fax),
                    (WEBSITE, mainData.website)
                ]
            )
        )
        repoAddress = self.parse_address(langData.address)
        setattr(repoAddress, "parent", repo)
        newAddresses = self.createObjectsList([(self.findAddress, repoAddress)])

        self.trySetGrampsId(repo, mainData.repository_id, REPOSITORY_ID_PFX)
        repo.set_name(langData.name)
        for note in notes:
            repo.add_note(note.get_handle())
        for url in urls:
            repo.add_url(url)
        for address in newAddresses:
            repo.add_address(address)

        self.addConnectReferences(repo, notes, urls=urls, addresses=newAddresses)

        return repo
    
    def modifyDate(self, dateObj: Date, data: DateDTO):
        if not data: return None
        
        dateObj.set(data.quality, data.modified, 0, data.value, data.dateText)

        return dateObj

    def modifyURL(self, url: Url, data: UrlDTO):
        if not data: return None

        url.set_type(data.type)
        url.set_description(data.descr)
        url.set_path(data.path)
        url.set_privacy(bool(data.privacy))

        return url

    def modifyAddress(self, address: Address, data: MHAddress):
        if not data: return None

        address.set_street(data.address)
        address.set_locality(data.address2)
        address.set_city(data.city)
        address.set_state(data.state)
        address.set_postal_code(data.zip)
        address.set_country(data.country)

        return address

    def modifyPlace(self, place: Place, data: places_lang_data_DTO):
        if not data: return None
        if isEmptyOrWhitespace(data.place) or not data.place or data.place == "": return None

        self.trySetGrampsId(place, data.place_id, PLACE_ID_PFX)
        placeName = PlaceName()
        placeName.set_value(data.place)
        place.set_name(placeName)

        return place
    #endregion

    #region Class Helpers 
    def getNotes(self, id):
        try:
            return self.createObjectsList(
                self.formatList(
                    self.findNote,
                    self.formatList(
                        None, 
                        self.fetchData(((id,), note_to_item_connection_DTO, False)),
                        True
                    )
                )
            )
        except:
            return []

    def addObjRef(self, typeRef, obj):
        ref = typeRef()
        ref.set_reference_handle(obj.get_handle())
        return ref

    def setPersonFamilyList(self, person, familyHandle, listType=0):
        """
        Sets persons family list

        :param self: FTB_Gramps_sync class
        :param person: Person class
        :param familyHandle: Family class handle
        :param listType: Type of action: 0 - parent family, 1 - persons family
        """
        if listType == 0:
            person.add_parent_family_handle(familyHandle)
        elif listType == 1:
            person.add_family_handle(familyHandle)

    def clearEmptyAttributes(self, obj):
        try:
            attrs = obj.get_attribute_list()
            for att in attrs:
                val = att.get_value()
                type = att.get_type()
                if not val or isEmptyOrWhitespace(val):
                    if type == getValFromMap(AttributeType._BASEMAP, AttributeType.ID, 2):
                        obj.remove_attribute(att)
        except:
            return

    def extract_date(self, data) -> DateDTO:
        dto = self.parse_custom_date(data.date)
        dateObj = self.handleObject(self.findDate, dto, True)

        return dateObj

    def convert_gender(self, gender):
        if gender == 'F': return 0
        elif gender == 'M': return 1
        else: return 2

    def defineEventType(self, token: str, factType: str):
        if factType:
            token = factType

        if ET_MH_TOKEN in token:
            token = token.replace(ET_MH_TOKEN, "", 1)
            if ET_REL_PRFX in token:
                token = token.replace(ET_REL_PRFX, "", 1)

        def getET(key):
            return getValFromMap(EventType._DATAMAP, key, 2)
        def getAT(key):
            return getValFromMap(EventType._DATAMAP, key, 2)

        event_mapping = {
            DEAT_TOKEN: getET(EventType.DEATH),
            BIRT_TOKEN: getET(EventType.BIRTH),
            EDUC_TOKEN: getET(EventType.EDUCATION),
            OCCU_TOKEN: getET(EventType.OCCUPATION),
            NATU_TOKEN: getET(EventType.NATURALIZATION),
            RESI_TOKEN: getET(EventType.RESIDENCE),
            BURI_TOKEN: getET(EventType.BURIAL),
            MARR_TOKEN: getET(EventType.MARRIAGE),
            NMR_TOKEN: getET(EventType.NUM_MARRIAGES),
            DIV_TOKEN: getET(EventType.DIVORCE),
            RELI_TOKEN: getET(EventType.RELIGION),
            BARM_TOKEN: getET(EventType.BAR_MITZVAH),
            BASM_TOKEN: getET(EventType.BAS_MITZVAH),
            WILL_TOKEN: getET(EventType.WILL),
            PROB_TOKEN: getET(EventType.PROBATE),
            PROP_TOKEN: getET(EventType.PROPERTY),
            FCOM_TOKEN: getET(EventType.FIRST_COMMUN),
            DIVF_TOKEN: getET(EventType.DIV_FILING),
            CHRA_TOKEN: getET(EventType.ADULT_CHRISTEN),
            BAPM_TOKEN: getET(EventType.BAPTISM),
            ORDN_TOKEN: getET(EventType.ORDINATION),
            CONF_TOKEN: getET(EventType.CONFIRMATION),
            RETI_TOKEN: getET(EventType.RETIREMENT),
            CENS_TOKEN: getET(EventType.CENSUS),
            SSN_TOKEN: getAT(AttributeType.SSN),
            NATI_TOKEN: getAT(AttributeType.NATIONAL),
            MARB_TOKEN: ET_MARB,
            TITL_TOKEN: ET_TITLE,
            IDNO_TOKEN: ET_IDNO,
            ADDR_TOKEN: ET_ADDR,
            PHON_TOKEN: ET_PHONE,
            WWW_TOKEN: ET_WEBSITE,
            EMAIL_TOKEN: ET_EMAIL,
            DSCR_TOKEN: PHYS_DESCR,
            NCHI_TOKEN: ET_NUM_CHI,
        }


        default_type = token
        if "_" in default_type:
            default_type = default_type.replace("_", " ", -1)
        default_type = default_type.title()

        type = event_mapping.get(token, default_type)

        return type

    def createObjectsList(self, list, func=None, *args):
        if not func: func = self.handleObject

        def do(func, el, *args):
            if isinstance(el, Iterable):
                return func(*el, *args)
            else:
                return func(el, *args)

        newlist = [
            do(func, el, args)
            for el in list
            if el is not None
        ]
        res = [el for el in newlist if el is not None]

        return res

    def format_text(self, text):
        return StyledText(self.parse_html(text))

    def removeControlChars(self, s):
        return ''.join(char for char in s if ord(char) > 31)

    def parse_address(self, data: bytes) -> Optional[MHAddress]:
        # Decode bytes to string
        decoded_text = data
        if not isinstance(data, str):
            decoded_text = data.decode('utf-8', errors='ignore')

        # Split the string by specified ASCII control characters (0-31) and special markers (" and *)
        text_fragments = re.split(r'[\x00-\x1F"*]+', decoded_text)
        text_fragments = [frag for frag in text_fragments if frag]  # Remove empty strings

        # Define expected left markers for each field
        markers = {
            'address': '\x0A',       # Specific left marker for address (LF)
            'address2': '\x12',      # Specific left marker for address2 (DC2)
            'city': '\x1A',          # Specific left marker for city (SUB)
            'state': '"',         # Specific left marker for state (")
            'zip': '*',           # Specific left marker for zip (*)
            'country': '2'           # Specific left marker for country (2)
        }

        # Initialize fields to empty strings
        address = address2 = city = state = zip_code = country = ''

        # Flags to track if a field is already filled
        filled_fields = {
            'address': False,
            'address2': False,
            'city': False,
            'state': False,
            'zip': False,
            'country': False
        }
        contxt = []
        # Helper function to check left marker
        def identify_field(fragment: str, original_text: str) -> str:
            match_position = original_text.find(fragment)
            if match_position == -1:
                return ''  # Fragment not found in the original text, skip

            # Get two chars to the left, or use empty string if out of bounds
            left_context = original_text[max(0, match_position - 2):match_position]

            # Compare left context with the markers to identify the field
            for field, left_marker in markers.items():
                # Check if field has already been filled
                if filled_fields[field]:
                    continue  # Skip if field is already filled

                # Check if surrounding left context matches expected marker for this field
                if left_marker in left_context:
                    # Remove the matched fragment from the original text
                    return field

            return ''


        # Iterate through fragments and identify fields
        for fragment in text_fragments:
            field = identify_field(fragment, decoded_text)
            if field == 'address' and not filled_fields['address']:
                address = fragment
                filled_fields['address'] = True
            elif field == 'address2' and not filled_fields['address2']:
                address2 = fragment
                filled_fields['address2'] = True
            elif field == 'city' and not filled_fields['city']:
                city = fragment
                filled_fields['city'] = True
            elif field == 'state' and not filled_fields['state']:
                if fragment.endswith('2'): fragment = fragment[:-1]
                state = fragment
                filled_fields['state'] = True
            elif field == 'zip' and not filled_fields['zip']:
                if fragment[-1] == '2':
                    fragment = fragment[:-1]
                zip_code = fragment
                filled_fields['zip'] = True
            elif field == 'country' and not filled_fields['country']:
                country = fragment
                filled_fields['country'] = True

            decoded_text = decoded_text.replace(fragment, "", 1)
        
        # Create an instance of MHAddress with the parsed values
        newObj = MHAddress(address, address2, city, state, zip_code, country)
        return newObj

    def parse_custom_date(self, date_str: str) -> DateDTO:
        # Define default values
        quality, modified = 0, 0
        value = None

        if isinstance(date_str, bytes):
            date_str = date_str.decode('utf-16', errors='ignore')
        dateText = date_str  # Default to original text if parsing fails
        # Define mappings for the modifiers and quality indicators
        type_modifiers = {
            "FROM": 5,
            "TO": 5,
            "BET": 4,
            "AND": 4
        }
        precision_modifiers = {
            "EST": (1, "quality"),
            "ABT": (3, "modified"),
            "BEF": (1, "modified"),
            "AFT": (2, "modified"),
            "CAL": (2, "quality")
        }

        # Regex to identify dates and keywords
        date_regex = r"\b(\d{1,2}) ([A-Z]{3}) (\d{4})\b"
        date_regex_one = r"\b([A-Z]{3}) (\d{4})\b"
        date_regex_two = r"\b(\d{4})\b"
        keywords_regex = r"(FROM|TO|BET|AND|EST|ABT|BEF|AFT|CAL)"
        
        # Find all keywords and dates in the string
        keywords = re.findall(keywords_regex, date_str)
        date_matches = re.findall(date_regex, date_str)
        if not date_matches:
            date_matches = re.findall(date_regex_one, date_str)
            date_matches = [tuple(['0', *el]) for el in date_matches]
        if not date_matches:
            date_matches = re.findall(date_regex_two, date_str)
            date_matches = [tuple(['0', '', el]) for el in date_matches]

        # Determine if it’s a timespan by checking for specific keywords
        is_timespan = any(keyword in ["FROM", "TO", "BET", "AND"] for keyword in keywords)
        
        # Determine modified and quality based on keywords
        for keyword in keywords:
            if keyword in type_modifiers:
                modified = max(modified, type_modifiers[keyword])  # Use the highest type modifier
            elif keyword in precision_modifiers:
                modifier_value, modifier_type = precision_modifiers[keyword]
                if modifier_type == "quality":
                    quality = modifier_value
                else:
                    modified = modifier_value
        
        # If it’s a timespan and not exactly two dates found, return original text
        if is_timespan and len(date_matches) != 2:
            return DateDTO(quality, modified, value, dateText)
        
        # Determine the date values if dates were found   
        def dateVal(date_matches):
            def defmonth(mon):
                monthIndex = {
                    "JAN": "01",
                    "FEB": "02",
                    "MAR": "03",
                    "APR": "04",
                    "MAY": "05",
                    "JUN": "06",
                    "JUL": "07",
                    "AUG": "08",
                    "SEP": "09",
                    "OCT": "10",
                    "NOV": "11",
                    "DEC": "12"
                }

                if mon:
                    return datetime.strptime(monthIndex.get(mon), "%m").month
                else:
                    return 0
                
            if len(date_matches) == 1:
                # Single date case
                day1, month1, year1 = date_matches[0]
                day1, month1, year1 = int(day1), defmonth(month1), int(year1)
                return (day1, month1, year1, False)
            elif len(date_matches) == 2:
                # Timespan case
                day1, month1, year1 = date_matches[0]
                day2, month2, year2 = date_matches[1]
                day1, month1, year1 = int(day1), defmonth(month1), int(year1)
                day2, month2, year2 = int(day2), defmonth(month2), int(year2)
                return (day1, month1, year1, False, day2, month2, year2, False)
        
        try:
            value = dateVal(date_matches)
        except Exception as e:
            self.log(e)
            try:
                value = dateVal([date_matches[0]])
            except Exception as e:
                self.log(e)
                value = None

        # If dates were parsed, update dateText with formatted date, else leave as original text
        if value:
            dateText = str(value)
        
        return DateDTO(quality, modified, value, dateText)

    def parse_html(self, html_string):
        html_string = re.sub(r'<\s*br\s*/?>', '\n', html_string, flags=re.IGNORECASE)
        clean_text = re.sub(r'<.*?>', '', html_string)

        return clean_text.strip()
   
    def formatId(self, id, typeObj=""):
        if isinstance(id, tuple):
            id = id[0]
        form = self.prefixesDict.get(typeObj, "")
        return form % id
    
    def find_photos_folder(self):
        path = None
        base_path = self.path
        for folder_name in FTB_PHOTOS_DIRS:
            # Check in lowercase
            lower_folder = os.path.join(base_path, folder_name.lower())
            if os.path.isdir(lower_folder):
                path = lower_folder
            
            # Check in CamelCase
            camel_folder = os.path.join(base_path, folder_name.title())
            if os.path.isdir(camel_folder):
                path = camel_folder
            
            # Check in UPPERCASE
            upper_folder = os.path.join(base_path, folder_name.upper())
            if os.path.isdir(upper_folder):
                path = upper_folder
        
        self.photosPath = path
        return path

    def getMediaPath(self, photo_id: int):
        photos_folder = self.photosPath
        
        if not photos_folder:
            self.log(HINT_GETMEDIA_FLDRNTFND.format(self.path))
            return None
        
        file_prefix = f"P{photo_id}_"
        
        matching_files = [f for f in os.listdir(photos_folder) if f.startswith(file_prefix)]
        
        if not matching_files:
            self.log(HINT_GETMEDIA_FILEIDNTFND.format(photo_id))
            return None
        
        highest_resolution_file = None
        highest_resolution = (0, 0)
        
        for filename in matching_files:
            file_path = os.path.join(photos_folder, filename)
            
            try:
                with Image.open(file_path) as img:
                    resolution = img.size  
                    
                    if resolution > highest_resolution:
                        highest_resolution = resolution
                        highest_resolution_file = file_path
            except Exception as e:
                self.log(HINT_GETMEDIA_ERROR.format(file_path, e))
                continue
        
        # try copy media else return its initial path
        resultFile = None
        if self._doCopyMedia:
            resultFile = self.copyMedia(highest_resolution_file)
        if not resultFile:
            resultFile = highest_resolution_file
        
        return resultFile

    def copyMedia(self, oldPath):
        try:
            mediaFolder = self.userMediaFolder

            if not os.path.exists(mediaFolder):
                os.makedirs(mediaFolder)
                self.log(HINT_COPYMEDIA_NEW_FOLDER.format(mediaFolder))

            fileName = os.path.basename(oldPath)
            newPath = os.path.join(mediaFolder, fileName)

            shutil.copy2(oldPath, newPath)
            return newPath
        except Exception as e:
            self.log(HINT_COPYMEDIA_ERROR.format(e))
            return None

    def formatFetchData(self, dto, arg, findFunc):
        data_list = self.fetchData(((arg,), dto, False))
        if not data_list: return []
        formatted_list = self.formatList(findFunc, data_list)
        return formatted_list

    def formatList(self, add, data_list, reverse=False):
        def do(add, item):
            if reverse:
                return (item, add)
            else: return (add, item)

        res = [do(add, item) for item in data_list]
        return clearNones(res)

    def setupRefList(self, newClass, parent, findFunc, list):
        list = [newClass(*item, parent=parent) for item in list]
        return self.formatList(findFunc, list)

    def tryFind(self, func, pfx, id):
        if not id: return None
        if isinstance(id, tuple):
            id = id[0]
        obj = func(self.formatId(id, pfx))
        if not obj:
            obj = func(f"{pfx}{id:05}")
        if not obj:
            obj = func(f"{id:05}")
        if not obj:
            obj = func(f"{id}")

        return obj

    def tryGetHandle(self, obj):
        try: return obj.get_handle()
        except: return None

    def getTempObj(self, handle):
        for obj, _ in self.compares:
            objHndl = self.tryGetHandle(obj)
            # print(f"Obj: {obj}, hndl: {hnd} vs {handle}, EQ? {hnd}")
            # print(f"hndl: {hnd} vs {handle}, EQ? {hnd}")
            if objHndl == handle:
                # print(f"FOUNDED!!!!!!!!!!")
                return obj
        return None

    def findByIdsAttributes(self, id: str, name: str, attType: str = "GUID", notInDb = False):
        types = {
            "GUID": UID,
            "RIN": RIN
        }
        attType = types.get(attType)
        try:
            if notInDb:
                handles = [obj for obj, _ in self.compares]
            else:
                handles = self.db.method("get_%s_handles", name)()
            for handle in handles:
                if not handle: continue

                if notInDb:
                    obj = handle
                    if type(obj).__name__.lower() != name: continue
                else:
                    obj = self.db.method("get_%s_from_handle", name)(handle)
                uid = self.findObjectByAttributes(
                    obj.get_attribute_list(), 
                    {"type": attType, "value": id.lower()}
                )
                if uid:
                    return obj
            return None
        except Exception as e:
            self.log(HINT_FINDBYID_ERROR.format(name, attType, e))
            return None

    def trySetGrampsId(self, obj, id, idPfx, find=False):
        if not isEmptyOrWhitespace(obj.get_gramps_id()): return None
        if find:
            newId = self.db.method("find_next_%s_gramps_id", type(obj).__name__.lower())()
        else:
            newId = self.formatId(id, idPfx)
        obj.set_gramps_id(newId)
        return newId

    def findObjectByAttributes(self, objects, attributes_dict):
        def lwr(s):
            if isinstance(s, str):
                return s.lower()
            else: return s
        for obj in objects:
            if all(lwr(getattr(obj, key, None)) == value for key, value in attributes_dict.items()):
                return obj
        return None
    
    def getPrefixesFromConfig(self):
        def form(name):
            key = f"preferences.{name}prefix"
            return config.get(key)
        def pfx(form):
            return form.split('%')[0]

        MEDIA_ID_FORM = form("o")
        PERSON_ID_FORM = form("i")
        FAMILY_ID_FORM = form("f")
        EVENT_ID_FORM = form("e")
        PLACE_ID_FORM = form("p")
        NOTE_ID_FORM = form("n")
        CITATION_ID_FORM = form("c")
        SOURCE_ID_FORM = form("s")
        REPOSITORY_ID_FORM = form("r")

        MEDIA_ID_PFX = pfx(MEDIA_ID_FORM)
        PERSON_ID_PFX = pfx(PERSON_ID_FORM)
        FAMILY_ID_PFX = pfx(FAMILY_ID_FORM)
        EVENT_ID_PFX = pfx(EVENT_ID_FORM)
        PLACE_ID_PFX = pfx(PLACE_ID_FORM)
        NOTE_ID_PFX = pfx(NOTE_ID_FORM)
        CITATION_ID_PFX = pfx(CITATION_ID_FORM)
        SOURCE_ID_PFX = pfx(SOURCE_ID_FORM)
        REPOSITORY_ID_PFX = pfx(REPOSITORY_ID_FORM)

        self.prefixesDict = {
            MEDIA_ID_PFX: MEDIA_ID_FORM,
            PERSON_ID_PFX: PERSON_ID_FORM,
            FAMILY_ID_PFX: FAMILY_ID_FORM,
            EVENT_ID_PFX: EVENT_ID_FORM,
            PLACE_ID_PFX: PLACE_ID_FORM,
            NOTE_ID_PFX: NOTE_ID_FORM,
            CITATION_ID_PFX: CITATION_ID_FORM,
            SOURCE_ID_PFX: SOURCE_ID_FORM,
            REPOSITORY_ID_PFX: REPOSITORY_ID_FORM,
        }

    #endregion

    #endregion
    #
    #------------------------------------------------------------------------

class FTBDatabaseHandler:
    def __init__(self, dbPath):
        self.dbPath = dbPath
        self.cursor, self.dbConnection = self.connect_to_database()

    def connect_to_database(self):
        self.dbPath = self.find_ftb_file(self.dbPath)
        if not self.dbPath: raise FileNotFoundError
        conn = sqlite3.connect(self.dbPath, check_same_thread=False)
        conn.text_factory = lambda b: b.decode(errors = 'ignore')
        cursor = conn.cursor()
        return cursor, conn

    def find_ftb_file(self, root_folder: str):
        # if not (FTB_DIR_NAME in root_folder.lower()): return None
        for dirpath, dirnames, filenames in os.walk(root_folder):
            if os.path.basename(dirpath).lower() == FTB_DB_DIR_NAME:
                for filename in filenames:
                    if filename.endswith(FTB_DB_FORMAT):
                        return os.path.join(dirpath, filename)
        return None

    def fetchDbDataDto(self, key, dtoClass, oneRow=True, query=None, keysStr=None):
        if query is None:
            query = dtoClass.query(keysStr)
            
        key = toTuple(key)

        try:
            self.cursor.execute(query, key)
            if oneRow:
                rows = self.cursor.fetchone()
            else:
                rows = self.cursor.fetchall()
            
            if rows:
                if oneRow:
                    objects = dtoClass(*rows)
                else:
                    objects = [dtoClass(*row) for row in rows]
                return objects
            else:
                return None

        except sqlite3.Error as e:
            print(f"Error while executing query: {e}")
            return None

    def fetchDbData(self, params: list, table_name: str, key: str = None) -> list:
        columns = ", ".join(params)
        if key:
            query = f"SELECT {columns} FROM {table_name} WHERE id = %s"
            self.cursor.execute(query, (key,))
        else:
            query = f"SELECT {columns} FROM {table_name}"
            self.cursor.execute(query)
        
        results = self.cursor.fetchall()
        
        return results

    def fetchQuery(self, query, all=False):
        self.cursor.execute(query)
        if all:
            return self.cursor.fetchall()
        else:
            return self.cursor.fetchone()

class FTB_Gramps_sync_options(ToolOptions):
    """Options for FTB_Gramps_sync."""
