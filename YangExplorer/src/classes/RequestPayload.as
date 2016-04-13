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
    import mx.collections.ArrayCollection;
    
    public class RequestPayload
    {
        private var protocol : String;
        private var operation : String;
        private var source : String;
        private var target : String;
        private var base_config : String;
        private var verify_config : String;
        private var reset_config : String
        public  var kvpairs : ArrayCollection;
        private var host : String;
        private var platform : String;
        private var port : String;
        private var user : String;
        private var passwd : String;
        private var nc_host : String;
        private var nc_port : String;
        private var nc_user : String;
        private var nc_passwd : String;
        private var profile : String;
        private var format : String;
        
        public static const FMT_XPATH:String = "xpath";
        public static const FMT_RAW:String = "raw";
        
        private function _toDeviceString() : String {
            var str : String = '<metadata>';
            str += '<device-auth'
            str += ' profile="' + profile + '"'
            str += ' platform="' + platform + '"'
            str += ' host="' + host + '"'
            str += ' port="' + port + '"'
            str += ' user="' + user + '"'
            str += ' passwd="' + passwd + '"'
            str += '/>\n'
            
            str += '<netconf-auth'
            str += ' host="' + nc_host + '"'
            str += ' port="' + nc_port + '"'
            str += ' user="' + nc_user + '"'
            str += ' passwd="' + nc_passwd + '"'
            str += '/>\n'
            str += '</metadata>'
            return str
        }
        
        public function toDeviceString() : String {
            var str : String = '<?xml version="1.0" encoding="UTF-8"?>\n';
            str += '<payload>'
            str += _toDeviceString()
            str += '</payload>'
            return str
        }
        
        private function optionString(option:String): String
        {
            if (option != '') {
                return ' option="' + option + '"';
            }
            return '';
        }
        
        public function toCapString() : String {
            var str : String = '<?xml version="1.0" encoding="UTF-8"?>\n';
            str += '<payload version="3" protocol="' + protocol + '">\n';
            str += _toDeviceString();
            str += '<keyvalue/>\n';
            str += '</payload>'
            return str;
        }
        
        public function toSchemaString(schemaStr : String) : String {
            var str : String = '<?xml version="1.0" encoding="UTF-8"?>\n';
            str += '<payload version="3" protocol="' + protocol + '">\n';
            str += _toDeviceString();
            str += '<keyvalue/>\n';
            str += schemaStr;
            str += '</payload>'
            return str;
        }

        public function toString(rpc:String = '') : String {
            
            var kvStr : String = '';
            var len : int = 0;
            
            if (format == FMT_XPATH) {
                for each (var item:Object in kvpairs) {
                    var path : String = item.Key;
                    var value : String = item.Value;
                    var option : String = item.Option;
                    
                    if (value == null || option == null) {
                        continue
                    }
                    
                    if (value == '<get-config>') {
                        kvStr += '<node path="' + path + '" flag="get-config"/>\n'
                    } else if (value == '<get>') {
                        kvStr += '<node path="' + path + '" flag="get"/>\n'
                    } else if (value == '<empty>') {
                        kvStr += '<node path="' + path + '" flag="empty"' + optionString(option) + '/>\n';
                    } else if (value != '') {
                        kvStr += '<node path="' + path + '"' + optionString(option) + '>' + value + '</node>\n';
                    } else {
                        kvStr += '<node path="' + path + '"' +  optionString(option)+ '/>\n';
                    }
                    len++;
                }
                
                if (len == 0) {
                    return '';
                }
            }
            
            var str : String = '<?xml version="1.0" encoding="UTF-8"?>\n';
            str += '<payload version="3"  protocol="' + protocol
            str += '" format="' + format + '"';
            
            if (operation != '') {
                str += ' operation="' + operation.toLowerCase() + '"'
            }
            
            if (source != '') {
                str += ' source="' + source.toLowerCase() + '"'
            }
            
            if (target != '') {
                str += ' target="' + target.toLowerCase() + '"'
            }
            str+= '>\n';

            str += _toDeviceString();
            if (format == FMT_XPATH) {
                if (kvStr != '') {
                    str += '<keyvalue>\n';
                    str += kvStr;
                    str += '</keyvalue>\n';
                } else {
                    str += '<keyvalue/>\n';
                }
            } else if (format == FMT_RAW) {
                str += "<raw><![CDATA[" + rpc + "]]></raw>";
            }
            
            str += '</payload>'
            return str;
        }
        
        public function RequestPayload()
        {
            reset();
            this.kvpairs = new ArrayCollection();
        }
        
        public function reset() : void
        {
            this.protocol = 'netconf'
            this.operation = ''
            this.source = ''
            this.target = ''
            this.base_config = ''
            this.verify_config = ''
            this.host = this.nc_host = this.platform = ''
            this.port = this.nc_port = ''
            this.user = this.nc_user = ''
            this.passwd = this.nc_passwd = ''
            this.profile = '';
            this.format = FMT_XPATH;
            removeAll();
        }
        
        public function setMode(oper:String) : void {
            this.operation = oper
        }
        
        public function setProtocol(proto:String) : void {
            this.protocol = proto
        }
        
        public function setConfig(base_cfg:String, config:String, reset: Boolean) : void {
            this.base_config = base_cfg
            this.verify_config = config
            this.reset_config = reset ? 'true' : 'false'
        }
        
        public function setDeviceSettings(plat: String, host: String, port : String,
                                          user : String, pwd : String, prof : String) : void {
            this.platform = plat
            this.host = host
            this.port = port
            this.user = user
            this.passwd = pwd
            this.profile = prof
        }
        
        public function setNetconfSettings(host: String, port : String, user : String, pwd : String) : void {
            this.nc_host = host
            this.nc_port = port
            this.nc_user = user
            this.nc_passwd = pwd
        }
        
        public function setDatastore(src:String, tgt:String) : void {
            this.source = src;
            this.target = tgt;
        }
        
        public function setFormat(fmt : String) : void {
            this.format = fmt;
        }
        
        public function removeItem(path : String) : void  {
            var delItem : Object = null;
            for each (var item : Object in kvpairs) {
                if (item.Key == path) {
                    delItem = item;
                    break;
                }
            }
            if (delItem != null) {
                kvpairs.removeItem(delItem);
            }
        }
        
        public function addItem (path : String, value:String, option:String = '') : void  {
            kvpairs.addItem({Key:path, Value:value, Option: option});
        }
        
        public function removeAll() : void {
            if (this.kvpairs != null) {
                kvpairs.removeAll();
            }
        }
    }
}