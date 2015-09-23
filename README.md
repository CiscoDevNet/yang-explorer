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

```bash
   git clone https://github.com/mbj4668/pyang.git
   cd pyang
   [sudo] python setup.py install
```
   - virtualenv (optional, recommended)
```bash
   Ubuntu: sudo apt-get install virtualenv
   MAC: sudo pip install virtualenv
```
   - Browser with latest flash plugin (tested with google chrome)

#####Download and install:
```bash
   git clone https://github.com/CiscoDevNet/yang-explorer.git
   cd yang-explorer
   bash setup.sh
```

```bash
   If you get installation error for missing python.h or xmlversion.h try installing
   dependency packages:
   
   Ubuntu: sudo apt-get install libxml2-dev libxslt1-dev python-dev
```

###3. Running YangExplorer
#####Start Server:
```bash
   cd <install-root>/yang-explorer
   ./start.sh
```

#####Start Explorer:
```bash
   Open http://localhost:8088/static/YangExplorer.html
```

###4. Caveats
   - Yang Model upload fails, Workaround: please use Google Chrome.

###5. User Guide (TBD)

####5.2 Workflow

#####5.2.1 Creating User Account (optional):
   - Click *Admin* button (top right)
   - Login as admin (user: admin, password: admin)
   - On admin page, click *Users* link
   - On User Profiles page, click *Add user* link (top-right)
   - Add user account info and click *Save* (Warning: passwords are transmitted in plaintext)

#####5.2.2 Creating Device Profiles:
   *Note: You can use default user login (guest/guest)*
   - Click *Admin* button (top right)
   - Login login as guest or your your own login
   - On admin page, click *Device profiles* link
   - On User Profiles page, click *Add device profiles* link (top-right)
   - Add device credentials (device login info is not secured)
      - Add device ssh info (Not used currently)
      - Add netconf credentials (Required for connecting to netconf server)
      - Add restconf credentials (Not used currently)
   - click *Save*
   
#####5.2.2 Login:
   YangExplorer uses user accounts to manage workspaces. You can create a user account using admin
   page (See 5.2.1 Creating User Account)

   You can use guest login (guest/guest) or newly created account.

   ![alt tag](https://github.com/CiscoDevNet/yang-explorer/blob/master/docs/images/YangExplorer.png)

#####5.2.2 Exploring Models:

   You can explore yang models in explorer area (left pane) using tree navigation:
   
   ![alt tag](https://github.com/CiscoDevNet/yang-explorer/blob/master/docs/images/explorer.png)
   
#####5.2.3 Adding Yang Models:
   - Click *Manage* tab
   
   ![alt tag](https://github.com/CiscoDevNet/yang-explorer/blob/master/docs/images/manage.png)

#####5.2.4 Creating RPCs (TBD):
   - Value and Operation coloumns in explorer area are editable.
   - Explorer a model
   - Click value cell next to data node (leaf, container etc)
   - Edit values
   - Click *RPC* button

#####5.2.5 Executing RPCs (TBD):

#####5.2.6 Managing Collections (TBD):
