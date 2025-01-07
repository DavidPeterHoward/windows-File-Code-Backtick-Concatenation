# Windows File/Folder Concatenation Including Absolute/Relative Filenames and Backticks code language

Purpose of this application is to facilliate code uploads to web-based LLMs like ChatGPT and Claude as a simple solution to providing a limited number of files. 

### Installation

```bash
# Create .exe 
pyinstaller file_concatenator.spec
```

```ps1
# Add to Windows context menu
./Install-ExeContextMenu.ps1
```

### Testing
```bash
pytest
```

### Uninstallation from Context Menu
```ps1
./Cleanup-Registry.ps1
```




```
file_concatenator.py
├── .gitignore
├── Cleanup-OldRegistry.ps1
├── file_concatenator.ico
├── file_concatenator.py
├── file_concatenator.svg
├── Install-ExeContextMenu.ps1
├── Install-PythonContextMenu.ps1
├── interface.png
├── pytest.ini
├── README.md
├── requirements-test.txt
├── requirements.txt
├── test_file_concatenator.py

```

![Interface of application](interface.png)