Copyright 2015, Cisco Systems, Inc

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

###1. Description
   An open-source Yang Browser and RPC Builder Application

###2. Installation
#####Prerequisite:
   - MAC, Linux, (not verified on Windows)
   - python 2.7
   - pip package manager (https://pip.pypa.io/en/stable/installing/)
   - pyang (https://github.com/mbj4668/pyang)
   - (optional, recommended) virtualenv
   - Browser with latest flash plugin (tested with google chrome)

#####Download and install:
   - (optional, recommended) Create and Activate virtual env
   - git clone https://github.com/CiscoDevNet/yang-explorer.git
   - cd yang-explorer
   - pip install -r requirements.txt

###3. Running YangExplorer
#####Start Server:
   - cd <install-root>/yangx
   - ./start.sh

#####Start Explorer:
   - Open http://localhost:8088/static/YangExplorer.html

###4. User Guide (TBD)
#####Login:
      (optional: you may create a local user account for yang explorer by clicking 'Admin' button
      Admin Login: username: admin, password: admin  (Use for admin stuffs e.g. adding user accounts)
      Guest Login: username: guest, password: guest  (Default user)

#####UI Description:
   **Buttons:**
   - 'Admin' -> Opens admin page, which allows you to create user accounts, device profiles
   - 'Refresh' -> Refresh YangExplorer content without reloading page
   - 'Reset' -> Clears explorer tree content
   - 'Login' -> User Logins
      
