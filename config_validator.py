"""
config_validator.py
Configuration Management and RVK Notation Validator
Part 1/3 of RVK-PICA Classifier AI
"""

import streamlit as st
import requests
import json
import re
from typing import Dict, List, Optional
import os
from pathlib import Path
import xml.etree.ElementTree as ET


class ConfigManager:
    """Handles secure configuration management with persistent storage"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.rvk_classifier'
        self.config_file = self.config_dir / 'config.json'
        self.ensure_config_dir()
    
    def ensure_config_dir(self):
        """Create configuration directory if it doesn't exist"""
        self.config_dir.mkdir(exist_ok=True)
        
        if hasattr(os, 'chmod'):
            try:
                os.chmod(self.config_dir, 0o700)
            except:
                pass
    
    def load_config(self) -> Dict:
        """Load configuration from secure local storage"""
        default_config = {
            'openai': {
                'enabled': False,
                'api_key': '',
                'base_url': 'https://api.openai.com/v1',
                'model': 'gpt-3.5-turbo',
                'max_tokens': 1000,
                'temperature': 0.3
            },
            'rvk': {
                'enabled': True,
                'base_url': 'https://rvk.uni-regensburg.de/api',
                'format': 'json.php',
                'requires_auth': False,
                'api_key': ''
            }
        }
        
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    for section in default_config:
                        if section in saved_config:
                            default_config[section].update(saved_config[section])
                    
                    default_config['rvk']['format'] = 'json.php'
                    return default_config
        except Exception as e:
            st.warning(f"Could not load saved configuration: {e}")
        
        return default_config
    
    def save_config(self, config: Dict):
        """Save configuration to secure local storage"""
        try:
            config['rvk']['format'] = 'json.php'
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            if hasattr(os, 'chmod'):
                try:
                    os.chmod(self.config_file, 0o600)
                except:
                    pass 
            
            return True
        except Exception as e:
            st.error(f"Could not save configuration: {e}")
            return False


