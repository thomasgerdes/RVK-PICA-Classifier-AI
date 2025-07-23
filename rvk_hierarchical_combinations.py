"""
rvk_hierarchical_combinations.py
RVK Hierarchical Combination Logic with Improved Search Strategy
Part 2/3 of RVK-PICA Classifier AI v1.0
Extension for RVKNotationValidator class
"""

from typing import Dict, List
import re
import requests
import xml.etree.ElementTree as ET

# === GLOBAL/MODULE-LEVEL DEFINITIONS FOR RVK MAPPINGS ===
HAUPTGRUPPE_MAPPING = {
    'A': {
        'keywords': ['bibliographie', 'nachschlagewerk', 'wissenschaftskunde', 'hochschule', 'buch', 'medien', 'kommunikation', 'umwelt'],
        'description': 'General, Bibliographies, Reference Works',
        'untergruppen': {
            'AA': 'Bibliographies - General', 'AB': 'Bibliographies - Subject Bibliographies',
            'AC': 'Reference Works - General', 'AD': 'Science Studies',
            'AL': 'Higher Education', 'AN': 'Book and Library Science',
            'AP': 'Media and Communication Science', 'AR': 'Environmental Sciences'
        }
    },
    'B': {
        'keywords': ['theologie', 'religion', 'gott', 'kirche', 'glaube', 'christentum', 'islam', 'judentum'],
        'description': 'Theology and Religious Studies',
        'untergruppen': {
            'BA': 'Theology - General', 'BB': 'Biblical Theology', 'BC': 'Church History',
            'BD': 'Systematic Theology', 'BE': 'Practical Theology', 'BH': 'Christian Denominations',
            'BL': 'Non-Christian Religions'
        }
    },
    'C': {
        'keywords': ['philosophie', 'denken', 'ethik', 'psychologie', 'verhalten', 'bewusstsein'],
        'description': 'Philosophy and Psychology',
        'untergruppen': {
            'CA': 'Philosophy - General', 'CB': 'Logic and Epistemology', 'CC': 'Metaphysics',
            'CD': 'Philosophical Anthropology', 'CE': 'Ethics', 'CL': 'Psychology - General',
            'CM': 'Developmental Psychology', 'CP': 'Applied Psychology'
        }
    },
    'D': {
        'keywords': ['pädagogik', 'erziehung', 'bildung', 'schule', 'lernen', 'didaktik'],
        'description': 'Education',
        'untergruppen': {
            'DA': 'Education - General', 'DB': 'Educational Philosophy', 'DC': 'History of Education',
            'DD': 'Educational Sociology', 'DF': 'School Education', 'DK': 'Adult Education'
        }
    },
    'G': {
        'keywords': ['deutsch', 'germanistik', 'niederländisch', 'skandinavisch', 'literatur'],
        'description': 'German Studies, Dutch Philology, Scandinavian Studies',
        'untergruppen': {
            'GA': 'German Studies - General', 'GB': 'German Linguistics',
            'GE': 'German Literary History', 'GI': 'German Authors',
            'GL': 'Dutch Philology', 'GN': 'Scandinavian Philology'
        },
        'feingruppen_examples': {
            'GE 4001': 'German Literature Medieval Period',
            'GE 5000': 'German Literature 16th-18th Century',
            'GB 1729': 'German Linguistics Dialectology'
        }
    },
    'L': {
        'keywords': ['kultur', 'ethnologie', 'archäologie', 'kunst', 'musik', 'bildung'],
        'description': 'Cultural Studies',
        'untergruppen': {
            'LA': 'Ethnology', 'LB': 'Education and Learning', 'LC': 'Cultural Science',
            'LD': 'Classical Archaeology', 'LH': 'Art History', 'LI': 'Islamic Art',
            'LJ': 'East Asian Art', 'LK': 'American Art', 'LP': 'Musicology'
        },
        'feingruppen_examples': {
            'LB 56000': 'Higher Education System', 'LB 34000': 'Education System Germany',
            'LD 1100': 'Archaeological Methods', 'LH 65000': 'Art History Germany',
            'LP 90000': 'Music History'
        }
    },
    'M': {
        'keywords': ['politik', 'soziologie', 'gesellschaft', 'migration', 'integration', 'sozial', 'militär'],
        'description': 'Political Science, Sociology, Military Science',
        'untergruppen': {
            'MA': 'Political Science - General', 'MB': 'Political Science - State Theory',
            'MC': 'Political Science - Political Systems', 'MD': 'Political Science - Political Ideologies',
            'ME': 'Political Science - Foreign Policy', 'MF': 'Political Science - Domestic Policy',
            'MG': 'Political Science - Parties', 'MH': 'Political Science - Elections',
            'MI': 'Political Science - Administration', 'MN': 'Sociology - General',
            'MQ': 'Sociology - Special Sociologies', 'MR': 'Sociology - Demographics',
            'MS': 'Sociology - Social Structure', 'MX': 'Military Science'
        },
        'feingruppen_examples': {
            'MN 1000': 'Sociology General', 'MN 8300': 'Migration, Population Movement',
            'MS 1200': 'Social Structure Germany', 'MQ 3200': 'Urban Sociology',
            'MA 1000': 'Political Science General'
        }
    },
    'N': {
        'keywords': ['geschichte', 'historisch', 'vergangenheit', 'zeitgeschichte'],
        'description': 'History',
        'untergruppen': {
            'NB': 'History - Auxiliary Sciences', 'NC': 'History - General',
            'ND': 'Prehistoric Archaeology', 'NF': 'Ancient History', 'NH': 'Medieval History',
            'NK': 'Modern History', 'NP': 'European History', 'NQ': 'German History',
            'NR': 'German Regional History', 'NS': 'German Local History',
            'NT': 'Austrian History', 'NU': 'Swiss History',
            'NV': 'French History', 'NW': 'British History',
            'NX': 'Russian History', 'NY': 'American History',
            'NZ': 'African, Asian, Oceanian History'
        },
        'feingruppen_examples': {
            'NQ 1000': 'German History General', 'NQ 6100': 'Germany 1945-1990',
            'NR 6050': 'Saxony History', 'NP 1000': 'European History General'
        }
    },
    'P': {
        'keywords': ['recht', 'gesetz', 'juridisch', 'legal', 'rechtswissenschaft', 'justiz'],
        'description': 'Legal Studies',
        'untergruppen': {
            'PA': 'Legal Studies - General', 'PB': 'Legal Philosophy',
            'PC': 'Legal History', 'PD': 'Civil Law', 'PE': 'Commercial Law',
            'PF': 'Labor Law', 'PG': 'Administrative Law', 'PH': 'Constitutional Law',
            'PI': 'Tax Law', 'PJ': 'Criminal Law', 'PK': 'Procedural Law'
        }
    },
    'Q': {
        'keywords': ['wirtschaft', 'ökonomie', 'management', 'finanzen', 'betrieb', 'unternehmen'],
        'description': 'Economics',
        'untergruppen': {
            'QA': 'Economics - General', 'QB': 'Economic Theory',
            'QC': 'Economic History', 'QD': 'Economic Policy',
            'QE': 'Macroeconomics', 'QH': 'Business Administration',
            'QI': 'Public Finance', 'QK': 'Banking', 'QL': 'Money and Credit',
            'QP': 'Enterprises', 'QR': 'Trade'
        }
    },
    'S': {
        'keywords': ['mathematik', 'statistik', 'informatik', 'computer', 'algorithmus', 'software'],
        'description': 'Mathematics and Computer Science',
        'untergruppen': {
            'SA': 'Mathematics - General', 'SB': 'Algebra', 'SC': 'Geometry',
            'SD': 'Analysis', 'SE': 'Probability Theory', 'SF': 'Statistics',
            'SG': 'Numerical Mathematics', 'SH': 'Applied Mathematics',
            'SI': 'Computer Science - General', 'SK': 'Theoretical Computer Science',
            'SM': 'Data Processing', 'SN': 'Programming', 'SO': 'Operating Systems',
            'SP': 'Applied Computer Science', 'SQ': 'Computer Graphics',
            'SR': 'Artificial Intelligence', 'SS': 'Software Engineering', 'ST': 'Computer Science - Applications'
        }
    },
    'V': {
        'keywords': ['chemie', 'pharmazie', 'molekül', 'reaktion', 'stoffkunde', 'arzneimittel'],
        'description': 'Chemistry and Pharmacy',
        'untergruppen': {
            'VA': 'Chemistry - General', 'VB': 'Theoretical Chemistry', 'VC': 'Inorganic Chemistry',
            'VD': 'Organic Chemistry', 'VE': 'Physical Chemistry', 'VF': 'Analytical Chemistry',
            'VG': 'Biochemistry', 'VH': 'Technical Chemistry', 'VI': 'Pharmacy - General',
            'VJ': 'Pharmaceutical Chemistry', 'VK': 'Pharmacology', 'VL': 'Toxicology'
        }
    },
    'W': {
        'keywords': ['biologie', 'botanik', 'zoologie', 'genetik', 'ökologie', 'evolution', 'medizin'],
        'description': 'Biology and Pre-Clinical Medicine',
        'untergruppen': {
            'WA': 'Biology - General', 'WB': 'Systematic Biology', 'WC': 'Botany',
            'WD': 'Zoology', 'WE': 'Anthropology', 'WF': 'Genetics', 'WG': 'Ecology',
            'WH': 'Developmental Biology', 'WI': 'Molecular Biology', 'WJ': 'Microbiology',
            'WK': 'Anatomy', 'WL': 'Physiology', 'WM': 'Pathology'
        }
    },
    'Y': {
        'keywords': ['medizin', 'klinisch', 'diagnose', 'therapie', 'chirurgie', 'innere medizin'],
        'description': 'Clinical Medicine',
        'untergruppen': {
            'YA': 'Clinical Medicine - General', 'YB': 'Internal Medicine', 'YC': 'Surgery',
            'YD': 'Gynecology', 'YE': 'Pediatrics', 'YF': 'Dermatology',
            'YG': 'Psychiatry', 'YH': 'Neurology', 'YI': 'Radiology', 'YJ': 'Anesthesiology'
        }
    },
    'Z': {
        'keywords': ['land', 'forst', 'garten', 'fischerei', 'hauswirtschaft', 'technik', 'ingenieur', 'sport'],
        'description': 'Agriculture, Forestry, Technology, Sports',
        'untergruppen': {
            'ZA': 'Agriculture and Forestry - General', 'ZB': 'Plant Cultivation',
            'ZC': 'Animal Breeding', 'ZD': 'Forestry', 'ZE': 'Horticulture', 'ZF': 'Fisheries',
            'ZG': 'Technology - General', 'ZH': 'Mechanical Engineering', 'ZI': 'Electrical Engineering',
            'ZJ': 'Civil Engineering', 'ZK': 'Transportation', 'ZL': 'Mining', 'ZM': 'Metallurgy',
            'ZN': 'Chemical Technology', 'ZO': 'Process Engineering', 'ZP': 'Environmental Technology',
            'ZQ': 'Energy Technology', 'ZR': 'Home Economics', 'ZX': 'Sports - General',
            'ZY': 'Sports Categories'
        }
    }
}

