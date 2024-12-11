from gramps.gen.lib import *

# class Date:
#     pass
# class StyledText:
#     pass
# class PlaceName:
#     pass

class BaseDTO:
    def __repr__(self, obj=None): 
        """Unified class representation"""
        if not obj: obj = self
        class_name = obj.__class__.__name__
        attrs = ", ".join(f"\n   {key} = {value!r}" for key, value in obj.__dict__.items())
        return f"{class_name}:{attrs}\n"

    def __init__(self, *args, **kwargs):
        attrsDict = self.__annotations__
        attrsList = list(attrsDict.keys())
        for i in range(len(attrsList)):
            att = attrsList[i]
            try:
                attType = attrsDict.get(att)
                setattr(self, att, attType(args[i]))
            except:
                setattr(self, att, getattr(self, att, None))

        for key, val in kwargs.items():
            setattr(self, key, val)

        # print(self)

    def hintKey(self):
        for key in self.__annotations__:    
            return f"{getattr(self, key)}"

    @classmethod
    def query(cls):
        attrs = ", ".join(cls.__annotations__.keys())
        suffix = "_DTO"
        return (f"SELECT {attrs} FROM {cls.__name__.removesuffix(suffix)} WHERE {cls.key} = ?")
    
    @classmethod
    def method(self, obj=None, fmt="", *args):
        """
        TAKEN FROM gramps.gen.db 
        """
        if not obj: obj = self
        return getattr(obj, fmt % tuple([arg.lower() for arg in args]), None)

class individual_main_data_DTO(BaseDTO):
    key = "individual_id"
    individual_id: int
    privacy_level: int
    gender: str
    last_update: int
    create_timestamp: int
    guid: str
    research_completed: int
    token_on_item_id: int

class individual_data_set_DTO(BaseDTO):
    key = "individual_id"
    individual_data_set_id: int

class individual_lang_data_DTO(BaseDTO):
    key = "individual_data_set_id"
    first_name: str
    last_name: str
    prefix: str
    suffix: str
    nickname: str
    religious_name: str
    former_name: str
    married_surname: str
    alias_name: str
    aka: str

class individual_fact_main_data_DTO(BaseDTO):
    key = "individual_id"
    individual_fact_id: int
    token: str
    fact_type: str
    age: str
    sorted_date: int
    lower_bound_search_date: int
    upper_bound_search_date: int
    date: str
    privacy_level: int
    guid: str
    place_id: int
    token_on_item_id: int

class individual_fact_lang_data_DTO(BaseDTO):
    key = "individual_fact_id"
    header: str
    cause_of_death: str

class family_individual_connection_DTO(BaseDTO):
    key = "family_id"
    individual_id: int
    individual_role_type: int

class family_main_data_DTO(BaseDTO):
    key = "family_id"
    family_id: int
    guid: str
    create_timestamp: int
    token_on_item_id: int

class family_fact_lang_data_DTO(BaseDTO):
    key = "family_fact_id"
    header: str

class family_fact_main_data_DTO(BaseDTO):
    key = "family_id"
    family_fact_id: int
    token: str
    fact_type: str
    spouse_age: str
    sorted_date: int
    lower_bound_search_date: int
    upper_bound_search_date: int
    date: str
    privacy_level: int
    guid: str
    place_id: int
    token_on_item_id: int

class media_item_to_item_connection_DTO(BaseDTO):
    key = "external_token_on_item_id"
    media_item_id: int

class media_item_main_data_DTO(BaseDTO):
    key = "media_item_id"
    media_item_id: int
    place_id: int
    guid: str
    sorted_date: int
    lower_bound_search_date: int
    upper_bound_search_date: int
    date: str
    is_privatized: int
    token_on_item_id: int

class media_item_lang_data_DTO(BaseDTO):
    key = "media_item_id"
    title: str
    description: str

class citation_main_data_DTO(BaseDTO):
    key = "external_token_on_item_id"
    citation_id: int
    source_id: int
    page: str
    confidence: int
    sorted_date: int
    lower_bound_search_date: int
    upper_bound_search_date: int
    date: str
    token_on_item_id: int

class citation_lang_data_DTO(BaseDTO):
    key = "citation_id"
    description: str

class source_main_data_DTO(BaseDTO):
    key = "source_id"
    source_id: int
    create_timestamp: int
    repository_id: int
    token_on_item_id: int

class source_lang_data_DTO(BaseDTO):
    key = "source_id"
    title: str
    abbreviation: str
    author: str
    publisher: str
    agency: str
    text: str

