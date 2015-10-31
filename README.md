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
   [sudo] bash setup.sh

   Note: sudo may be required if you do not use virtualenv.
```

```bash
   If you get installation error for missing python.h or xmlversion.h try installing
   dependency packages:
   
   Ubuntu: sudo apt-get install libxml2-dev libxslt1-dev python-dev
```

###3. Running YangExplorer
###3.1 Running with localhost
#####Start Server:
```bash
   cd <install-root>/yang-explorer
   [sudo] ./start.sh

   Note: sudo may be required if you did not use virtualenv during installation.
```

#####Start Explorer:
```bash
   http://localhost:8088/static/YangExplorer.html
```
###3.2 Running with ip-address
#####Start Server:
```bash
   cd <install-root>/yang-explorer
   
   vim ./start.sh
   (replace localhost with ip-address)
   
   [sudo] ./start.sh

   Note: sudo may be required if you did not use virtualenv during installation.
```

#####Start Explorer:
```bash
   cd <install-root>/yang-explorer/server/static
   vim YangExplorer.html
   
   Add ip-address/port in YangExplorer.html after following line:
      
      var flashvars = {}; 

+     flashvars.host = '1.2.3.4'; 
+     flashvars.port = '8088';

   http://localhost:8088/static/YangExplorer.html
```

###4. Caveats
   - Yang Model upload fails, Workaround: Use Google Chrome.

###5. User Guide (TBD)

####5.2 Admin Tasks

#####5.2.1 Creating User Account (optional):

   Creating user account is optional as you can use default guest/guest login, however creating user account can be userful
   if you have a shared yang-explorer installtion.
   
   - Click **Admin** button in YangExplorer
   - Login as admin (user: admin, password: admin)
   - On admin page, click **Users** link
   - On User Profiles page, click **Add user** link (top-right)
   - Add user account info and click **Save** (Warning: passwords are transmitted in plaintext)

#####5.2.2 Creating Device Profiles:

Device profiles can be created to quickly populate device info from drop-down list in yang-explorer.

   *Note: You can use default user login (guest/guest)*
   - Click **Admin** button in YangExplorer
   - Login login as guest or your own login
   - On admin page, click *Device profiles* link
   - On User Profiles page, click *Add device profiles* link (top-right)
   - Add device credentials (device login info is not secured)
      - Add netconf credentials (Required for connecting to netconf server)
      - Add restconf credentials (Not used currently)
   - click *Save*

#####5.2.3 Creating Collection:

Collections can be used to save user generated RPCs on the server so that saved RPCs can be re-used.

   *Note: You can use default user login (guest/guest)*
   - Click **Admin** button in YangExplorer
   - Login login as guest or your own login
   - On admin page, click **Collections** link
   - On User Profiles page, click *Add collection* link (top-right)
      - Provide collection name
      - Select User from drop-down box
      - Provide description for this collection
   - click **Save**
   
####5.3 Work Flow

#####5.3.1 Login:
   YangExplorer uses user accounts to manage workspaces. You can create a user account using admin
   page (See 5.2.1 Creating User Account)

   You can use guest login (guest/guest) or newly created account.
   ![alt tag](https://github.com/CiscoDevNet/yang-explorer/blob/master/docs/images/YangExplorer.png)

#####5.3.2 Exploring Models:

#####5.3.3 Adding/Deleing Yang Models:
###### Upload using yang-explorer user interface
   ![alt tag](https://github.com/CiscoDevNet/yang-explorer/blob/master/docs/images/manage.png)
   - Click **Manage** tab
   - Click **Upload** button
      - Click **Browse** and select models to upload
      - Click *Upload*
      - **Clear** button can be used clear models in upload window
   - Click Subscribe & Un-subscribe buttons to make selected models visible/invisible in exploerer area
   - Click Delete button to delete selected models from user account

###### Upload using server console

```bash
   cd <install-root>/yang-explorer
   source v/bin/activate
   cd server
   python manage.py --user <username> --git <git-url> --dir <path/to/yang/models>
   
   example: local upload (assumes models are already available at dir path)
   python manage.py bulkupload --user guest --dir /users/prgohite/git/yang/vendor/cisco/xr/531
   
   example: git upload
   python manage.py bulkupload --user guest --git https://github.com/YangModels/yang.git --dir vendor/cisco/xr/531
```
   All models must be compiled successfully, in case of any error none of the models will be uploaded to yang-explorer.
   
#####5.3.4 Creating RPCs:

   You can explore yang models in explorer area (left pane) using tree navigation:
   ![alt tag](https://github.com/CiscoDevNet/yang-explorer/blob/master/docs/images/explorer.png)
   
   - Value and Operation columns in explorer area are editable.
   - Explore model in explorer area by navigating model tree
   - Click value cell next to data node (leaf, container etc)
   - Edit values
      - Select &lt;get&gt; and &lt;get-config&gt; for get, get-config netconf operations
      - Select &lt;rpc&gt; for RPCs
      - Enter data values for edit-config operation
      - Use **Reset** button on top-right bar to reset data in the model tree
   - Click **RPC** button

#####5.3.5 Executing RPCs:
   - Create RPC using *5.3.4*
   - Populate Device info in Device Settings Tab
   - Click **Run**

#####5.3.6 Saving RPCs to Collection:
   - Create RPC using *5.3.4*
   - Click **Save**

#####5.3.7 Loading saved RPC:
   - Click **Collections** Tab
   - Double click on the RPCs title you want to load.
