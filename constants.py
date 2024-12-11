from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext

# Constants for menu labels and content
MENU_TITLE = _("FTB to Gramps data transfer")

MENU_LBL_INTRO_TITLE = _("Introduction")
MENU_LBL_INTRO_TEXT = _("""
This tool transfers data from MyHeritage Family Tree Builder (FTB).\n
It iterates through each person and transfer all connected to them data
such as Facts, Notes, Media, Citates and so on...
And then iterate through each family transfering its data too and connecting persons.\n
On next page please select folder of your FTB project.\n
You can get its path in FTB program by: \n
click "File" -> "Manage Projects" -> select your project -> click "Go to Folder" button on the right \n
\n
\n
For more info go to GitHub: 
https://github.com/VaZaR00/FTB-gramps-import-addon
""")

MENU_LBL_PATH_TITLE = _("FTB Project path")
MENU_LBL_PATH_TEXT = _("Please select the FTB project path.")
MENU_LBL_PATH_SELECTED = _("Path selected: {}")
MENU_LBL_CHOOSE_FILE = _("Choose folder")
MENU_LBL_CHK_REPLACE = _("Replace data for {}")
MENU_LBL_TIP_REPLACE = _("If true it try to find if {} object is already exists in gramps and then replace its data with new imported else it wil create new (might duplicate)")
MENU_LBL_CHK_COPYMEDIA = _("Copy media")
MENU_LBL_TIP_COPYMEDIA = _("Copy media to user media folder path")

MENU_LBL_PROGRESS_TITLE = _("Progress")
MENU_LBL_PROGRESS_TEXT = _("Processing is ongoing. Please wait...")

MENU_LBL_HDNLCHNG_TITLE = _("Handle changes")
MENU_LBL_HDNLCHNG_TEXT = _("Handle gramps changes")
MENU_LBL_HDNLCHNG_TABLE_NAME = _("Name")
MENU_LBL_HDNLCHNG_TABLE_NEW = _("New value")
MENU_LBL_HDNLCHNG_TABLE_OLD = _("Old value")
MENU_LBL_HDNLCHNG_TABLE_COMMIT = _("Commit")
MENU_LBL_HDNLCHNG_TABLE_COMMIT_ALL = _("Commit All")
MENU_LBL_HDNLCHNG_TABLE_FOLD_ALL = _("Fold All")
MENU_LBL_HDNLCHNG_TABLE_UNFOLD_ALL = _("Unfold All")

MENU_LBL_FINISH_TITLE = _("Completion")
MENU_LBL_FINISH_TEXT = _("The process is complete. You can now close the assistant.")

MENU_LBL_HIDDEN_CONT_ERROR_FILE_SEL = _("Folder is not selected or there is no Database!")

# progress page hints
HINT_PROCCESING = _("Please wait...\n\nProgram might freeze for some time\n\nProcessing started...")
HINT_PROCCES_DONE_S = _("\nFTB to Gramps transfer done successfuly!")
HINT_PROCCES_DONE_W = _("\nFTB to Gramps transfer done with some problems. Please read logs for more information.")
HINT_PROCCES_CONNTODB = _("Succesfully connected to db: '{}'")
HINT_PROCCES_ERROR = _("\nSomething went wrong: {} \n")

HINT_HANDLEOBJ_ERROR = _("\nERROR! Something went wrong while proccesing {} object ({}). \nDTO: {} \nError: {} \n")
HINT_HANDLEOBJ_COMMIT = _("Object '{}' ({}) commited. Time: {}")
HINT_HANDLEOBJ_EXIST = _("Object '{}' founded in Gramps by key '{}': {}")
HINT_HANDLEOBJ_DONTEXISTS = _("Object '{}' not found in Gramps by key '{}'. New created.")

HINT_GETMEDIA_FLDRNTFND = _("Media folder not found in {}.")
HINT_GETMEDIA_FILEIDNTFND = _("File with ID={} not found.")
HINT_GETMEDIA_ERROR = _("\nERROR! while working with file {}: {} \n")
HINT_COPYMEDIA_NEW_FOLDER = _("User media folder ({}) does not exists so new folder created")
HINT_COPYMEDIA_ERROR = _("\nERROR! while trying to copy media: {} \n")

HINT_FINDBYID_ERROR = _("\nERROR! while trying to find {} by {}: {}\n")

# Attributes and facts names
UID = "_UID"
CRT = "_CRT"
UPD = "_UPD"
RIN = "RIN"
EMAIL = "E-mail"
WEBSITE = _("Website")
FAX = "FAX"
DESCR = _("Description" )
PHYS_DESCR = _("Physical description")
RES_C = _("Research completed")
PERSON_AGE = _("Person age")
SPOUSE_AGE = _("Spouse age")
CAUSE_DEAT = _("Cause of Death")
AGENCY = _("Agency")
SRC_TEXT = _("Source text")
PHON_NUM = _("Phone number")

