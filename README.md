Import data from MyHeritage Family Tree Builder (FTB) to Gramps

How to install: https://gramps-project.org/wiki/index.php/5.2_Addons#Manually_installed_Addons

How to use

In Gramps navigate to 
"tools" -> "Family Tree Proccesing" -> "FTB to Gramps data transfer".

Than read instruction in addons menu. You will have to choose folder path of your FTB family tree project, which you can get in FTB:
click "File" -> "Manage Projects" -> *select your project* -> click "Go to Folder" button on the right

How it works:
It iterates through each person and transfer all connected to them data
such as Facts, Notes, Media, Citates and so on...
And then iterate through each family transfering its data too and connecting persons.
It tries to find if that object is already in gramps by its id (gramps_id formated to X000N). If object exists it replaces all non referenced values (strings, numbers, etc.) with FTB values, than iterates through objects reference list (attributes, notes, media, etc.) and tries to find it by id or by name and value (attributes, urls) and replace data there, or create new object.
