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
   An open-source Yang Browser and RPC Builder Application to experiment with Yang Data Models
   
   **Features**
   - Upload / Compile yang models from User Interface Or Command Line
   - Build NetConf RPC
   - Generate Python example code **[new]**
   - Search yang xpaths **[new]**
   - Execute RPC against real netconf server
   - Save created RPCs to collections for later use
   - Build dependency graph for models
   - Browse data model tree and inspect yang properties
   
   This application is under Beta mode, contributions / suggestions are welcome !!

#####Screenshots:
   ![alt tag](https://github.com/CiscoDevNet/yang-explorer/blob/master/docs/images/explorer.png)
   ![alt tag](https://github.com/CiscoDevNet/yang-explorer/blob/master/docs/images/graph.png)
   ![alt tag](https://github.com/CiscoDevNet/yang-explorer/blob/master/docs/images/script.png)

###2. Installation
####2.1 First time installation
#####Prerequisite:
   - MAC, Linux (not supported on Windows)
   - python 2.7
   - pip package manager (https://pip.pypa.io/en/stable/installing/)
```bash
   If already installed, make sure that pip / setuptools are upto date (commands may vary)
   
   pip install --upgrade pip
   
   Ubuntu: sudo pip install --upgrade setuptools
```
   - virtualenv (recommended)
```bash
   Ubuntu: sudo apt-get install virtualenv
   Fedora: sudo dnf install python-virtualenv
   MAC: sudo pip install virtualenv
```
   - graphviz (http://www.graphviz.org/Download.php)
```bash
   Ubuntu: sudo apt-get install graphviz
   Fedora: sudo dnf install graphviz
   MAC: brew install graphviz
```
   - Browser with latest flash plugin (tested with google chrome)

#####Download and install:
```bash
   git clone https://github.com/CiscoDevNet/yang-explorer.git
   cd yang-explorer
   [sudo] bash setup.sh

   Note: sudo may be required if you do not use virtualenv.
```
   See section 6 Troubleshooting for more:
```bash
   If you get installation error for missing python.h or xmlversion.h try installing
   dependency packages:
   
   Ubuntu: sudo apt-get install libxml2-dev libxslt1-dev python-dev zlib1g-dev
   Fedora: sudo dnf install libxml2-devel libxslt-devel python-devel zlib-devel
```
####2.2 Update exising installtion

```bash
  cd <install-root>/yang-explorer
  git stash (if you have local changes)
  git pull origin
  git stash apply (if you have local changes)
  bash setup.sh
```

###3. Running YangExplorer
####3.1 Running with localhost
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
####3.2 Running with ip-address (Shared server)
#####Start Server:
```bash
   # Determine <ip-address> using if-config
   
   # Add ip-address/port in YangExplorer.html after following line:
   cd <install-root>/yang-explorer/server/static
      vi YangExplorer.html
      var flashvars = {}; 
+     flashvars.host = '<ip-address>';
+     flashvars.port = '8088';

   # save & quit

   # Update ip-address in startup script
      cd <install-root>/yang-explorer
      vi start.sh
      (update HOST variable with <ip-address>)
   # save & quit
      
   ./start.sh

   Note: sudo may be required if you did not use virtualenv during installation.
```

#####Start Explorer:
```bash
   http://<ip-address>:8088/static/YangExplorer.html
```

###4. Caveats
   - Yang Model upload fails, Workaround: Use Google Chrome.
   - See section 6 Troubleshooting for more:

###5. User Guide (TBD)

####5.1 Work Flow

#####5.2.1 Login:
   YangExplorer uses user accounts to manage workspaces. You can create a user account using admin page (See 5.3.1 Creating User Account) or use the predefined login (guest/guest). You must login (click on the Login button on top right corner)

   You can use guest login **(guest/guest)** or newly created account.
   ![alt tag](https://github.com/CiscoDevNet/yang-explorer/blob/master/docs/images/YangExplorer.png)

#####5.2.2 Adding/Deleing Yang Models:
###### Upload using yang-explorer user interface (TBD: screen shot is out-of-date)
   ![alt tag](https://github.com/CiscoDevNet/yang-explorer/blob/master/docs/images/manage.png)
   - Click **Manage Models** tab
   - Click **Workspace** tab
   - Click **Add** button
      - Click **Browse** and select models to upload
      - Click *Upload*
      - **Clear** button can be used clear models in upload window
   - Click Subscribe & Un-subscribe buttons to make selected models visible/invisible in explorer area
   - Click Delete button to delete selected models from user account

###### Sync from Device
   - Click **Manage Models** tab
   - Click **Device** tab
      - Select a device from profile list
         - YangExplorer will list yang models on device
      - Select models to Sync to YangExplorer Workspace
      - **Sync** button to Sync Models to YangExplorer
      - You may encounter these error during sync:
         - Missing models: Select missing models from the list and try sync again
         - Duplicate models: In workspace tab, select duplicate models and delete
   - Click **Workspace** tab
   - Click Subscribe & Un-subscribe buttons to make selected models visible/invisible in explorer area
   - Click Delete button to delete selected models from user account

###### Upload models using server console

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
   
#####5.2.3 Generating the model dependency graph:
   - Click **Manage Models** tab
   - Click **Workspace** tab
      - Select one or more model name to get dependency graph
      - If no models are selected, all subscribed model will be used to generate graph
   - Click Graph buttons to generate graph

#####5.2.4 Creating RPCs:
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

   - Click **RPC** button under **Build** tab

#####5.2.5 Executing RPCs:
   - Create RPC using *5.2.4*
   - Populate Device info in Device Settings Tab
   - Click **Run** button under **Build** tab
   
   Yang Explorer uses ncclient library to execute RPCs, connection timeout can be configured via
   environment varible default timout value is 45 seconds. 
```
   #update value in start.sh & restart server
   export NCCLIENT_TIMEOUT=120
```

##### 5.2.6 Generating Python example:
   - Create a netconf / xml RPC
    - Create RPC using *5.2.4*
    - (OR) Provide custom netconf XML (Click custom RPC Checkbox)

   - Click **Script** button under **Build** tab
   - Click **Copy** button to copy generated code into system clipboard
   - Save content as a python script (say example.py)
   - Run python script from command line using given instruction in script header comments.
 
##### 5.2.7 Saving RPCs to Collection:
   - Create RPC using *5.2.4*
   - Click **Save** button under **Build** tab

#####5.2.7 Loading saved RPC:
   - Click **Collections** Tab
   - Double click on the RPCs title you want to load.

####5.3 Admin Tasks 

#####5.3.1 Creating User Account (optional):

   Creating user account is optional as you can use default guest/guest login, however creating user account can be userful
   if you have a shared yang-explorer installation.
   
   - Click **Admin** button in YangExplorer
   - Login as admin (user: admin, password: admin)
   - On admin page, click **Users** link
   - On User Profiles page, click **Add user** link (top-right)
   - Add user account info and click **Save** (Warning: passwords are transmitted in plaintext)

#####5.3.2 Creating Device Profiles:

Device profiles can be created to quickly populate device info from drop-down list in yang-explorer.

   *Note: You can use default user login (guest/guest)*
   - Click **"Create device profile"** link on **Build -> Device Settings**
   - (OR) Click **"Create device profile"** link on **Manage Models -> Device**
   - (OR) Click **Admin** button in YangExplorer
      - Login login as guest or your own login
      - On admin page, click *Device profiles* link
   - On User Profiles page, click *Add device profiles* link (top-right)
   - Add device credentials (device login info is not secured)
      - Add netconf credentials (Required for connecting to netconf server)
      - Add restconf credentials (Not used currently)
   - click *Save*
   - 

#####5.3.3 Creating Collection:

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

###6 Troubleshooting
####6.1 Installation
#####6.1.1 error for missing python.h or xmlversion.h
   - Ubuntu: sudo apt-get install libxml2-dev libxslt1-dev python-dev
   - Mac : xcode-select --install

#####6.1.2 django.db.utils.OperationalError: near "񐁂򐁇N": syntax error
   - http://stackoverflow.com/questions/33270297/django-db-utils-operationalerror-near-n-syntax-error

#####6.1.3 After install if you are not able to login using guest/guest try one of the following
   - mv server/data/db.sqlite3 server/data/db.sqlite3_backup
   - bash setup.sh
   In end of setup.sh script log you should see something like this -
```bash
      ...
      Creating default users ..
      Copying default models ..
      Setup completed.. 
      
      Use start.sh to start yang-explorer server
```

####6.2 Yang Model Upload
#####6.2.1 Failure during upload of yang model
   - Chrome browser is required currently to upload models using User Interface
   - Please see failure message, if dependent models are missing you will see specific error in message window.

   


