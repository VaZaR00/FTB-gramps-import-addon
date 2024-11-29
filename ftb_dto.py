class BaseRepr:
    def __repr__(self, obj=None):
        """Unified class representation"""
        if not obj or obj == None: obj = self
        class_name = obj.__class__.__name__
        attrs = ", ".join(f"\n   {key} = {value!r}" for key, value in obj.__dict__.items())
        return f"{class_name}:{attrs}\n"

class IndividualMainDataDTO(BaseRepr):
    query = """
        SELECT individual_id, privacy_level, gender, last_update, create_timestamp, 
               guid, research_completed, token_on_item_id
        FROM individual_main_data
        WHERE individual_id = ?
    """

    def __init__(self, individual_id, privacy_level, gender, last_update, create_timestamp, guid, research_completed, token_on_item_id):
        self.individual_id = individual_id
        self.privacy_level = privacy_level
        self.gender = gender
        self.last_update = last_update
        self.create_timestamp = create_timestamp
        self.guid = guid
        self.research_completed = bool(research_completed)
        self.token_on_item_id = token_on_item_id

class IndividualDataSetDTO(BaseRepr):
    query = """
        SELECT individual_data_set_id
        FROM individual_data_set
        WHERE individual_id = ?
    """

    def __init__(self, individual_data_set_id):
        self.individual_data_set_id = individual_data_set_id

class IndividualLangDataDTO(BaseRepr):
    query = """
        SELECT first_name, last_name, prefix, suffix, nickname, religious_name, former_name, 
               married_surname, alias_name, aka
        FROM individual_lang_data
        WHERE individual_data_set_id = ?
    """

    def __init__(self, first_name, last_name, prefix, suffix, nickname, religious_name, former_name, 
                 married_surname, alias_name, aka):
        self.first_name = first_name
        self.last_name = last_name
        self.prefix = prefix
        self.suffix = suffix
        self.nickname = nickname
        self.religious_name = religious_name
        self.former_name = former_name
        self.married_surname = married_surname
        self.alias_name = alias_name
        self.aka = aka

class IndividualFactMainDataDTO(BaseRepr):
    query = """
        SELECT individual_fact_id, token, fact_type, age, sorted_date, lower_bound_search_date, 
            upper_bound_search_date, date, privacy_level, guid, place_id, token_on_item_id
        FROM individual_fact_main_data
        WHERE individual_id = ?
    """

    def __init__(self, individual_fact_id, token, fact_type, age, sorted_date, lower_bound_search_date, upper_bound_search_date, date, privacy_level, guid, place_id, token_on_item_id):
        self.individual_fact_id = individual_fact_id
        self.token = token
        self.fact_type = fact_type
        self.age = age
        self.sorted_date = sorted_date
        self.lower_bound_search_date = lower_bound_search_date
        self.upper_bound_search_date = upper_bound_search_date
        self.date = date
        self.privacy_level = privacy_level
        self.guid = guid
        self.place_id = place_id
        self.token_on_item_id = token_on_item_id

class IndividualFactLangDataDTO(BaseRepr):
    query = """
        SELECT header, cause_of_death
        FROM individual_fact_lang_data
        WHERE individual_fact_id = ?
    """

    def __init__(self, header, cause_of_death=None):
        self.header = header
        self.cause_of_death = cause_of_death

class FamilyIndividualConnectionDTO(BaseRepr):
    query = """
        SELECT individual_id, individual_role_type
        FROM family_individual_connection
        WHERE family_id = ?
    """

    def __init__(self, individual_id, individual_role_type):
        self.individual_id = individual_id
        self.individual_role_type = individual_role_type

class FamilyMainDataDTO(BaseRepr):
    query = """
        SELECT family_id, guid, create_timestamp, token_on_item_id
        FROM family_main_data
        WHERE family_id = ?
    """

    def __init__(self, family_id, guid, create_timestamp, token_on_item_id):
        self.family_id = family_id
        self.guid = guid
        self.create_timestamp = create_timestamp
        self.token_on_item_id = token_on_item_id

class FamilyFactLangDataDTO(BaseRepr):
    query = """
        SELECT header
        FROM family_fact_lang_data
        WHERE family_fact_id = ?
    """

    def __init__(self, header):
        self.header = header

class FamilyFactMainDataDTO(BaseRepr):
    query = """
        SELECT family_fact_id, token, fact_type, spouse_age, sorted_date, lower_bound_search_date, 
        upper_bound_search_date, date, privacy_level, guid, place_id, token_on_item_id
        FROM family_fact_main_data
        WHERE family_id = ?
    """

    def __init__(self, family_fact_id, token, fact_type, spouse_age, sorted_date, lower_bound_search_date, 
                 upper_bound_search_date, date, privacy_level, guid, place_id, token_on_item_id):
        self.family_fact_id = family_fact_id
        self.token = token
        self.fact_type = fact_type
        self.spouse_age = spouse_age
        self.sorted_date = sorted_date
        self.lower_bound_search_date = lower_bound_search_date
        self.upper_bound_search_date = upper_bound_search_date
        self.date = date
        self.privacy_level = privacy_level
        self.guid = guid
        self.place_id = place_id
        self.token_on_item_id = token_on_item_id

class MediaItemToItemConnectionDTO(BaseRepr):
    query = """
        SELECT media_item_id
        FROM media_item_to_item_connection
        WHERE external_token_on_item_id = ?
    """

    def __init__(self, media_item_id):
        self.media_item_id = media_item_id

