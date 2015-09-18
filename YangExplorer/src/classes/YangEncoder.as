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
    import flash.utils.Dictionary;
    
    import mx.controls.Alert;
    
    public class YangEncoder
    {
        public static const ENC_XML  : int = 1;
        public static const ENC_JSON : int = 2;
        private var nsdict : Dictionary;
        private var mode : String;
        
        public function YangEncoder(version : String = "1.0")
        {
            nsdict = new Dictionary()
            nsdict['xc'] = "urn:ietf:params:xml:ns:netconf:base:" + version;
        }
        
        public function init_namespaces(tree : XML) : void {
            var ns_str : String;
            var arr : Array;
            trace('init_namespaces');
            for each (var module : XML in tree.children()) {
                if (module.hasOwnProperty('@namespaces')) {
                    ns_str = module.@namespaces;
                    trace('init_namespaces' + ns_str + module.@prefix);
                    var nsarr : Array =  ns_str.split('|')
                    for each (var ns : String in nsarr) {
                        arr = ns.split(',');
                        trace (arr[0] + '->' + arr[1]);
                        nsdict[arr[0]] = arr[1];
                    }
                }
            }
        }
        
        private function get_namespace(node : String, default_ns :Boolean = false) : String {
            var prefix : String = node;
            if (node.indexOf(':') >= -1) {
                prefix = node.split(':')[0];
            }
            
            if (nsdict[prefix] != undefined) {
                var rvalue : String = (default_ns) ? ' xmlns="' : ' xmlns:' + prefix + '="'
                trace ('get_namespace: ' + prefix + '->' + nsdict[prefix]);
                return rvalue + nsdict[prefix] + '"';
            }
            return ''
        }
        
        private function is_datanode(type : String) : Boolean 
        {
            switch (type) {
                case 'module':
                case 'choice':
                case 'case':
                case 'input':
                case 'output':
                    return false;
            }
            return true;
        }
        
        private function is_terminal(type : String) : Boolean 
        {
            return (type == 'leaf' || type == 'leaf-list' || type == '__yang_placeholder');
        }
        
        public function to_xml(tree : XML, mode : String, src : String, tgt : String) : XML 
        {
            var result : XML;
            var out : XML;
            
            if (tree == null) {
                Alert.show('Null Data Tree!!', 'to_xml');
                return null;
            }
            trace('to_xml: mode = ' + mode);
            // add namespaces to disctionary for reference
            init_namespaces(tree);
            this.mode = mode;
            var xml_str : String = '<rpc message-id="101" xmlns="' + nsdict['xc'] + '">'
            switch (mode) {
                case 'edit-config':
                    xml_str += '<edit-config>';
                    xml_str += '<target><' + tgt.toLowerCase() + '/></target>';
                    xml_str += '<config '+ get_namespace('xc') +'></config>';
                    xml_str += '</edit-config>'
                    xml_str += '</rpc>';
                    result = new XML(xml_str);
                    out = result.children()[0].children()[1];
                    break;
                case 'get':
                    xml_str += '<get>';
                    xml_str += '<filter '+ get_namespace('xc') +'></filter>';
                    xml_str += '</get>';
                    xml_str += '</rpc>';
                    result = new XML(xml_str);
                    out = result.children()[0].children()[0];
                    break;
                case 'get-config':
                    xml_str += '<get-config>'
                    xml_str += '<source><' + src.toLowerCase() + '/></source>'
                    xml_str += '<filter '+ get_namespace('xc') +'></filter>';
                    xml_str += '</get-config>';
                    xml_str += '</rpc>';
                    result = new XML(xml_str);
                    out = result.children()[0].children()[1];
                    break;
                case 'rpc':
                    xml_str += '</rpc>';
                    result = out = new XML(xml_str);
                    break;
                default:
                    return null;
            }
            
            trace('to_xml :' + xml_str);
            process_netconf(tree.children(), out);
            if (out.children().length() <= 0) {
                trace('to_xml : no data');
                return null;
            }
            trace('to_xml : payload ' + out.toXMLString());
            return result;
        }
        
        /**
         * This function processes one yang node and  returns a xml tag with or
         * without value (xml text). @value and @ncop attributes contains user
         * data for the node.
         */
        private function process_terminal(node : XML) : XML
        {
            var value : String = '';
            var ncop  : String = '';
            var op : String = '';
            var ns : String = '';
            
            if (node.hasOwnProperty('@value')) {
                value = node.@value;
            } 
            
            if (node.hasOwnProperty('@ncop')) {
                ncop = node.@ncop
                if (ncop != '' && ncop != 'merge') {
                    op = ' xc:operation = "' + ncop ;
                    ns += get_namespace('xc');
                }
            }
            
            trace(' process_terminal-ns: ' + ns)
            // if node is has no user values then nothing to be done here
            if (value == ''  && ncop == '') {
                return null;
            }
            
            var name  : String = node.@name;
            ns += get_namespace(name);
            trace(' process_terminal-value: ' + value + ':' + ncop)
            if (value == '<get>' || value == '<get-config>' || value == '<rpc>') {
                return new XML('<' + name + ns + '></' + name + '>');
            }
            
            var type : String = node.@type;
            var xml  : XML;
            
            if (is_terminal(type)) {
                if (value == '') {
                    return null;
                }
                if (node.hasOwnProperty('@is_key') || mode == 'edit-config' || mode == 'rpc') {
                    if (value == '<empty>') {
                        value = '';
                    } else {
                        ns += get_namespace(value);
                    }
                    xml = new XML('<' + name + ns + op +'>' + value + '</' + name + '>')
                } else {
                    xml = new XML('<' + name + ns + op + '></' + name + '>');
                }
                return xml;
            }
            trace(' process_terminal: no match')
            return null;
        }
        
        /**
         * 
         * This function processes one yang node and  returns a xml tag with or
         * without value (xml text). @value and @ncop attributes contains user
         * data for the node.
         * 
         *  @xmllist : 
         */
        private function process_netconf(xmllist:XMLList, out:XML) : XML {
            var xml : XML;
            var count : int = 0;
            var keep : Boolean;
            var key : String;
            var ns : String;
            
            for each (var node:XML in xmllist) {
                var name : String = node.@name;
                var type : String = node.@type;
                trace('process_netconf: ' +  name + ':' + type);
                if (type == '__yang_placeholder') {
                    continue;
                }
                
                if (name == null || name == '') {
                    continue;
                }
                
                if (is_datanode(type)) {
                    if (is_terminal(type)) {
                        // terminas (leaf, leaf-list)
                        xml = process_terminal(node);
                        if (xml != null) {
                            out.appendChild(xml);
                        }
                    } else {
                        // container and list nodes
                        trace('  process_netconf: container/list node ');
                        keep = true;
                        xml = process_terminal(node);
                        if (xml == null) {
                            keep = false;
                            xml = new XML('<' + name + get_namespace(name) + '></' + name + '>');
                        } else if (type == 'container') {
                            var value : String = ''
                            if (node.hasOwnProperty('@value')) {
                                value = node.@value;
                                if (value == '<get>' || value == '<get-config>') {
                                    // found get operation on this container, stop processing
                                    // child elements
                                    out.appendChild(xml);
                                    return out;
                                }
                            }
                        } 
                        process_netconf(node.children(), xml);
                        if (keep || xml.children().length() > 0) {
                            out.appendChild(xml);
                            trace('Processed terminal ' + out.toXMLString());
                        }
                    }
                } else {
                    // non data nodes (module, choice, case ...)
                    if (type == 'module') {
                        key = node.@prefix;
                        ns = this.nsdict[key];
                        count = out.children().length();
                    }
                    out = process_netconf(node.children(), out);
                    
                    trace('Processed non-data ' + out.toXMLString());
                    if (type == 'module' && node.hasOwnProperty('@prefix')) {
                        for (var i : int = count; i < out.children().length(); i++) {
                            out.children()[i].@xmlns = ns
                        }
                    }
                }
            }
            return out;
        }
    }
}