# Adjusted REGIONAL_INDICATORS to directly map sub-national to national level where appropriate
# Removed "lokal" as a top-level indicator.
REGIONAL_INDICATORS = {
    'deutschland': ['deutschland', 'german', 'bundesrepublik', 'brd', 'deutsche', 'sachsen', 'chemnitz', 'dresden', 'leipzig', 'ostdeutschland', 'bayern', 'münchen', 'nürnberg', 'nrw', 'nordrhein-westfalen', 'köln', 'düsseldorf', 'dortmund', 'essen', 'baden-württemberg', 'stuttgart', 'karlsruhe', 'mannheim', 'hessen', 'frankfurt', 'wiesbaden', 'kassel', 'darmstadt', 'niedersachsen', 'hannover', 'braunschweig', 'göttingen'],
    'europa': ['europa', 'european', 'eu', 'europäisch'],
    'usa': ['usa', 'america', 'vereinigte staaten', 'amerikanisch', 'new york', 'kalifornien'],
    'großbritannien': ['großbritannien', 'england', 'britain', 'british', 'uk'],
    'frankreich': ['frankreich', 'france', 'französisch', 'paris'],
    'italien': ['italien', 'italy', 'italienisch', 'rom'],
    'spanien': ['spanien', 'spain', 'spanisch', 'madrid'],
    'russland': ['russland', 'russia', 'russisch', 'moskau'],
    'china': ['china', 'chinese', 'chinesisch', 'beijing'],
    'japan': ['japan', 'japanese', 'japanisch', 'tokyo'],
    'brasilien': ['brasilien', 'brazil', 'südamerika', 'buenos aires', 'argentinien'], # Added Buenos Aires and Argentina as example for South America/Brazil if relevant
    'afrika': ['afrika', 'african', 'afrikanisch'],
    'asien': ['asien', 'asian', 'asiatisch'],
    'global': ['international', 'global', 'weltweit', 'transnational'],
    # No 'lokal' key anymore, as specific cities/regions are mapped to countries.
}