class MediaItemMainDataDTO(BaseRepr):
    query = """
        SELECT media_item_id, place_id, guid, sorted_date, lower_bound_search_date, 
               upper_bound_search_date, date, is_privatized, token_on_item_id
        FROM media_item_main_data
        WHERE media_item_id = ?
    """

    def __init__(self, media_item_id, place_id, guid, sorted_date, lower_bound_search_date, 
                 upper_bound_search_date, date, is_privatized, token_on_item_id):
        self.media_item_id = media_item_id
        self.place_id = place_id
        self.guid = guid
        self.sorted_date = sorted_date
        self.lower_bound_search_date = lower_bound_search_date
        self.upper_bound_search_date = upper_bound_search_date
        self.date = date
        self.is_privatized = is_privatized
        self.token_on_item_id = token_on_item_id

class MediaItemLangDataDTO(BaseRepr):
    query = """
        SELECT title, description
        FROM media_item_lang_data
        WHERE media_item_id = ?
    """

    def __init__(self, title, description):
        self.title = title
        self.description = description

class CitationMainDataDTO(BaseRepr):
    query = """
        SELECT citation_id, source_id, page, confidence, sorted_date, lower_bound_search_date, 
               upper_bound_search_date, date, token_on_item_id
        FROM citation_main_data
        WHERE external_token_on_item_id = ?
    """

    def __init__(self, citation_id, source_id, page, confidence, sorted_date, lower_bound_search_date, 
                 upper_bound_search_date, date, token_on_item_id):
        self.citation_id = citation_id
        self.source_id = source_id
        self.page = page
        self.confidence = confidence
        self.sorted_date = sorted_date
        self.lower_bound_search_date = lower_bound_search_date
        self.upper_bound_search_date = upper_bound_search_date
        self.date = date
        self.token_on_item_id = token_on_item_id

class CitationLangDataDTO(BaseRepr):
    query = """
        SELECT description
        FROM citation_lang_data
        WHERE citation_id = ?
    """

    def __init__(self, description):
        self.description = description

class SourceMainDataDTO(BaseRepr):
    query = """
        SELECT source_id, create_timestamp, repository_id, token_on_item_id
        FROM source_main_data
        WHERE source_id = ?
    """

    def __init__(self, source_id, create_timestamp, repository_id, token_on_item_id):
        self.source_id = source_id
        self.create_timestamp = create_timestamp
        self.repository_id = repository_id
        self.token_on_item_id = token_on_item_id

class SourceLangDataDTO(BaseRepr):
    query = """
        SELECT title, abbreviation, author, publisher, agency, text
        FROM source_lang_data
        WHERE source_id = ?
    """

    def __init__(self, title, abbreviation, author, publisher, agency, text):
        self.title = title
        self.abbreviation = abbreviation
        self.author = author
        self.publisher = publisher
        self.agency = agency
        self.text = text

class RepositoryMainDataDTO(BaseRepr):
    query = """
        SELECT repository_id, phone1, phone2, fax, email, website, token_on_item_id
        FROM repository_main_data
        WHERE repository_id = ?
    """

    def __init__(self, repository_id, phone1, phone2, fax, email, website, token_on_item_id):
        self.repository_id = repository_id
        self.phone1 = phone1
        self.phone2 = phone2
        self.fax = fax
        self.email = email
        self.website = website
        self.token_on_item_id = token_on_item_id

class RepositoryLangDataDTO(BaseRepr):
    query = """
        SELECT name, address
        FROM repository_lang_data
        WHERE repository_id = ?
    """

    def __init__(self, name, address):
        self.name = name
        self.address = address

class PlaceLangDataDTO(BaseRepr):
    query = """
        SELECT place_id, place
        FROM places_lang_data
        WHERE place_id = ?
    """

    def __init__(self, place_id, place):
        self.place_id = place_id
        self.place = place

class NoteToItemConnectionDTO(BaseRepr):
    query = """
        SELECT note_id
        FROM note_to_item_connection
        WHERE external_token_on_item_id = ?
    """

    def __init__(self, note_id):
        self.note_id = note_id

class NoteMainDataDTO(BaseRepr):
    query = """
        SELECT note_id, guid, privacy_level
        FROM note_main_data
        WHERE note_id = ?
    """

    def __init__(self, note_id, guid, privacy_level):
        self.note_id = note_id
        self.guid = guid
        self.privacy_level = privacy_level

class NoteLangDataDTO(BaseRepr):
    query = """
        SELECT note_text
        FROM note_lang_data
        WHERE note_id = ?
    """

    def __init__(self, note_text):
        self.note_text = note_text

class MHAddress(BaseRepr):
    def __init__(self, address: str, address2: str, city: str, state: str, zip_code: str, country: str, parent=None):
        self.address = str(address)
        self.address2 = str(address2)
        self.city = str(city)
        self.state = str(state)
        self.zip = str(zip_code)
        self.country = str(country)
        self.parent =str( parent)

class AttributeDTO(BaseRepr):
    def __init__(self, privacy, type, value, parent=None):
        self.privacy = privacy
        self.type = type
        if value:
            self.value = str(value)
        else:
            self.value = ""
        self.parent = parent

class DateDTO(BaseRepr):
    def __init__(self, quality, modified, value, dateText, parent=None):
        self.quality = quality
        self.modified = modified
        self.value = value
        self.dateText = str(dateText)
        self.parent = parent

class UrlDTO(BaseRepr):
    def __init__(self, type, path, descr="", privacy=0, parent=None):
        self.type = type
        self.path = path
        self.descr = descr
        self.privacy = privacy
        self.parent = parent

class SurnameDTO(BaseRepr):
    def __init__(self, surname, origin="", prefix="", parent=None):
        self.surname = surname
        self.origin = origin
        self.prefix = prefix
        self.parent = parent
