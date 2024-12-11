Import data from [MyHeritage Family Tree Builder (FTB)](https://www.myheritage.com/family-tree-builder) to Gramps.
### You can download FTB and sync your tree from [MyHeritage](https://www.myheritage.com) site and transfer it to Gramps.

Addon reads local SQLite file of FTB project DB and **doesn't overwrite it!**

# [How to install](https://gramps-project.org/wiki/index.php/5.2_Addons#Manually_installed_Addons)

# How to use

In Gramps navigate to
"Tools" -> "Family Tree Proccesing" -> "FTB to Gramps data transfer".

![navigate_gramps](https://github.com/user-attachments/assets/19c1a56c-2604-43d3-8312-aba574b7f3b5)

![warning](https://github.com/user-attachments/assets/e58936bf-600e-4bf0-8f7d-2b7043626e36)

Than read instruction in addons menu.

![menu_intro](https://github.com/user-attachments/assets/856a8e04-c964-4b88-b318-e6d03c0fd14e)

You will have to choose folder path of your FTB family tree project and you can manage some options

![menu_file](https://github.com/user-attachments/assets/5ba69a8a-063d-415e-ad5c-64e776e6482a)

Which you can get in FTB:
"File" -> "Manage Projects"

![ftb_manage](https://github.com/user-attachments/assets/97b030ac-9b92-4efa-99b6-2a7d1bdb55ce)

_select your project_ -> click "Go to Folder" button 

![ftb_select](https://github.com/user-attachments/assets/2a494412-edce-4c2f-b4ae-e9ab4830ce84)

Than you can manage what data you want to import by checking "Commit" flag

![handle](https://github.com/user-attachments/assets/67d00082-fdb5-469f-b329-97f484b720e8)

# How it works
It reads local SQLite database file of FTB project.
It iterates through each person in FTB database and transfer all connected to them data
such as Facts, Notes, Media, Citates and so on...
And then iterate through each family in FTB database transfering its data too and connecting persons.
It tries to find if that object is already in gramps by its _UID attribute for Person, Family, Event, Media and id (gramps_id formated to X000N) for other objects.
If object exists and you "Commited" it in "Handle Chnages" tab it replaces all non referenced values (strings, numbers, etc.) with FTB values, than iterates through objects reference list (attributes, notes, media, etc.) and tries to find it by id or by name and value (attributes, urls) and replace data there, or create new object.