# A reverse map to quickly find the canonical country for a city/state for display purposes
COUNTRY_MAP_FOR_DISPLAY = {}
for country, cities_regions in REGIONAL_INDICATORS.items():
    if country not in ['europa', 'afrika', 'asien', 'global']: # Exclude continents/global from direct mapping
        for item in cities_regions:
            # Only map if the item is not already a country name itself to avoid self-mapping/confusion
            if item not in [c for c in REGIONAL_INDICATORS.keys() if c not in ['europa', 'afrika', 'asien', 'global']]:
                COUNTRY_MAP_FOR_DISPLAY[item] = country


FORM_INDICATORS = {
    'empirical study': ['empirie', 'studie', 'untersuchung', 'befragung', 'interview', 'feldforschung'],
    'quantitative analysis': ['statistik', 'quantitativ', 'zahlen', 'daten', 'messung', 'survey'],
    'qualitative research': ['qualitativ', 'ethnographie', 'fallstudie', 'narrativ'],
    'theoretical work': ['theorie', 'konzept', 'modell', 'framework', 'ansatz'],
    'comparative study': ['vergleich', 'komparativ', 'international', 'cross-cultural'],
    'handbook': ['handbuch', 'lehrbuch', 'einführung', 'grundlagen'],
    'encyclopedia': ['lexikon', 'wörterbuch', 'enzyklopädie', 'nachschlagewerk'],
    'bibliography': ['bibliographie', 'literaturverzeichnis', 'quellen'],
    'conference proceedings': ['kongress', 'tagung', 'konferenz', 'symposium'],
    'journal': ['zeitschrift', 'journal', 'periodikum'],
    'dissertation': ['dissertation', 'doktorarbeit', 'promotion'],
    'collected volume': ['sammelband', 'herausgeber', 'beiträge', 'aufsätze']
}

