Import data from MyHeritage Family Tree Builder (FTB) to Gramps

[How to install](https://gramps-project.org/wiki/index.php/5.2_Addons#Manually_installed_Addons)

How to use:

In Gramps navigate to 
"tools" -> "Family Tree Proccesing" -> "FTB to Gramps data transfer". 
![navigate_gramps](https://github.com/user-attachments/assets/19c1a56c-2604-43d3-8312-aba574b7f3b5)
![warning](https://github.com/user-attachments/assets/e58936bf-600e-4bf0-8f7d-2b7043626e36)

Than read instruction in addons menu. 
![instruction](https://github.com/user-attachments/assets/72eac2ab-e892-4578-af1c-9d0431e3f8c6)

You will have to choose folder path of your FTB family tree project
![ftb_select](https://github.com/user-attachments/assets/d9115a26-b308-4e63-8e16-ed8a3ce3f736)

Which you can get in FTB:
click "File" -> "Manage Projects"
![ftb_manage](https://github.com/user-attachments/assets/97b030ac-9b92-4efa-99b6-2a7d1bdb55ce)

*select your project* -> click "Go to Folder" button on the right
![ftb_select](https://github.com/user-attachments/assets/2a494412-edce-4c2f-b4ae-e9ab4830ce84)

How it works:
It iterates through each person in FTB database and transfer all connected to them data
such as Facts, Notes, Media, Citates and so on...
And then iterate through each family in FTB database transfering its data too and connecting persons.
It tries to find if that object is already in gramps by its id (gramps_id formated to X000N). 
If object exists it replaces all non referenced values (strings, numbers, etc.) with FTB values, than iterates through objects reference list (attributes, notes, media, etc.) and tries to find it by id or by name and value (attributes, urls) and replace data there, or create new object.
