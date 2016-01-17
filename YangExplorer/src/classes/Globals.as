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
    public class Globals
    {
        public var host : String;
        public var port : String;
        public var user : String;
        public function Globals()
        {
            host = 'localhost';
            port = '8088'
            user = ''
        }
        
        public function get_url() : String {
            return 'http://' + this.host + ':' + this.port + '/explorer';
        }

        public function get_root_url() : String {
            return 'http://' + this.host + ':' + this.port;
        }
    }
}