EPOCHEN_INDICATORS = {
    'antiquity': ['antike', 'altertum', 'römisch', 'griechisch', 'klassisch'],
    'medieval': ['mittelalter', 'medieval', 'mittelalterlich'],
    'early modern': ['frühe neuzeit', 'renaissance', '16.', '17.'],
    '18th century': ['18.', '1700', 'aufklärung', 'achtzehntes'],
    '19th century': ['19.', '1800', '1900', 'neunzehntes'],
    '20th century': ['20.', '1900', '2000', 'zwanzigstes'],
    '21st century': ['21.', '2000', 'einundzwanzigstes', 'modern', 'zeitgenössisch'],
    'post 1945': ['nach 1945', 'nachkriegszeit', 'bundesrepublik'],
    'post 1989': ['nach 1989', 'wiedervereinigung', 'post-wende'],
    'gdr period': ['ddr', 'deutsche demokratische republik', '1949-1989'],
    'weimar republic': ['weimarer republik', '1918-1933', 'zwischenkriegszeit'],
    'third reich': ['drittes reich', '1933-1945', 'nationalsozialismus'],
    'historical': ['geschichte', 'historisch', 'vergangenheit'],
    'contemporary': ['heute', 'aktuell', 'gegenwart', 'contemporary']
}

# Moved to the top so it's defined before it's imported
def add_hierarchical_methods_to_validator():
    """
    This function adds the hierarchical combination methods to RVKNotationValidator
    Import this file and call this function to extend the validator class
    """
    from config_validator import RVKNotationValidator
    
    RVKNotationValidator.extract_rvk_hierarchical_combinations = extract_rvk_hierarchical_combinations
    RVKNotationValidator.search_with_rvk_hierarchical_combinations = search_with_rvk_hierarchical_combinations
    RVKNotationValidator.search_with_hierarchical_priority_logic = search_with_hierarchical_priority_logic
    RVKNotationValidator.calculate_rvk_combination_relevance = calculate_rvk_combination_relevance
    RVKNotationValidator.ai_analysis = {} # Store AI analysis within the validator for easier access in search methods
    # Adding the new method for child exploration
    RVKNotationValidator.search_children_endpoint_and_validate = search_children_endpoint_and_validate


