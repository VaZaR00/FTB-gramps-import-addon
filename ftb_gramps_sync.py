#------------------------------------------------------------------------
#
# python modules
#
#------------------------------------------------------------------------
import mimetypes
import threading
import time
from typing import Optional
from constants import *
from ftb_dto import *
import sqlite3
import re
import os
from datetime import datetime
from PIL import Image
from collections.abc import Iterable
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

#------------------------------------------------------------------------
#
# gramps modules "C:/Users/Саша/Documents/MyHeritage/mh-db-test"
#
#------------------------------------------------------------------------
from gramps.gen.db import DbTxn
from gramps.gen.db.base import DbWriteBase
from gramps.gui.managedwindow import ManagedWindow
from gramps.gen.lib import *
from gramps.gen.utils.id import create_id
from gramps.gui.plug.tool import BatchTool, ToolOptions


#region Helpers
def isEmptyOrWhitespace(s):
    return not s or s.strip() == ""

def getValFromMap(data_map, search_key, indx):
    for tupl in data_map:
        if tupl[0] == search_key:
            return tupl[indx]
    return None
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
    def __init__(self, assistant, tryConnect):
        super().__init__(assistant)
        
        self.tryConnect = tryConnect

        label = Gtk.Label(label=MENU_LBL_PATH_TEXT)
        label.set_line_wrap(True)
        label.set_use_markup(True)
        label.set_max_width_chars(60)
        self.pack_start(label, False, False, 0)
        
        self.file_chooser = Gtk.FileChooserButton(
            title=MENU_LBL_CHOOSE_FILE, 
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        self.file_chooser.set_width_chars(50)
        self.file_chooser.connect("file-set", self.on_file_selected)
        self.pack_start(self.file_chooser, False, False, 5)

        self.file_path_label = Gtk.Label(label="")
        self.pack_start(self.file_path_label, False, False, 5)

        self.folder_error = Gtk.Label(label="")
        self.pack_start(self.folder_error, False, False, 5)

        self.selected_file_path = None
        self._complete = False

        self.show_all()

    def on_file_selected(self, widget):
        """File selector handler."""
        self.show_folder_error(False)
        path = widget.get_filename() 
        self.selected_file_path = path
        self.file_path_label.set_text(f"Selected: {path}")
        
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
        self.path = None # File path chosen by user
        self.toCommit = []  # Log entries
        self.logs = []  # Log entries
        self.processing_complete = False
        self.createGUI()

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
        
        self.intro_page = IntroductionPage(self.assistant)
        self.add_page(self.intro_page, Gtk.AssistantPageType.INTRO, MENU_LBL_INTRO_TITLE)

        self.file_sel_page = FileSelectorPage(self.assistant, self.tryConnectSQLdb)
        self.add_page(self.file_sel_page, Gtk.AssistantPageType.CONTENT, MENU_LBL_PATH_TITLE)

        self.progress_page = ProgressPage(self.assistant)
        self.add_page(self.progress_page, Gtk.AssistantPageType.PROGRESS, MENU_LBL_PROGRESS_TITLE)

        self.finish_page = FinishPage(self.assistant)
        self.add_page(self.finish_page, Gtk.AssistantPageType.SUMMARY, MENU_LBL_FINISH_TITLE)
    
        self.show()
        self.assistant.set_forward_page_func(self.forward_page, None)

    def prepare(self, assistant, page: Page):
        """Run page preparation code."""
        page.update_complete()
        if page == self.progress_page:
            if self.connectedToFTBdb:
                t = threading.Thread(target=self.proccesAsync)
                t.start()
            else:
                self.assistant.previous_page()
        elif page == self.file_sel_page:
            pass
        else:
            page.set_complete()

    def proccesAsync(self):
        self.log(HINT_PROCCESING)
        time.sleep(2) # temporary, to let next page load
        GLib.idle_add(self.start_processing)
        self.progress_page.set_complete()

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
    
    def forward_page(self, page, data):
        """Specify the next page to be displayed."""

        return page + 1

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
    def start_processing(self):
        """Start the backend processing."""
        try:
            self.log(f"Succesfully connected to db: '{self.path}'")
            self.log(f"db: '{self.dbHandler.cursor}'")
            with DbTxn(f"FTB:GRAMPS:SYNC", self.db) as trans:   
                self.trans = trans
                self.run()
        except Exception as e:
            self.log(f"Something went wrong: {e}")
            self.cancelChanges()
            raise e
        
        self.dbState.signal_change()

    def run(self):
        allPersonsIds = self.dbHandler.fetchDbData(["individual_id"], "individual_main_data")
        allFamiliesIds = self.dbHandler.fetchDbData(["family_id"], "family_main_data")

        for id in allPersonsIds:
            self.handleObject(self.findPerson, id, False, False)

        for id in allFamiliesIds:
            self.handleObject(self.findFamily, id, False, False)

        self.log(HINT_PROCCES_DONE)
        self.processing_complete = True

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
        name = objClass.__name__.lower()
        exists = bool(obj)
        if not exists:
            obj = objClass()
            try:
                obj.set_handle(create_id())
            except:
                pass
        try:
            new = modify(obj, data)
        except Exception as e:
            new = None
            self.log(f"\nSomething went wrong while proccesing {name} object ({obj}). Error: {e}")

        if not new:
            if not keepEmpty: return None 
            new = obj

        self.clearEmptyAttributes(new)
        self.grampsDbMethod(obj, name, "add_%s")
        self.grampsDbMethod(new, name)
        
        self.log(f"Object '{name}' ({obj}) commited. Time: {datetime.now()}")

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
            mainDto, langDto = FamilyFactMainDataDTO, FamilyFactLangDataDTO
            id_name = "family_fact_id"
        else: 
            mainDto, langDto = IndividualFactMainDataDTO, IndividualFactLangDataDTO
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
                urls.append((self.findURL, UrlDTO((0, factName), text, "", 0, parent)))
            elif token in NOTE_TYPES:
                if token == DSCR_TOKEN: 
                    obj: MHAddress = self.parse_address(langData.header)
                    text = NOTE_PHYS_DESCR.format(obj.address, obj.address2, obj.city, obj.state, obj.zip, obj.country)
                noteMain = NoteMainDataDTO(factId, fact.guid, fact.privacy_level)
                noteLang = NoteLangDataDTO(text)
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
            method(obj, self.trans)

    def setFamilyMembers(self, family: Family, familyId):
        membersConnections: tuple[FamilyIndividualConnectionDTO] = self.fetchData((familyId, FamilyIndividualConnectionDTO, False))
        for member in membersConnections:
            id = member.individual_id
            role = member.individual_role_type
            person: Person = self.tryFind(self.db.get_person_from_gramps_id, PERSON_ID_PFX, id)

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
            
            self.grampsDbMethod(person, type(person).__name__.lower())

    def cancelChanges(self):
        self.db.undo()
    #endregion

    #region Find objects in gramps
    def findPerson(self, id):
        if not id: return None, self.modifyPerson, Person, None
        person = self.tryFind(self.db.get_person_from_gramps_id, PERSON_ID_PFX, id)
        mainData, dataSets = self.fetchData((id, IndividualMainDataDTO), (id, IndividualDataSetDTO, False))
        langData = [self.fetchData(((dataSet.individual_data_set_id, ), IndividualLangDataDTO)) for dataSet in dataSets]
        return person, self.modifyPerson, Person, (mainData, langData)

    def findFamily(self, id):
        family = self.tryFind(self.db.get_family_from_gramps_id, FAMILY_ID_PFX, id)
        data = self.fetchData((id, FamilyMainDataDTO))
        return family, self.modifyFamily, Family, data

    def findEvent(self, data):
        if not data: return None, self.modifyPerson, Person, None
        mainData, langData = data
        if isinstance(mainData, IndividualFactMainDataDTO):
            eventParentType = PERSON_ID_PFX
            id = mainData.individual_fact_id
            pfx = PERSON_EVENT_ID_PFX
        else:
            eventParentType = FAMILY_ID_PFX
            id = mainData.family_fact_id
            pfx = FAMILY_EVENT_ID_PFX

        event = self.tryFind(self.db.get_event_from_gramps_id, pfx, id)
        if not event:
            event = self.tryFind(self.db.get_event_from_gramps_id, EVENT_ID_PFX, id)

        mainData.__setattr__("parentType", eventParentType)

        return event, self.modifyEvent, Event, data

    def findName(self, data: IndividualLangDataDTO):
        name = None
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
        parent = getattr(data, "parent", None)
        if parent:
            attribute = self.findObjectByAttributes(
                parent.get_attribute_list(),
                {"type": data.type, "value": data.value}
            )
            if isinstance(parent, (Citation, Source)):
                attClass = SrcAttribute

        return attribute, self.modifyAttribute, attClass, data

    def findNote(self, data: tuple[NoteToItemConnectionDTO, tuple[NoteMainDataDTO, NoteLangDataDTO]]):
        if not data: return None, self.modifyPerson, Person, None
        id, _data = data
        if not isinstance(id, int):
            id = id.note_id
        note = self.tryFind(self.db.get_note_from_gramps_id, NOTE_ID_PFX, id)
        if not _data:
            _data = self.fetchData((id, NoteMainDataDTO, True), (id, NoteLangDataDTO))
        return note, self.modifyNote, Note, _data

    def findCitation(self, mainData: CitationMainDataDTO):
        citation = self.tryFind(self.db.get_citation_from_gramps_id, CITATION_ID_PFX, mainData.citation_id)
        langData = self.fetchData((mainData.citation_id, CitationLangDataDTO))
        return citation, self.modifyCitation, Citation, (mainData, langData)

    def findMedia(self, id):
        if not id: return None, self.modifyPerson, Person, None
        id = id.media_item_id
        media = self.tryFind(self.db.get_media_from_gramps_id, MEDIA_ID_PFX, id)
        data = self.fetchData((id, MediaItemMainDataDTO), (id, MediaItemLangDataDTO))
        return media, self.modifyMedia, Media, data

    def findSource(self, id):
        source = self.tryFind(self.db.get_source_from_gramps_id, SOURCE_ID_PFX, id)
        data = self.fetchData((id, SourceMainDataDTO), (id, SourceLangDataDTO))
        return source, self.modifySource, Source, data

    def findRepository(self, id):
        repository = self.tryFind(self.db.get_repository_from_gramps_id, REPOSITORY_ID_PFX, id)
        data = self.fetchData((id, RepositoryMainDataDTO), (id, RepositoryLangDataDTO))
        return repository, self.modifyRepository, Repository, data

    def findDate(self, data: DateDTO):
        date = None
        parent = getattr(data, "parent", None)
        if parent:
            date = self.findObjectByAttributes(
                [parent.date],
                {"dateval": data.value}
            )

        return date, self.modifyDate, Date, data

    def findURL(self, data: UrlDTO):
        url = None
        parent = getattr(data, "parent", None)
        if parent:
            url = self.findObjectByAttributes(
                parent.get_url_list(),
                {"type": data.type, "path": data.path}
            )
            
        return url, self.modifyURL, Url, data

    def findAddress(self, data: MHAddress):
        address = None
        parent = getattr(data, "parent", None)
        if parent:
            address = self.findObjectByAttributes(
                parent.get_address_list(),
                {"street": data.address}
            )
            
        return address, self.modifyAddress, Address, data

    def findPlace(self, id):
        place = self.tryFind(self.db.get_place_from_gramps_id, PLACE_ID_PFX, id)
        data = self.fetchData((id, PlaceLangDataDTO))
        return place, self.modifyPlace, Place, data
    #endregion

    #region Modify objects
    def modifyPerson(self, person: Person, data: tuple[IndividualMainDataDTO, list[IndividualLangDataDTO]]):
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
            (privacy, UID, mainData.guid),
            (privacy, RES_C, mainData.research_completed)
        ]
        
        events, attributes, urls, addresses, notes = self.unpackFacts(mainData.individual_id, PERSON_ID_PFX, person)
        attributes = defaultAttributes + attributes
        media = self.formatFetchData(MediaItemToItemConnectionDTO, mainData.token_on_item_id, self.findMedia)
        citations = self.formatFetchData(CitationMainDataDTO, mainData.token_on_item_id, self.findCitation)
        
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

        self.trySetGrampsId(person, mainData.individual_id, PERSON_ID_PFX)
        person.set_privacy(privacy)
        person.set_gender(gender)
        person.set_primary_name(primary_name)
        for name in newNames:
            person.add_alternate_name(name)
        for attribute in newAttributes:
            person.add_attribute(attribute)
        for event in newEvents:
            person.add_event_ref(self.addObjRef(EventRef, event))
        for citation in newCitations:
            person.add_citation(citation.get_handle())
        for media in newMedia:
            person.add_media_reference(self.addObjRef(MediaRef, media))
        for note in newNotes:
            person.add_note(note.get_handle())
        for url in newUrls:
            person.add_url(url)
        for address in newAddresses:
            person.add_address(address)

        return person

    def modifyFamily(self, family: Family, data: FamilyMainDataDTO):
        mainData = data
        if not mainData: return None

        privacy = False

        defaultAttributes = [
            (False, CRT, mainData.create_timestamp)
        ]
        
        events, attributes, urls, addresses, notes = self.unpackFacts(mainData.family_id, FAMILY_ID_PFX, family)
        attributes = defaultAttributes + attributes
        media = self.formatFetchData(MediaItemToItemConnectionDTO, mainData.token_on_item_id, self.findMedia)
        citations = self.formatFetchData(CitationMainDataDTO, mainData.token_on_item_id, self.findCitation)
        
        newAttributes = self.createObjectsList(
            self.setupRefList(AttributeDTO, family, self.findAttribute, attributes)
        )
        newEvents = self.createObjectsList(events)
        newCitations = self.createObjectsList(citations)
        newMedia = self.createObjectsList(media)
        newNotes = self.createObjectsList(notes) + self.getNotes(mainData.token_on_item_id)

        self.trySetGrampsId(family, mainData.family_id, FAMILY_ID_PFX)
        family.set_privacy(privacy)
        for attribute in newAttributes:
            family.add_attribute(attribute)
        for event in newEvents:
            family.add_event_ref(self.addObjRef(EventRef, event))
        for citation in newCitations:
            family.add_citation(citation.get_handle())
        for media in newMedia:
            family.add_media_reference(self.addObjRef(MediaRef, media))
        for note in newNotes:
            family.add_note(note.get_handle())

        self.setFamilyMembers(family, mainData.family_id)

        return family

    def modifyEvent(self, event: Event, data: tuple):
        mainData, langData = data
        if not (mainData and langData): return None

        privacy = bool(mainData.privacy_level)
        eventParentType = getattr(mainData, "parentType")
        if eventParentType == PERSON_ID_PFX:
            attributes = [
                (privacy, UID, mainData.guid),
                (privacy, PERSON_AGE, mainData.age),
                (privacy, CAUSE_DEAT, langData.cause_of_death)
            ]
            id = mainData.individual_fact_id
            pfx = PERSON_EVENT_ID_PFX
        else:
            attributes = [
                (privacy, UID, mainData.guid),
                (privacy, SPOUSE_AGE, mainData.spouse_age)
            ]
            id = mainData.family_fact_id
            pfx = FAMILY_EVENT_ID_PFX

        eventType = self.defineEventType(mainData.token, mainData.fact_type)
        date = self.extract_date(mainData)
        description = langData.header
        causeOfDeat = getattr(langData, "cause_of_death", None)
        if not isEmptyOrWhitespace(causeOfDeat) and causeOfDeat: 
            description = description + f" {CAUSE_DEAT}: " + causeOfDeat
        
        place = self.handleObject(self.findPlace, mainData.place_id, True, False)
        if place:
            if place.get_name(): 
                place = place.get_handle() 
        else: place = ""

        media = self.formatFetchData(MediaItemToItemConnectionDTO, mainData.token_on_item_id, self.findMedia)
        newNotes = self.getNotes(mainData.token_on_item_id)
        newAttributes = self.createObjectsList(
            self.setupRefList(AttributeDTO, event, self.findAttribute, attributes)
        )
        newCitations = []
        newMedia = self.createObjectsList(media)

        self.trySetGrampsId(event, id, pfx)
        event.set_privacy(privacy)
        event.set_type(eventType)
        event.set_date_object(date)
        event.set_description(description)
        event.set_place_handle(place)
        for attribute in newAttributes:
            event.add_attribute(attribute)
        for citation in newCitations:
            event.add_citation(citation.get_handle())
        for media in newMedia:
            event.add_media_reference(self.addObjRef(MediaRef, media))
        for note in newNotes:
            event.add_note(note.get_handle())

        return event

    def modifyName(self, name: Name, data: IndividualLangDataDTO):
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
        for surname in surnames:
            if not isEmptyOrWhitespace(surname.get_surname()):
                name.add_surname(surname)

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
    
    def modifyNote(self, note: Note, data: tuple[NoteMainDataDTO, NoteLangDataDTO]):
        mainData, langData = data
        if not (mainData and langData): return None

        self.trySetGrampsId(note, mainData.note_id, NOTE_ID_PFX)
        note.set_privacy(bool(mainData.privacy_level))
        note.set_styledtext(self.format_text(langData.note_text))
        return note

    def modifyCitation(self, citation: Citation, data: tuple[CitationMainDataDTO, CitationLangDataDTO]):
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
        for attribute in attributes:
            citation.add_attribute(attribute)
        for note in notes:
            citation.add_note(note.get_handle())

        source = self.handleObject(self.findSource, mainData.source_id, True, False)
        if source:
            citation.set_reference_handle(source.get_handle())

        return citation
    
    def modifyMedia(self, media: Media, data: tuple[MediaItemMainDataDTO, MediaItemLangDataDTO]):
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
                    (prvt, UID, mainData.guid),
                    (prvt, DESCR, langData.description)
                ]
            )
        )

        media.set_path(path)
        self.trySetGrampsId(media, mediaId, MEDIA_ID_PFX)
        media.set_privacy(prvt)
        media.set_date_object(self.extract_date(mainData))
        media.set_description(langData.title)
        for attribute in attributes:
            media.add_attribute(attribute)
        for note in notes:
            media.add_note(note.get_handle())
        # deal with mime types
        value = mimetypes.guess_type(media.get_path())
        if value and value[0]:  # found from filename
            media.set_mime_type(value[0])

        return media

    def modifySource(self, source: Source, data: tuple[SourceMainDataDTO, SourceLangDataDTO]):
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
            self.formatFetchData(MediaItemToItemConnectionDTO, mainData.token_on_item_id, self.findMedia)
        )
        
        self.trySetGrampsId(source, mainData.source_id, SOURCE_ID_PFX)
        source.set_title(langData.title)
        source.set_abbreviation(langData.abbreviation)
        source.set_author(langData.author)
        source.set_publication_info(langData.publisher)
        for attribute in attributes:
            source.add_attribute(attribute)
        for note in notes:
            source.add_note(note.get_handle())
        for media in medias:
            source.add_media_reference(self.addObjRef(MediaRef, media))

        repo: Repository = self.handleObject(self.findRepository, mainData.repository_id, True, False)
        if repo:
            newRepoRef = self.addObjRef(RepoRef, repo)
            repoRefs = source.get_reporef_list()
            if not any(rr.ref == newRepoRef.ref for rr in repoRefs):
                source.add_repo_reference(newRepoRef)

        return source

    def modifyRepository(self, repo: Repository, data: tuple[RepositoryMainDataDTO, RepositoryLangDataDTO]):
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

    def modifyPlace(self, place: Place, data: PlaceLangDataDTO):
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
                        self.fetchData(((id,), NoteToItemConnectionDTO, False)),
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
            print(f"DECODING")
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
            # contxt.append(f"\nFRAG: {fragment} -> |{left_context}|")

            # Compare left context with the markers to identify the field
            for field, left_marker in markers.items():
                # Check if field has already been filled
                if filled_fields[field]:
                    continue  # Skip if field is already filled

                # Check if surrounding left context matches expected marker for this field
                if left_marker in left_context:
                    # Remove the matched fragment from the original text
                    # print(f"ORIG_TXT: {original_text}")
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
        # print(f"\nTEXT: {decoded_text}\nFRAGS: {text_fragments}\nCONTEXTS: {contxt}\nADDRESS: {newObj}")
        return newObj

    def parse_custom_date(self, date_str: str) -> DateDTO:
        # Define default values
        quality, modified = 0, 0
        value = None
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
        keywords_regex = r"(FROM|TO|BET|AND|EST|ABT|BEF|AFT|CAL)"
        
        # Find all keywords and dates in the string
        keywords = re.findall(keywords_regex, date_str)
        date_matches = re.findall(date_regex, date_str)

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
            if len(date_matches) == 1:
                # Single date case
                day1, month1, year1 = date_matches[0]
                day1, month1, year1 = int(day1), datetime.strptime(month1, "%b").month, int(year1)
                return (day1, month1, year1, False)
            elif len(date_matches) == 2:
                # Timespan case
                day1, month1, year1 = date_matches[0]
                day2, month2, year2 = date_matches[1]
                day1, month1, year1 = int(day1), datetime.strptime(month1, "%b").month, int(year1)
                day2, month2, year2 = int(day2), datetime.strptime(month2, "%b").month, int(year2)
                return (day1, month1, year1, False, day2, month2, year2, False)
        
        try:
            value = dateVal(date_matches)
        except:
            try:
                value = dateVal([date_matches[0]])
            except:
                value = None

        # If dates were parsed, update dateText with formatted date, else leave as original text
        if value:
            dateText = str(value)
        
        return DateDTO(quality, modified, value, dateText)

    def parse_html(self, html_string):
        html_string = re.sub(r'<\s*br\s*/?>', '\n', html_string, flags=re.IGNORECASE)
        clean_text = re.sub(r'<.*?>', '', html_string)

        return clean_text.strip()
   
    def formatId(self, id, typeObj="", num=DEFAULT_NUM_OF_ZEROS_ID):
        if isinstance(id, tuple):
            id = id[0]
        return f"{typeObj}{id:0{num}}"
    
    def getMediaPath(self, photo_id: int):
        #helper func
        def find_photos_folder(base_path):
            for folder_name in FTB_PHOTOS_DIRS:
                # Check in lowercase
                lower_folder = os.path.join(base_path, folder_name.lower())
                if os.path.isdir(lower_folder):
                    return lower_folder
                
                # Check in CamelCase
                camel_folder = os.path.join(base_path, folder_name.title())
                if os.path.isdir(camel_folder):
                    return camel_folder
                
                # Check in UPPERCASE
                upper_folder = os.path.join(base_path, folder_name.upper())
                if os.path.isdir(upper_folder):
                    return upper_folder
            
            return None
        
        photos_folder = find_photos_folder(self.path)
        
        if not photos_folder:
            print(f"Media folder not found.")
            return None
        
        file_prefix = f"P{photo_id}_"
        
        matching_files = [f for f in os.listdir(photos_folder) if f.startswith(file_prefix)]
        
        if not matching_files:
            print(f"File with ID={photo_id} not found.")
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
                print(f"Error while working with file {file_path}: {e}")
                continue
        
        return highest_resolution_file

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
        return [el for el in res if el is not None]

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
    
    def trySetGrampsId(self, obj, id, idPfx):
        newId = self.formatId(id, idPfx)

        obj.set_gramps_id(newId)

    def findObjectByAttributes(self, objects, attributes_dict):
        for obj in objects:
            if all(getattr(obj, key, None) == value for key, value in attributes_dict.items()):
                return obj
        return None
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

    def fetchDbDataDto(self, key, dtoClass, oneRow=True, query=None):
        if query is None:
            query = dtoClass().query
            
        if not isinstance(key, tuple):
            key = (key, )

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

class FTB_Gramps_sync_options(ToolOptions):
    """Options for FTB_Gramps_sync."""