class RVKNotationValidator:
    """
    Validates RVK notations against the official RVK API with hierarchical understanding
    """
    
    def __init__(self, rvk_config: Dict):
        self.rvk_config = rvk_config
        self.validated_cache = {}
        self.invalid_cache = set()
    
    def validate_notation(self, notation: str) -> Optional[Dict]:
        """Validate a single RVK notation against official RVK API"""
        if notation in self.validated_cache:
            return self.validated_cache[notation]
        if notation in self.invalid_cache:
            return None
        
        try:
            encoded_notation = requests.utils.quote(notation)
            url = f"{self.rvk_config['base_url']}/{self.rvk_config['format']}/node/{encoded_notation}"
            
            headers = {'Accept': 'application/xml'}
            if self.rvk_config['requires_auth'] and self.rvk_config['api_key']:
                headers['Authorization'] = f"Bearer {self.rvk_config['api_key']}"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.ok:
                try:
                    root = ET.fromstring(response.text)
                    node_element = root.find('node')
                    if node_element is not None:
                        validated_notation = {
                            'notation': node_element.get('notation', notation),
                            'benennung': node_element.get('benennung', ''),
                            'hierarchy': [],
                            'children': [],
                            'valid': True,
                            'source_verified': True 
                        }
                        
                        self.validated_cache[notation] = validated_notation
                        return validated_notation
                except ET.ParseError as e:
                    pass
                
            self.invalid_cache.add(notation)
            return None
            
        except Exception as e:
            pass
    
    def search_nodes_endpoint_and_validate(self, search_terms: List[str], rvk_notation_prefixes: Optional[List[str]] = None) -> List[Dict]:
        """Search the RVK /nodes endpoint for terms and return validated notations"""
        suggestions = []
        prefix_regex = None
        if rvk_notation_prefixes:
            clean_prefixes = [re.escape(p.upper().strip()) for p in rvk_notation_prefixes if p.strip()]
            if clean_prefixes:
                prefix_pattern = f"^({'|'.join(clean_prefixes)})\\S*"
                prefix_regex = re.compile(prefix_pattern)

        for term in search_terms:
            if not term.strip():
                continue
            try:
                encoded_term = requests.utils.quote(term)
                url = f"{self.rvk_config['base_url']}/{self.rvk_config['format']}/nodes/{encoded_term}"
                
                headers = {'Accept': 'application/xml'}
                if self.rvk_config['requires_auth'] and self.rvk_config['api_key']:
                    headers['Authorization'] = f"Bearer {self.rvk_config['api_key']}"
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.ok:
                    try:
                        root = ET.fromstring(response.text)
                        node_elements = root.findall('node')
                        
                        for node_element in node_elements:
                            notation = node_element.get('notation')
                            benennung = node_element.get('benennung')
                            
                            if not notation or not benennung:
                                continue

                            rvk_prefix_match = False
                            if prefix_regex:
                                if prefix_regex.match(notation):
                                    rvk_prefix_match = True
                                else:
                                    continue

                            suggestions.append({
                                'notation': notation,
                                'benennung': benennung,
                                'relevance': self.calculate_relevance_for_description([term], benennung),
                                'keyword': term,
                                'source': 'RVK API (/nodes-Suche)',
                                'valid': True,
                                'source_verified': True,
                                'hierarchy': [],
                                'children': [], 
                                'rvk_prefix_match': rvk_prefix_match 
                            })
                    except ET.ParseError as e:
                        pass
                else: 
                    pass
            except Exception as e:
                pass
                continue
        
        unique_suggestions = {}
        for sug in suggestions:
            if sug['notation'] not in unique_suggestions:
                unique_suggestions[sug['notation']] = sug
            else:
                existing_sug = unique_suggestions[sug['notation']]
                if sug['rvk_prefix_match'] and not existing_sug.get('rvk_prefix_match', False):
                    unique_suggestions[sug['notation']] = sug
                elif sug['relevance'] > existing_sug['relevance']:
                    unique_suggestions[sug['notation']] = sug

        return list(unique_suggestions.values())

    def calculate_relevance_for_description(self, keywords: List[str], description: str) -> int:
        """Calculate relevance score based on keyword matching in RVK descriptions"""
        if not description:
            return 10
        
        description_lower = description.lower().strip()
        score = 0
        
        # Universal semantic equivalents for all domains
        semantic_equivalents = {
            'migration': ['zuwanderung', 'einwanderung', 'auswanderung', 'flucht', 'vertreibung', 'migrationsforschung', 'bevölkerungsbewegung'],
            'integration': ['soziale integration', 'eingliederung', 'inkulturation', 'integrationsprozesse', 'assimilation'],
            'interkulturell': ['kulturtransfer', 'interkulturalität', 'multikulturell', 'interkulturelle beziehungen', 'kulturkontakt'],
            'stadtforschung': ['urbanistik', 'stadtentwicklung', 'kommunal', 'lokal', 'stadtsoziologie', 'urban'],
            'soziologie': ['gesellschaftswissenschaften', 'sozialwissenschaften', 'gesellschaft'],
            'gesellschaftlicher wandel': ['sozialer wandel', 'soziokulturell', 'demographischer wandel', 'transformation'],
            'informatik': ['computer', 'software', 'algorithmus', 'digital', 'technologie', 'it'],
            'medizin': ['gesundheit', 'klinik', 'diagnose', 'therapie', 'healthcare', 'medical'],
            'bildung': ['erziehung', 'pädagogik', 'schule', 'universität', 'ausbildung', 'lernen'],
            'recht': ['gesetz', 'juridisch', 'legal', 'justiz', 'rechtswissenschaft'],
            'wirtschaft': ['ökonomie', 'management', 'finanzen', 'betrieb', 'unternehmen'],
            'geschichte': ['historisch', 'vergangenheit', 'zeitgeschichte', 'historie'],
            'kunst': ['ästhetik', 'künstlerisch', 'kreativ', 'design', 'kultur'],
            'musik': ['musikwissenschaft', 'musikalisch', 'komposition', 'audio'],
            'literatur': ['schrift', 'text', 'roman', 'gedicht', 'literarisch'],
            'philosophie': ['denken', 'ethik', 'metaphysik', 'erkenntnistheorie'],
            'psychologie': ['verhalten', 'kognition', 'entwicklung', 'persönlichkeit'],
            'politik': ['staat', 'regierung', 'demokratie', 'verwaltung', 'politisch'],
            'naturwissenschaft': ['physik', 'chemie', 'biologie', 'wissenschaft', 'forschung'],
            'mathematik': ['zahlen', 'statistik', 'algebra', 'geometrie', 'rechnen']
        }

        for keyword in keywords:
            keyword_lower = keyword.lower().strip()
            if keyword_lower in description_lower:
                score += 40
            
            if keyword_lower in semantic_equivalents:
                for equivalent in semantic_equivalents[keyword_lower]:
                    if equivalent in description_lower:
                        score += 20

        doc_words = set(re.findall(r'\b\w+\b', ' '.join(keywords).lower()))
        desc_words = set(re.findall(r'\b\w+\b', description_lower))
        
        overlap_count = len(doc_words.intersection(desc_words))
        score += min(30, overlap_count * 5)

        return min(100, max(score, 10))

    def get_hierarchical_path(self, notation: str) -> List[Dict]:
        """Get the complete hierarchical path for an RVK notation"""
        try:
            encoded_notation = requests.utils.quote(notation)
            url = f"{self.rvk_config['base_url']}/{self.rvk_config['format']}/ancestors/{encoded_notation}"
            
            headers = {'Accept': 'application/xml'}
            if self.rvk_config['requires_auth'] and self.rvk_config['api_key']:
                headers['Authorization'] = f"Bearer {self.rvk_config['api_key']}"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.ok:
                root = ET.fromstring(response.text)
                
                path = []
                for ancestor in root.findall('ancestor'):
                    path.append({
                        'notation': ancestor.get('notation', ''),
                        'benennung': ancestor.get('benennung', ''),
                        'level': len(ancestor.get('notation', '').split())
                    })
                
                current_node = self.validate_notation(notation)
                if current_node:
                    path.append({
                        'notation': current_node['notation'],
                        'benennung': current_node['benennung'],
                        'level': len(current_node['notation'].split())
                    })
                
                return sorted(path, key=lambda x: x['level'])
            
        except Exception as e:
            pass
        
        return []

    def format_hierarchical_path(self, path: List[Dict]) -> str:
        """Format hierarchical path for display"""
        if not path:
            return ""
        
        path_elements = []
        for level in path:
            notation = level['notation']
            description = level['benennung']
            if notation and description:
                path_elements.append(f"{notation} ({description})")
        
        return " → ".join(path_elements)

    def determine_rvk_hierarchy_level(self, notation: str) -> str:
        """Determine the RVK hierarchy level based on official RVK structure"""
        notation_clean = notation.strip()
        
        parts = notation_clean.split()
        
        if len(parts) == 1:
            if len(parts[0]) == 1 and parts[0].isalpha():
                return "Hauptgruppe"
            elif len(parts[0]) == 2 and parts[0].isalpha():
                return "Untergruppe"
            elif len(parts[0]) > 2:
                return "Untergruppe"
        elif len(parts) == 2:
            letters, numbers = parts[0], parts[1]
            if letters.isalpha() and numbers.isdigit():
                return "Feingruppe"
        elif len(parts) >= 3:
            return "Feingruppe + Schlüssel"
        
        return "Unbekannt"