def extract_rvk_hierarchical_combinations(self, ai_analysis: Dict) -> Dict[str, List[str]]:
    """
    Extract RVK-specific hierarchical combinations based on official RVK structure.
    Maps local terms to country level for regional combinations.
    """
    
    full_text = ' '.join([
        ai_analysis.get('title', ''),
        ai_analysis.get('abstract', ''),
        ai_analysis.get('mainTopic', ''),
        ' '.join(ai_analysis.get('subjects', [])),
        ' '.join(ai_analysis.get('relatedGermanConcepts', []))
    ]).lower()
    
    combinations = {
        'hauptgruppe_context': [],
        'untergruppe_context': [],
        'feingruppe_context': [],
        'regional_schluessel': [], # This will now primarily contain country-level terms
        'form_schluessel': [],
        'epochen_schluessel': []
    }
    
    primary_keyword = ai_analysis.get('primaryKeyword', '').lower()
    
    # === HAUPTGRUPPE CONTEXT ===
    for hauptgruppe, data in HAUPTGRUPPE_MAPPING.items():
        if any(kw in full_text for kw in data['keywords']):
            if primary_keyword:
                combinations['hauptgruppe_context'].append(f"{primary_keyword} + {hauptgruppe} ({data['description']})")
            
            # Add Untergruppe combinations
            for untergruppe, beschreibung in data['untergruppen'].items():
                untergruppe_keywords = data['keywords'] + [beschreibung.lower().split()[0]]
                if any(kw in full_text for kw in untergruppe_keywords):
                    combinations['untergruppe_context'].append(f"{primary_keyword} + {untergruppe} ({beschreibung})")
            
            # Add Feingruppe examples
            for feingruppe_notation, feingruppe_desc in data.get('feingruppen_examples', {}).items():
                feingruppe_keywords = feingruppe_desc.lower().split()
                if any(kw in full_text for kw in feingruppe_keywords):
                    combinations['feingruppe_context'].append(f"{primary_keyword} + {feingruppe_notation} ({feingruppe_desc})")
    
    # === REGIONAL KEYS ===
    found_normalized_regions = set()
    for canonical_region, indicators in REGIONAL_INDICATORS.items():
        if any(indicator in full_text for indicator in indicators):
            found_normalized_regions.add(canonical_region)

    for region_name in sorted(list(found_normalized_regions)): # Sort for consistent output
        if primary_keyword:
            combinations['regional_schluessel'].append(f"{primary_keyword} + {region_name}")
        for subject in ai_analysis.get('subjects', []):
            if subject.lower() != primary_keyword:
                combinations['regional_schluessel'].append(f"{subject.lower()} + {region_name}")
    
    # === FORM KEYS ===
    for form_type, indicators in FORM_INDICATORS.items():
        if any(indicator in full_text for indicator in indicators):
            if primary_keyword:
                combinations['form_schluessel'].append(f"{primary_keyword} + {form_type}")
    
    # === TIME PERIOD KEYS ===
    for epoche, indicators in EPOCHEN_INDICATORS.items():
        if any(indicator in full_text for indicator in indicators):
            if primary_keyword:
                combinations['epochen_schluessel'].append(f"{primary_keyword} + {epoche}")
    
    return combinations