ET_MARB = _("Marriage Banns")
ET_HASSID = _("Hassidism")
ET_ENGA = _("Engagement")
ET_TITLE = _("Identification title")
ET_ADDR = _("Address")
ET_PHONE = _("Phone")
ET_NUM_CHI = _("Known number of childs")
ET_IDNO = _("ID Number")
ET_WEBSITE = WEBSITE
ET_EMAIL = EMAIL

# "Physical description" note structure
NOTE_PHYS_DESCR = _("""
Height: {}
Weight: {}
Hair color: {}
Eye color: {}
Description: {}
Medical: {}
""")


# global config variables
FTB_DIR_NAME = "myheritage"
FTB_DB_DIR_NAME = "database"
FTB_PHOTOS_DIRS = ["photos"]
FTB_DB_FORMAT = '.ftb'

NUMBER_OF_TRY_FIND_ID = 10
DEFAULT_NUM_OF_ZEROS_ID = 4
DEFAULT_NUM_OF_ZEROS_ID_MH = 6

# Default prefixes
# It will get user settled preferences in progress this is just defaults
MEDIA_ID_PFX = "O"
PERSON_ID_PFX = "I"
FAMILY_ID_PFX = "F"
EVENT_ID_PFX = "E"
FAMILY_EVENT_ID_PFX = EVENT_ID_PFX
PERSON_EVENT_ID_PFX = EVENT_ID_PFX
PLACE_ID_PFX = "P"
NOTE_ID_PFX = "N"
CITATION_ID_PFX = "C"
SOURCE_ID_PFX = "S"
REPOSITORY_ID_PFX = "R"
# Default id formation
MEDIA_ID_FORM = "O%04d"
PERSON_ID_FORM = "I%04d"
FAMILY_ID_FORM = "F%04d"
EVENT_ID_FORM = "E%04d"
PLACE_ID_FORM = "P%04d"
NOTE_ID_FORM = "N%04d"
CITATION_ID_FORM = "C%04d"
SOURCE_ID_FORM = "S%04d"
REPOSITORY_ID_FORM = "R%04d"

# Fact tokens in FTB db
ET_MH_TOKEN = "MYHERITAGE:"
ET_REL_PRFX = "REL_"
DEAT_TOKEN = "DEAT"
BIRT_TOKEN = "BIRT"
EDUC_TOKEN = "EDUC"
OCCU_TOKEN = "OCCU"
NATI_TOKEN = "NATI"
NCHI_TOKEN = "NCHI"
NATU_TOKEN = "NATU"
TITL_TOKEN = "TITL"
RESI_TOKEN = "RESI"
RELI_TOKEN = "RELI"
RETI_TOKEN = "RETI"
ADDR_TOKEN = "ADDR"
PHON_TOKEN = "PHON"
WWW_TOKEN = "WWW"
EMAIL_TOKEN = "EMAIL"
SSN_TOKEN = "SSN"
DSCR_TOKEN = "DSCR"
BURI_TOKEN = "BURI"
BARM_TOKEN = "BARM"
BASM_TOKEN = "BASM"
BAPM_TOKEN = "BAPM"
CHRA_TOKEN = "CHRA"
ORDN_TOKEN = "ORDN"
CONF_TOKEN = "CONF"
CENS_TOKEN = "CENS"
NMR_TOKEN = "NMR"
MARR_TOKEN = "MARR"
MARB_TOKEN = "MARB"
ENGA_TOKEN = "ENGA"
FCOM_TOKEN = "FCOM"
IDNO_TOKEN = "IDNO"
WILL_TOKEN = "WILL"
PROP_TOKEN = "PROP"
PROB_TOKEN = "PROB"
DIV_TOKEN = "DIV"
DIVF_TOKEN = "DIVF"
HASSID_TOKEN = "HASSIDUT"
DEAT_TOKEN_FILTER_VAL = "Y"

# EVENT_TYPES = [DEAT_TOKEN, BIRT_TOKEN, EDUC_TOKEN, OCCU_TOKEN, BURI_TOKEN, MARR_TOKEN, DIV_TOKEN]
NOTE_TYPES = [DSCR_TOKEN]
ADDRESS_TYPES = [ADDR_TOKEN]
URL_TYPES = [WWW_TOKEN, PHON_TOKEN, EMAIL_TOKEN]
ATTRIBUTE_TYPES = [NATI_TOKEN, NCHI_TOKEN, TITL_TOKEN, IDNO_TOKEN, SSN_TOKEN]