class repository_main_data_DTO(BaseDTO):
    key = "repository_id"
    repository_id: int
    phone1: str
    phone2: str
    fax: str
    email: str
    website: str
    token_on_item_id: int

class repository_lang_data_DTO(BaseDTO):
    key = "repository_id"
    name: str
    address: str

class places_lang_data_DTO(BaseDTO):
    key = "place_id"
    place_id: int
    place: str

class note_to_item_connection_DTO(BaseDTO):
    key = "external_token_on_item_id"
    note_id: int

class note_main_data_DTO(BaseDTO):
    key = "note_id"
    note_id: int
    guid: str
    privacy_level: int

class note_lang_data_DTO(BaseDTO):
    key = "note_id"
    note_text: str

class MHAddress(BaseDTO):
    address: str
    address2: str
    city: str
    state: str
    zip: str
    country: str
    parent: object

class AttributeDTO(BaseDTO):
    privacy: int
    type: str
    value: str
    parent: object

    def hintKey(self):
        return f"{self.type}: {self.value}"

class SrcAttributeDTO(AttributeDTO):
    pass

class DateDTO(BaseDTO):
    quality: int
    modified: int
    value: tuple
    dateText: str
    parent: object
    
    def hintKey(self):
        return f"{self.value}"

class UrlDTO(BaseDTO):
    type: str
    path: str
    descr: str
    privacy: int
    parent: object
    
    def hintKey(self):
        return f"{self.type} and {self.path}"

class SurnameDTO(BaseDTO):
    surname: str
    origin: str
    prefix: str
    parent: object

class PersonDTO(BaseDTO):
    gramps_id: str
    privacy: bool
    gender: str
    primary_name: str

class FamilyDTO(BaseDTO):
    gramps_id: str
    privacy: bool

class EventDTO(BaseDTO):
    gramps_id: str
    privacy: bool
    type: str
    date_object: Date
    description: str
    place_handle: str

class NameDTO(BaseDTO):
    first_name: str
    suffix: str
    nick_name: str
    call_name: str

class NoteDTO(BaseDTO):
    gramps_id: str
    privacy: str
    styledtext: StyledText

class CitationDTO(BaseDTO):
    gramps_id: str
    page: str
    confidence_level: int
    date_object: Date

class MediaDTO(BaseDTO):
    gramps_id: str
    path: str
    privacy: bool
    date_object: Date
    description: str
    mime_type: str

class SourceDTO(BaseDTO):
    gramps_id: str
    title: bool
    abbreviation: str
    author: str
    publication_info: str

class RepositoryDTO(BaseDTO):
    gramps_id: str
    name: bool

class PlaceDTO(BaseDTO):
    gramps_id: str
    name: PlaceName

class AddressDTO(BaseDTO):
    street: str
    locality: str
    city: str
    state: str
    postal_code: str
    country: str

class AttributeHandle(BaseDTO):
    def __init__(self, name="Attribute", newVal="-", oldVal="-"):
        self.name = name
        self.newValue = newVal
        self.oldValue = oldVal

class ObjectHandle(BaseDTO):
    def __init__(self, name="Primary Object", commited=False, attributes=list(), secondaryObjects=list(), objRef=None):
        self.name = name
        self.commited = commited
        self.attributes = attributes
        self.secondaryObjects = secondaryObjects
        self.objRef = objRef

class CompareDTO():
    def getAttributes(self, obj) -> dict:
        if not obj: return None

        dtoName = type(obj).__name__ + "DTO"
        dto = globals().get(dtoName, None)

        if not dto: return None
        
        attDict = dict()
        keys = list(dto.__annotations__.keys())
        if "parent" in keys:
            keys.remove("parent")

        for key in keys:
            val = self.getMethod(obj, key)
            val = self.getObjectReprValue(val)
            attDict[key] = str(val)

        return attDict
    
    def getMethod(self, obj, name):
        def mthd(s):
            return BaseDTO.method(obj, s)

        methodName = "get_" + name
        method = mthd(methodName)
        if not method:
            method = mthd(self.nonTypicalMethod(name))

        # print(f"\n\n--------\n{method}\n---------\n\n")
        if method:
            return method()
        else:
            return None

    def nonTypicalMethod(self, name):
        methods = {
            'citation_referene': 'get_reference_handle'
        }
        return methods.get(name, name)
    
    def getObjectReprValue(self, obj):
        cls = type(obj)
        if cls == StyledText:
            return obj.get_string()
        elif cls == Date:
            return obj.get_ymd()
        elif cls == PlaceName:
            return obj.get_value()
        elif cls == Name:
            return obj.get_first_name()
        else:
            return obj