def search_children_endpoint_and_validate(self, notation: str, current_depth: int, max_depth: int, 
                                          parent_relevance: float, primary_keyword: str, 
                                          regional_preferences: List[str], seen_notations: set) -> List[Dict]:
    """
    Recursively searches the RVK /children endpoint for a given notation up to a max_depth.
    Evaluates children relevance based on parent relevance and keyword/regional matches.
    """
    if current_depth >= max_depth: # Changed from > to >= to respect max_depth as inclusive
        return []

    children_results = []
    try:
        # For notations like "LB 56000 - LB 56730", the children endpoint might expect "LB 56000"
        # We need to extract the base notation for the children endpoint.
        base_notation_match = re.match(r'([A-Z]+\s+\d+)', notation)
        if base_notation_match:
            encoded_notation = requests.utils.quote(base_notation_match.group(1).strip())
        else: # For single notations like 'MN', 'MT 27400'
            encoded_notation = requests.utils.quote(notation.strip())

        url = f"{self.rvk_config['base_url']}/{self.rvk_config['format']}/children/{encoded_notation}"
        
        headers = {'Accept': 'application/xml'}
        response = requests.get(url, headers=headers, timeout=5) 
        
        if response.ok:
            root = ET.fromstring(response.text)
            child_elements = root.findall('node')
            
            for child_element in child_elements:
                child_notation = child_element.get('notation')
                child_benennung = child_element.get('benennung')
                
                if not child_notation or child_notation in seen_notations:
                    continue
                
                seen_notations.add(child_notation)
                
                child_hierarchical_path = self.get_hierarchical_path(child_notation)
                child_path_and_benennung_lower = (child_benennung + " " + " ".join([d.get('benennung', '') for d in child_hierarchical_path])).lower()
                
                # Re-evaluate keyword and regional scores for the child
                child_keyword_score = self.calculate_relevance_for_description([primary_keyword], child_benennung)
                
                child_regional_score = 0
                for i, region_level in enumerate(['deutschland', 'usa', 'europa', 'global']): # Simplified chain for children scoring
                    if region_level in child_path_and_benennung_lower or \
                       any(ind in child_path_and_benennung_lower for ind in REGIONAL_INDICATORS.get(region_level, [])):
                        child_regional_score = 50 - (i * 5) # Adjusted base score
                        if region_level in regional_preferences:
                            child_regional_score += 20 # Bonus if recognized region from AI matches
                        break
                
                primary_keyword_match_in_child = False
                if primary_keyword.lower() in child_benennung.lower():
                    primary_keyword_match_in_child = True
                else:
                    for related_concept in self.ai_analysis.get('relatedGermanConcepts', []):
                        if related_concept.lower() in child_path_and_benennung_lower:
                            primary_keyword_match_in_child = True
                            break

                if not primary_keyword_match_in_child:
                    child_regional_score *= 0.1 # Heavily penalize regional if theme is missing

                # Combine scores for child. Children should be more specific.
                # Give a higher thematic weight to children.
                child_final_score = (child_keyword_score * 0.7) + (child_regional_score * 0.3) 
                
                # Ensure a child's score is at least a percentage of its parent's score if it's relevant
                min_child_score_from_parent = parent_relevance * 0.6 # Child must be at least 60% as relevant as parent
                child_final_score = max(min_child_score_from_parent, child_final_score)
                child_final_score = min(100, max(10, int(child_final_score)))

                # --- NEUE LOGIK: ZUSÄTZLICHER BONUS FÜR SPEZIFISCHE LÄNDER-NOTATIONEN ---
                # Wenn das Kind eine Länder-Notation ist (z.B. LB 56015) und das Land von der AI erkannt wurde,
                # und der primäre Keyword passt, dann geben wir einen signifikanten Bonus.
                if primary_keyword_match_in_child and found_regional_level_in_notation == 'deutschland' and 'deutschland' in regional_preferences:
                    child_final_score = min(100, child_final_score + 30) # Starker Bonus für "Deutschland" Match
                elif primary_keyword_match_in_child and found_regional_level_in_notation in ['usa', 'frankreich', 'großbritannien', 'italien', 'spanien', 'russland', 'china', 'japan', 'brasilien'] and found_regional_level_in_notation in regional_preferences:
                    child_final_score = min(100, child_final_score + 25) # Starker Bonus für andere Länder-Matches
                # --- ENDE NEUE LOGIK ---

                children_results.append({
                    'notation': child_notation,
                    'benennung': child_benennung,
                    'relevance': child_final_score,
                    'combination_used': f"Child of {notation}",
                    'combination_type': 'child_exploration',
                    'search_strategy': f"Child Exploration (Depth {current_depth+1})",
                    'reasoning': f"Refined search from parent '{notation}', relevant to '{primary_keyword}'",
                    'priority_weight': child_final_score / 100,
                    'rvk_hierarchy_level': self.determine_rvk_hierarchy_level(child_notation),
                    'hierarchical_path': child_hierarchical_path,
                    'path_display': self.format_hierarchical_path(child_hierarchical_path),
                    'hauptgruppe_match': False # Children don't get 'hauptgruppe_match' based on their own prefix, but parent's
                })

                # Recursively search children's children if within depth and it's a broad category
                if current_depth + 1 < max_depth and self.determine_rvk_hierarchy_level(child_notation) in ["Hauptgruppe", "Untergruppe"]: 
                     children_results.extend(
                         self.search_children_endpoint_and_validate(
                             child_notation, current_depth + 1, max_depth, 
                             child_final_score, primary_keyword, regional_preferences, seen_notations
                         )
                     )

    except Exception as e:
        # print(f"Error searching children for {notation}: {e}") # For debugging
        pass
    
    return children_results


