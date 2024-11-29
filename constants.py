FTB_DIR_NAME = "myheritage"
FTB_DB_DIR_NAME = "database"
FTB_PHOTOS_DIRS = ["photos"]
FTB_DB_FORMAT = '.ftb'

NUMBER_OF_TRY_FIND_ID = 10
DEFAULT_NUM_OF_ZEROS_ID = 4

UID = "_UID"
CRT = "_CRT"
UPD = "_UPD"
DESCR = "Description" 
PHYS_DESCR = "Physical description" 
RES_C = "Research completed"
PERSON_AGE = "Person age"
SPOUSE_AGE = "Spouse age"
CAUSE_DEAT = "Cause of Death"
AGENCY = "Agency"
SRC_TEXT = "Source text"
PHON_NUM = "Phone number"
EMAIL = "E-mail"
WEBSITE = "Website"
FAX = "FAX"

MEDIA_ID_PFX = "O"
PERSON_ID_PFX = "I"
FAMILY_ID_PFX = "F"
EVENT_ID_PFX = "E"
FAMILY_EVENT_ID_PFX = "EF"
PERSON_EVENT_ID_PFX = "EI"
PLACE_ID_PFX = "P"
NOTE_ID_PFX = "N"
CITATION_ID_PFX = "C"
SOURCE_ID_PFX = "S"
REPOSITORY_ID_PFX = "R"

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

ET_MARB = "Marriage Banns"
ET_HASSID = "Hassidism"
ET_ENGA = "Engagement"
ET_TITLE = "Identification title"
ET_ADDR = "Address"
ET_PHONE = "Phone"
ET_NUM_CHI = "Known number of childs"
ET_IDNO = "ID Number"
ET_WEBSITE = WEBSITE
ET_EMAIL = EMAIL

# EVENT_TYPES = [DEAT_TOKEN, BIRT_TOKEN, EDUC_TOKEN, OCCU_TOKEN, BURI_TOKEN, MARR_TOKEN, DIV_TOKEN]
NOTE_TYPES = [DSCR_TOKEN]
ADDRESS_TYPES = [ADDR_TOKEN]
URL_TYPES = [WWW_TOKEN, PHON_TOKEN, EMAIL_TOKEN]
ATTRIBUTE_TYPES = [NATI_TOKEN, NCHI_TOKEN, TITL_TOKEN, IDNO_TOKEN, SSN_TOKEN]

NOTE_PHYS_DESCR = """
Height: {}
Weight: {}
Hair color: {}
Eye color: {}
Description: {}
Medical: {}
"""


HINT_PROCCESING = "Please wait...\n\nProgram might freeze for some time\n\nProcessing started..."
HINT_PROCCES_DONE = "\nFTB to Gramps transfer done successfuly!"

# Constants for menu labels and content
MENU_TITLE = "FTB to Gramps data transfer"

MENU_LBL_INTRO_TITLE = "Introduction"
MENU_LBL_INTRO_TEXT = """
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
"""

MENU_LBL_PATH_TITLE = "FTB Project path"
MENU_LBL_PATH_TEXT = "Please select the FTB project path."
MENU_LBL_CHOOSE_FILE = "Choose folder"

MENU_LBL_PROGRESS_TITLE = "Progress"
MENU_LBL_PROGRESS_TEXT = "Processing is ongoing. Please wait..."

MENU_LBL_FINISH_TITLE = "Completion"
MENU_LBL_FINISH_TEXT = "The process is complete. You can now close the assistant."

MENU_LBL_HIDDEN_CONT_ERROR_FILE_SEL = "Folder is not selected or there is no Database!"