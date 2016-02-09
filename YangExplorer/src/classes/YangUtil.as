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
    import mx.utils.StringUtil;

    public class YangUtil
    {
        private var netconfOp:ArrayCollection;
        private var msg_id : uint;
        public static const DEFAULT:int = 0;
        public static const EDIT_CONFIG:int = 1;
        public static const GET_CONFIG:int = 2;
        public static const GET:int = 3;
        public static const RPC:int = 4;
        public var mode : int;
        public var kvpair : ArrayCollection;

        public function YangUtil()
        {
            msg_id = uint(Math.random() * (uint.MAX_VALUE/100000));
            mode = DEFAULT;
            kvpair = new ArrayCollection();
        }

        public function setMode (mode : int): void {
            this.mode = mode;
        }

        public function getMode () : int {
            return this.mode;
        }

        public function getModeString() : String
        {
            switch (mode) {
                case EDIT_CONFIG:
                    return 'edit-config';
                case GET_CONFIG:
                    return 'get-config';
                case GET:
                    return 'get';
                case RPC:
                    return 'rpc';
            }

            return ''
        }

        public function getPath(object:XML):String
        {
            var path:String = "";
            var name:String = "";
            var type:String = "";

            while (object != null && object.@type != 'module') {
                name = object.@name;
                type = object.@type;
                if (type != "choice" && type != "case" && type != "input" && type != "output") {
                    path = "/" + name + path;
                }
                object = object.parent();
            }
            return path;
        }

        public function searchNode (root:XML, path:String) : XML
        {
            var names:Array = path.split('/');
            for (var i:int = 0; i < names.length; i++) {
                for each (var child:XML in root.node) {
                    if (child.@name == names[i]) {
                        root = child
                        break;
                    }
                }
            }

            if (root.@path == path) {
                return root
            }

            return null;
        }

        public function isKey(node:XML) : Boolean
        {
            return (node.attribute('is_key') == 'true');
        }

        public function isPresence(node:XML) : Boolean
        {
            return (node.attribute('presence') == 'true');
        }

        public function isEmpty(node:XML) : Boolean
        {
            return (node.attribute('type') == 'leaf' && node.attribute('datatype') == 'empty');
        }

        public function resetXML (xml:XMLList, target_mode:int = DEFAULT) : void {
            this.mode = target_mode;

            if (xml == null) return;

            for each (var item:XML in xml) {
                if (item.hasOwnProperty('@ncop')) {
                    item.@ncop = '';
                }
                if (item.hasOwnProperty('@value')) {
                    item.@value = '';
                }
                resetXML(item.children());
            }
        }

        public function changeMode (xml:XMLList, target_mode:int = DEFAULT) : void {
            var value : String = '';
            if (xml == null) return;
            this.mode = target_mode;

            for each (var item:XML in xml) {
                if (item.hasOwnProperty('@ncop')) {
                    if (target_mode != EDIT_CONFIG) {
                        item.@ncop = '';
                    }
                }

                if (item.hasOwnProperty('@value')) {
                    value = item.@value;
                    value = StringUtil.trim(value);
                    var access:String = item.attribute('access');
                    switch (target_mode) {
                        case DEFAULT:
                        case EDIT_CONFIG:
                            if (value == '<get-config>' || value == '<get>' ||  access != 'read-write') {
                                item.@value = '';
                            }
                            break;
                        case GET_CONFIG:
                            if (value == '<get>' && access == 'read-write') {
                                item.@value = '<get-config>';
                            }
                            break;
                        case GET:
                            if (value == '<get-config>') {
                                item.@value = '<get>';
                            }
                            break;
                        default:
                            item.@value = '';
                    }
                }
                changeMode(item.children(), target_mode);
            }
            return;
        }

        public function processXMLList (xmllist:XMLList, kvpairs:ArrayCollection) : void {
            for each (var item:XML in xmllist) {
                if (item.hasOwnProperty('@path')) {
                    var path : String = item.attribute('path');
                    var type : String = item.attribute('type');
                    var value : String = '';
                    var ncop : String = '';

                    if (item.hasOwnProperty('@value')) {
                        value = item.attribute('value');
                        value = StringUtil.trim(value);
                    }

                    if (item.hasOwnProperty('@ncop')) {
                        ncop = item.attribute('ncop');
                    }

                    if (kvpairs != null && (value != '' || ncop != '')) {
                        kvpairs.addItem({Key:path, Value:value, Option:ncop})
                    }

                    if (value != '') {
                        updateNetConfMode(item, value);
                    }
                }
                processXMLList(item.children(), kvpairs)
            }
        }

        public function processXML (xml:XML, kvpairs:ArrayCollection) : void {
            processXMLList(xml.children(), kvpairs)
        }

        public  function updateNetConfMode(node:XML, val:String): void
        {
            if (val == null || node == null || val == '') {
                return;
            }

            /* Set mode based on cell value */
            if (val == '<get-config>') {
                this.mode = GET_CONFIG;
            } else if (val == '<get>') {
                this.mode = GET;
            } else if (val == '<rpc>') {
                this.mode = RPC;
            } else {
                var access:String = node.attribute('access');
                /* Don't set to edit config mode for oper data filter values */
                if (access == 'read-write' && this.mode == DEFAULT) {
                    this.mode = EDIT_CONFIG;
                } else if (access == 'read-only') {
                    this.mode = GET;
                }
            }
        }

        public function validateInput(node:XML, val:String) : Boolean
        {
            if (val == null || node == null || val == '') {
                return true;
            }

            var type: String = node.attribute('type');

            // Validate that value has been entered in correct node *//
            switch(type) {
                case 'module':
                case 'case':
                case 'choice':
                case 'input':
                case 'output':
                    return false;
                default:
                    break;
            }

            // Skip Special Values *//
            var access: String = node.attribute('access');
            if (access == 'read-only' && val == '<get-config>') {
                return false;
            }

            if (val == '<get>' || val == '<get-config>') {
                return true;
            }

            if (type == 'leaf' || type == 'leaf-list') {
                var datatype : String = node.attribute('datatype');
                switch (datatype) {
                    case 'int8':
                    case 'int16':
                    case 'int32':
                    case 'uint8':
                    case 'uint32':
                    case 'uint64':
                    case 'counter32':
                    case 'counter64':
                    case 'gauge32':
                    case 'gauge64':
                    case 'zero-based-counter32':
                    case 'zero-based-counter64':
                    case 'timeticks':
                    case 'timestamp':
                        return (!isNaN(parseInt(val)));

                    case 'boolean':
                        return (val == 'true' || val == 'false')

                    case 'empty':
                        return (val == '<empty>')
                    default:
                        break;
                }
            } else if (type == 'container') {
                // presence container
                return (val == '<empty>' && node.attribute('presence') =='true')
            } else if (type == 'list') {
                return false;
            }
            return true;
        }
    }
}