def search_with_hierarchical_priority_logic(self, keyword_combinations: Dict[str, List[str]]) -> List[Dict]:
    """
    NEW: Search RVK using hierarchical priority logic, including child node exploration.
    1. Find Hauptgruppe (M, L etc.) based on AI analysis.
    2. Search within identified Hauptgruppe(n) for the primary keyword.
    3. Explore children of top broad notations for more specific matches.
    4. Check hierarchical path for regional indicators (Deutschland, USA, etc.).
    5. Apply priority scores based on Hauptgruppe match, regional relevance, and thematic keyword match.
    6. Display full hierarchy path.
    """
    all_results = []
    seen_notations = set()
    
    # Step 1: Identify priority Hauptgruppen from AI analysis
    priority_hauptgruppen = []
    for combination in keyword_combinations.get('hauptgruppe_context', []):
        if ' + ' in combination:
            hauptgruppe_match = re.search(r'\+ ([A-Z]) ', combination)
            if hauptgruppe_match:
                hauptgruppe = hauptgruppe_match.group(1).strip()
                if hauptgruppe not in priority_hauptgruppen:
                    priority_hauptgruppen.append(hauptgruppe)
    
    # Step 2: Extract primary keyword and regional preferences (now already normalized to countries/continents)
    primary_keyword = ""
    regional_preferences_from_analysis = [] 
    
    for combination in keyword_combinations.get('regional_schluessel', []):
        if ' + ' in combination:
            parts = combination.split(' + ')
            if not primary_keyword:
                primary_keyword = parts[0]
            regional_preferences_from_analysis.append(parts[1]) 
    
    if not primary_keyword:
        for combo_type, combinations in keyword_combinations.items():
            if combinations:
                first_part = combinations[0].split(' + ')[0] 
                if first_part:
                    primary_keyword = first_part
                    break

    if not primary_keyword:
        primary_keyword = self.ai_analysis.get('primaryKeyword', 'gesellschaft') 
    
    # Step 3: Define regional priority for scoring logic (order matters for bonus application)
    regional_scoring_chain = [
        'deutschland', 'usa', 'frankreich', 'großbritannien', 'italien', 'spanien', 'russland', 'china', 'japan', 'brasilien', # Countries
        'europa', 'afrika', 'asien', 'global', # Continents/Global
    ] 

    # Collect all search terms to initially query the RVK API
    all_search_terms = [primary_keyword] + self.ai_analysis.get('suggestedSearchTerms', [])
    for country in set(regional_preferences_from_analysis): 
        all_search_terms.append(f"{primary_keyword} {country}")
    
    all_search_terms = list(set([term.strip() for term in all_search_terms if term.strip()]))

    # Get all potential results using the general search endpoint
    initial_potential_results = self.search_nodes_endpoint_and_validate(all_search_terms, None)
    
    # Add initial results to all_results and seen_notations
    for result in initial_potential_results:
        if result['notation'] not in seen_notations:
            seen_notations.add(result['notation'])
            # Temporarily add, will update scores later
            all_results.append(result) 

    # Step 4: Explore children of top broad notations
    MAX_CHILD_EXPLORATION_DEPTH = 1 # Explore direct children only (Level 1 from parent)
    TOP_N_FOR_CHILD_EXPLORATION = 5 # Check children only for the top N initial results

    # Sort initial results by relevance to pick the best candidates for child exploration
    initial_potential_results.sort(key=lambda x: x.get('relevance', 0), reverse=True)

    for i, top_result in enumerate(initial_potential_results[:TOP_N_FOR_CHILD_EXPLORATION]):
        # Identify if this is a broad category that might have relevant children
        is_broad_category = False
        notation_level = self.determine_rvk_hierarchy_level(top_result['notation'])
        if notation_level in ["Hauptgruppe", "Untergruppe"] or (" - " in top_result['notation'] and len(top_result['notation'].split()) > 1): # Include explicit ranges
            is_broad_category = True
        
        if is_broad_category:
            children_of_top_result = self.search_children_endpoint_and_validate(
                top_result['notation'], 0, MAX_CHILD_EXPLORATION_DEPTH,
                top_result.get('relevance', 0), primary_keyword, 
                regional_preferences_from_analysis, seen_notations
            )
            for child_result in children_of_top_result:
                if child_result['notation'] not in seen_notations:
                    seen_notations.add(child_result['notation'])
                    all_results.append(child_result)

    # Step 5: Recalculate scores for all collected results (initial + children)
    final_results_with_scores = []
    for result in all_results: # Iterate through all collected results (initial and children)
        # Recalculate scores to ensure consistent weighting after child exploration
        hierarchical_path = self.get_hierarchical_path(result['notation'])
        path_and_benennung_lower = (result['benennung'] + " " + " ".join([d.get('benennung', '') for d in hierarchical_path])).lower()
        
        hauptgruppe_score = 0
        notation_hauptgruppe_prefix = result['notation'][0].upper() if result['notation'] else ''
        
        if notation_hauptgruppe_prefix in priority_hauptgruppen:
            hauptgruppe_score = 100
        elif notation_hauptgruppe_prefix in ['M', 'L']:
            hauptgruppe_score = 80
        else:
            hauptgruppe_score = 20
        
        regional_score = 0
        found_regional_level_in_notation = None 
        for i, region_level in enumerate(regional_scoring_chain):
            if region_level in path_and_benennung_lower or \
               any(ind in path_and_benennung_lower for ind in REGIONAL_INDICATORS.get(region_level, [])):
                regional_score_base = 50 - (i * 2) 
                found_regional_level_in_notation = region_level
                break 
        
        if found_regional_level_in_notation and found_regional_level_in_notation in regional_preferences_from_analysis:
            regional_score = regional_score_base + 40 
        elif found_regional_level_in_notation:
            regional_score = regional_score_base + 10 
        
        keyword_score = self.calculate_relevance_for_description([primary_keyword], result['benennung'])
        
        primary_keyword_match_in_rvk = False
        if primary_keyword.lower() in result['benennung'].lower():
            primary_keyword_match_in_rvk = True
        else:
            for related_concept in self.ai_analysis.get('relatedGermanConcepts', []):
                if related_concept.lower() in path_and_benennung_lower:
                    primary_keyword_match_in_rvk = True
                    break

        if not primary_keyword_match_in_rvk:
            regional_score *= 0.05 
            hauptgruppe_score *= 0.5 

        final_score = (hauptgruppe_score * 0.3) + (regional_score * 0.25) + (keyword_score * 0.45) 
        final_score = max(10, min(100, int(final_score))) 

        if keyword_score > 70 and primary_keyword_match_in_rvk:
            final_score = min(100, final_score + 15)

        # Clean up regional_preferences_from_analysis for display
        display_regions_set = set()
        for ai_rec_region in regional_preferences_from_analysis:
            display_regions_set.add(ai_rec_region) 
        display_regions = ", ".join(sorted(list(display_regions_set))) if display_regions_set else "None"


        result.update({
            'relevance': final_score, 
            'combination_used': result.get('combination_used', f"{primary_keyword} in {notation_hauptgruppe_prefix}"), 
            'combination_type': result.get('combination_type', 'hierarchical_priority'),
            'search_strategy': result.get('search_strategy', f"Hierarchical Priority Search (Hauptgruppe: {notation_hauptgruppe_prefix})"),
            'reasoning': f"Priority: Hauptgruppe {notation_hauptgruppe_prefix}, Regional context: [{display_regions}]", 
            'priority_weight': final_score / 100, 
            'rvk_hierarchy_level': self.determine_rvk_hierarchy_level(result['notation']),
            'hierarchical_path': hierarchical_path,
            'path_display': self.format_hierarchical_path(hierarchical_path), 
            'hauptgruppe_match': notation_hauptgruppe_prefix in priority_hauptgruppen
        })
        final_results_with_scores.append(result)
    
    final_results_with_scores.sort(key=lambda x: x.get('relevance', 0), reverse=True)
    
    return final_results_with_scores[:12]


