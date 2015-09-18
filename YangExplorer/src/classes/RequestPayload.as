/********************************************************************************
 *    Copyright 2015, Cisco Systems, Inc
 *    
 *    Licensed under the Apache License, Version 2.0 (the "License");
 *    you may not use this file except in compliance with the License.
 *    You may obtain a copy of the License at
 *    
 *    http://www.apache.org/licenses/LICENSE-2.0
 *    
 *    Unless required by applicable law or agreed to in writing, software
 *    distributed under the License is distributed on an "AS IS" BASIS,
 *    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *    See the License for the specific language governing permissions and
 *    limitations under the License.
 *    
 *    @author: Pravin Gohite, Cisco Systems, Inc.
 ********************************************************************************/

package classes
{
    public class RequestPayload
    {
        private var protocol : String;
        private var operation : String;
        private var host : String;
        private var platform : String;
        private var port : String;
        private var user : String;
        private var passwd : String;
        private var nc_host : String;
        private var nc_port : String;
        private var nc_user : String;
        private var nc_passwd : String;
        private var rpc : String;
        
        private function _toDeviceString() : String {
            var str : String = '<metadata>'
            str += '<device-auth'
            if (host != '') {
                str += ' platform="' + platform + '"'
                str += ' host="' + host + '"'
                str += ' port="' + port + '"'
                str += ' user="' + user + '"'
                str += ' passwd="' + passwd + '"'
            }
            str += '/>\n'
            str += '<netconf-auth'
            if (nc_host != '') {
                str += ' host="' + nc_host + '"'
                str += ' port="' + nc_port + '"'
                str += ' user="' + nc_user + '"'
                str += ' passwd="' + nc_passwd + '"'
            }
            str += '/>\n';
            str += '</metadata>';
            return str
        }
        
        public function toDeviceString() : String {
            var str : String = '<?xml version="1.0" encoding="UTF-8"?>\n';
            str += '<payload>'
            str += _toDeviceString();
            str += '</payload>'
            return str
        }

        public function toCapString() : String {
            var str : String = '<?xml version="1.0" encoding="UTF-8"?>\n';
            str += '<payload protocol="' + protocol + '">\n'
            str += _toDeviceString();
            str += '</payload>'
            return str;
        }

        public function toString() : String {
            
            var kvStr : String = '';
 
            var str : String = '<?xml version="1.0" encoding="UTF-8"?>\n';
            str += '<payload  protocol="' + protocol + '"'
            str += '>\n'
            str += _toDeviceString();
            str += rpc;
            str += '</payload>'
            return str;
        }
        
        public function RequestPayload()
        {
            reset();
        }
        
        public function reset() : void
        {
            this.protocol = 'netconf'
            this.operation = ''
            this.host = this.nc_host = this.platform = ''
            this.port = this.nc_port = ''
            this.user = this.nc_user = ''
            this.passwd = this.nc_passwd = ''
            this.rpc = null;
        }
        
        public function setRPC(rpc:String) : void {
            this.rpc = rpc;
        }
        
        public function setMode(oper:String) : void {
            this.operation = oper
        }
        
        public function setProtocol(proto:String) : void {
            this.protocol = proto
        }

        public function setDeviceSettings(plat: String, host: String, port : String,
                                          user : String, pwd : String) : void {
            this.platform = plat
            this.host = host
            this.port = port
            this.user = user
            this.passwd = pwd
        }
        
        public function setNetconfSettings(host: String, port : String, user : String, pwd : String) : void {
            this.nc_host = host
            this.nc_port = port
            this.nc_user = user
            this.nc_passwd = pwd
        }
    }
}