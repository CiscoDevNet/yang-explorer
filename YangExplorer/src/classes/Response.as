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
    public class Response
    {
        public var type : String;
        public var errored : Boolean;
        public var msg : String;
        public var xml : XML;

        public function Response(response : XML)
        {
            type = '';
            errored = true;
            msg = '';
            xml = null;
            
            if (response.localName() != 'response') {
                return;
            }
            
            type = response.attribute('type');
            for each (var child : XML in response.children()) {
                if (child.localName() == 'error') {
                    errored = true;
                    msg = child.toString();
                } else if (child.localName() == 'success') {
                    msg = child.toString();
                    errored = false;
                } else {
                    xml = child;
                }
            }
        }
        
        public function toString() : String {
            var str : String = 'Response { type : ' + type;
            str += 'status : ' + errored.toString()
            str += '\n  xml : ' + xml.toXMLString();
            str += '  }';
            return str;
        }
    }
}