def search_with_rvk_hierarchical_combinations(self, keyword_combinations: Dict[str, List[str]]) -> List[Dict]:
    """Use the new hierarchical priority logic"""
    return self.search_with_hierarchical_priority_logic(keyword_combinations)


def calculate_rvk_combination_relevance(self, search_terms: List[str], notation: str, 
                                       rvk_description: str, combination_type: str, 
                                       priority_weight: float) -> int:
    """Calculate relevance specifically for RVK hierarchical combinations"""
    base_score = 0
    rvk_desc_lower = rvk_description.lower()
    
    term_matches = sum(1 for term in search_terms if term.lower() in rvk_desc_lower)
    match_ratio = term_matches / len(search_terms) if search_terms else 0
    
    base_score = int(match_ratio * 70)
    
    structure_bonuses = {
        'hierarchical_priority': 30,
        'regional_schluessel': 25,
        'hauptgruppe_context': 20,
        'untergruppe_context': 18,
        'feingruppe_context': 15,
        'epochen_schluessel': 12,
        'form_schluessel': 10,
        'child_exploration': 10 # Added bonus for results coming from child exploration
    }
    
    base_score += structure_bonuses.get(combination_type, 0)
    
    notation_parts = notation.split()
    if len(notation_parts) == 2:
        letters, numbers = notation_parts[0], notation_parts[1]
        if letters.isalpha() and numbers.isdigit():
            base_score += 15
    elif len(notation_parts) == 1 and len(notation_parts[0]) == 2:
        base_score += 10
    elif len(notation_parts) >= 3:
        base_score += 8
    
    final_score = int(base_score * priority_weight)
    
    if match_ratio >= 0.8:
        final_score += 15
    
    return min(100, max(10, final_score))