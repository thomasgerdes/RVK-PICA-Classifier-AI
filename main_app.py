"""
main_app.py
Main Streamlit Application
Part 3/3 of RVK-PICA Classifier AI v1.1
"""

import streamlit as st
import requests
import json
import re
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import xml.etree.ElementTree as ET

# Import our modules
from config_validator import ConfigManager, RVKNotationValidator
from rvk_hierarchical_combinations import add_hierarchical_methods_to_validator

# Add hierarchical methods to validator
add_hierarchical_methods_to_validator()

# Page configuration
st.set_page_config(
    page_title="RVK-PICA Classifier AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Custom CSS for modern, clean design
st.markdown("""
<style>
    /* Main layout */
    .main-header {
        text-align: center;
        color: #1a1a1a;
        margin-bottom: 3rem;
        font-weight: 300;
    }
    
    /* Modern card design */
    .analysis-box {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1.5rem 0;
    }
    
    .suggestion-card {
        border: 1px solid #dee2e6;
        border-radius: 6px;
        padding: 1rem;
        margin: 0.75rem 0;
        background: #ffffff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Status indicators */
    .api-status {
        padding: 0.5rem 1rem;
        border-radius: 4px;
        margin: 0.25rem;
        display: inline-block;
        font-size: 0.9rem;
        font-weight: 500;
    }
    .api-active { 
        background: #d1f2d1; 
        color: #0d5016; 
        border: 1px solid #c3e6c3;
    }
    .api-inactive { 
        background: #f8d7da; 
        color: #721c24; 
        border: 1px solid #f1aeb5;
    }
    
    /* Results cards */
    .verified-notation {
        border-left: 3px solid #6c757d;
        background: #ffffff;
        margin: 0.5rem 0;
    }
    .hauptgruppe-match {
        border-left: 3px solid #495057;
        background: #f8f9fa;
        margin: 0.5rem 0;
    }
    
    /* Compact design */
    .result-header {
        margin-bottom: 0.5rem;
    }
    .result-details {
        font-size: 0.9rem;
        color: #6c757d;
        margin: 0.25rem 0;
    }
    
    /* Typography */
    .metric-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 6px;
        margin: 0.5rem 0;
        border: 1px solid #e9ecef;
    }
    
    /* Compact sidebar */
    .sidebar-section {
        margin-bottom: 1rem;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 4px;
        border: 1px solid #dee2e6;
        font-weight: 500;
        padding: 0.375rem 0.75rem;
    }
    
    /* Primary button less dominant */
    .stButton > button[kind="primary"] {
        background-color: #495057;
        border-color: #495057;
    }
    
    /* Reduce visual noise */
    .stAlert {
        border-radius: 4px;
    }
    
    /* Clean footer */
    .footer-clean {
        text-align: center;
        color: #6c757d;
        margin-top: 3rem;
        padding-top: 2rem;
        border-top: 1px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)


class RVKClassifierAI:
    """Main AI-powered RVK classifier with hierarchical understanding"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.session_state = st.session_state
        
        # Initialize config and results in session_state if they don't exist
        if 'config' not in self.session_state:
            self.session_state.config = self.config_manager.load_config()
        if 'results' not in self.session_state:
            self.session_state.results = None
        
        self.notation_validator = RVKNotationValidator(self.session_state.config['rvk'])
    
    def save_current_config(self):
        """Save current configuration to persistent storage"""
        return self.config_manager.save_config(self.session_state.config)
    
    def parse_pica_data(self, pica_data: str) -> Dict:
        """Parse and structure PICA data from K10plus format"""
        lines = [line.strip() for line in pica_data.split('\n') if line.strip()]
        parsed = {}
        
        for line in lines:
            match = re.match(r'^(\d{4})\s+(.+)$', line)
            if match:
                field = match.group(1)
                content = match.group(2)
                
                subfields = {}
                for sf_match in re.finditer(r'\$([a-z])([^$]*)', content):
                    code = sf_match.group(1)
                    value = sf_match.group(2).strip()
                    subfields[code] = value
                
                if field not in parsed:
                    parsed[field] = []
                main_content = subfields.get('a', content)
                parsed[field].append(main_content)
        
        return parsed
    
    def analyze_with_openai(self, pica_data: str) -> Dict:
        """Analyze PICA data using OpenAI API for intelligent content extraction"""
        config = self.session_state.config['openai']
        
        prompt = f"""
Analyze the following PICA library data for RVK classification.
Focus on identifying core topics, disciplines, and key concepts.

PICA Data:
{pica_data}

Return a structured JSON response with the following keys. Ensure values are accurate and relevant for library classification in the German context (RVK).

- title: Main title of the work
- author: Author(s)
- year: Publication year
- publisher: Publisher
- subjects: Array of German keywords (focus on key concepts for classification, e.g. 'Künstliche Intelligenz', 'Medizinische Informatik', 'Migration', 'Sozialwissenschaften')
- abstract: Summary, if available
- mainTopic: Main topic in a few words (e.g. 'KI im Gesundheitswesen', 'Migrationsstudien', 'Stadtsoziologie')
- primaryKeyword: The most important and representative German keyword/concept of the document (e.g. 'Migration', 'Künstliche Intelligenz', 'Medizinische Diagnostik'). This should be a precise term.
- relatedGermanConcepts: Array of German related and synonymous concepts for RVK search, based on primaryKeyword and mainTopic. Examples for Migration: ['Zuwanderung', 'Einwanderung', 'Auswanderung', 'Integrationsprozesse', 'Flüchtlinge', 'Gesellschaftlicher Wandel', 'Kulturtransfer'].
- discipline: Main academic discipline (e.g. 'Informatik', 'Medizin', 'Soziologie', 'Politikwissenschaft')
- suggestedSearchTerms: Array of optimal German search terms for RVK search, including specific keywords from PICA data, broader academic concepts. Prioritize terms likely to be found in the RVK system. Examples: ['Migration', 'Zuwanderung', 'Interkultureller Mehrwert', 'Soziologie', 'Stadtforschung', 'Integrationsprozesse']
- suggestedRVKPrefixes: Array of 1 to 3 relevant RVK notation prefixes (e.g. 'ST', 'L', 'M', 'MS', 'NP', 'NZ') based on identified discipline and main topic. Focus on prefixes that broadly cover the subject area. For 'Migration' or 'Soziologie' think of prefixes like 'L', 'M', 'NP', 'NZ'. Return empty array if no strong prefix recommendation.
- relevantRVKHierarchyExamples: Array of 1 to 3 specific RVK notations (e.g. 'L 1000', 'M 100', 'NP 350', 'LB 56015') die für das primaryKeyword oder mainTopic hochrelevant sind und als gute Ausgangspunkte für die hierarchische Erkundung dienen. Gib ein leeres Array zurück, wenn du unsicher bist.
- confidence: Analysis quality assessment (1-100)

Respond only with valid JSON without additional text or conversational elements.
"""

        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {config['api_key']}"
            }
            
            response = requests.post(
                f"{config['base_url']}/chat/completions",
                headers=headers,
                json={
                    'model': config['model'],
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': config['temperature'],
                    'max_tokens': config['max_tokens']
                },
                timeout=30
            )
            
            if response.ok:
                data = response.json()
                content = data['choices'][0]['message']['content']
                
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    return json.loads(json_match.group(0))
                
            raise Exception(f"OpenAI API Error: {response.status_code} - {response.text}")
            
        except Exception as e:
            st.error(f"OpenAI API call failed: {e}") 
            raise e 
    
    def create_fallback_analysis(self, parsed_data: Dict) -> Dict:
        """Create fallback analysis when AI analysis is not available"""
        return {
            'title': parsed_data.get('4000', ['Unknown Title'])[0],
            'author': parsed_data.get('3000', ['Unknown Author'])[0],
            'year': parsed_data.get('1100', ['Unknown Year'])[0],
            'publisher': parsed_data.get('4030', ['Unknown Publisher'])[0],
            'mainTopic': 'General Research', 
            'primaryKeyword': 'Gesellschaft', 
            'relatedGermanConcepts': ['Kultur', 'Sozialer Wandel', 'Migration'],
            'subjects': ['Technologie', 'Informatik', 'Wissenschaft', 'Gesellschaft'],
            'suggestedSearchTerms': ['Informatik', 'Medizin', 'Forschung', 'Allgemein', 'Wissenschaft', 'Gesellschaft', 'Migration'], 
            'discipline': 'Interdisciplinary',
            'suggestedRVKPrefixes': [], 
            'relevantRVKHierarchyExamples': [], 
            'confidence': 30 
        }
    
    def analyze_pica_data_with_rvk_hierarchy(self, pica_data: str) -> Dict:
        """Enhanced analysis using official RVK hierarchical structure"""
        
        # Steps 1-2: Parse PICA and AI analysis
        parsed_data = self.parse_pica_data(pica_data)
        
        analyzed_data = {}
        ai_enabled_actual = False
        if (self.session_state.config['openai']['enabled'] and 
            self.session_state.config['openai']['api_key']):
            try:
                analyzed_data = self.analyze_with_openai(pica_data)
                ai_enabled_actual = True
            except Exception as e:
                st.warning(f"OpenAI analysis failed, using fallback: {e}")
                analyzed_data = self.create_fallback_analysis(parsed_data)
                ai_enabled_actual = False
        else:
            analyzed_data = self.create_fallback_analysis(parsed_data)
            ai_enabled_actual = False
        
        # Pass AI analysis to the validator for more informed search
        self.notation_validator.ai_analysis = analyzed_data
        
        # Step 3: RVK hierarchical combination analysis
        suggestions = []
        rvk_combinations = {} 
        
        if self.session_state.config['rvk']['enabled']:
            # Extract RVK-specific hierarchical combinations
            rvk_combinations = self.notation_validator.extract_rvk_hierarchical_combinations(analyzed_data)
            
            # Search with NEW hierarchical priority logic
            suggestions = self.notation_validator.search_with_rvk_hierarchical_combinations(rvk_combinations)
            
            # Emergency fallback if no results
            if not suggestions:
                emergency_terms = ['gesellschaft', 'wissenschaft', 'forschung']
                emergency_results = self.notation_validator.search_nodes_endpoint_and_validate(emergency_terms)
                for result in emergency_results:
                    result.update({
                        'relevance': 25,
                        'combination_used': 'Emergency fallback',
                        'combination_type': 'emergency',
                        'reasoning': 'Emergency fallback - no combination matches found',
                        'hierarchical_path': self.notation_validator.get_hierarchical_path(result['notation']),
                        'path_display': self.notation_validator.format_hierarchical_path(self.notation_validator.get_hierarchical_path(result['notation'])),
                        'rvk_hierarchy_level': self.notation_validator.determine_rvk_hierarchy_level(result['notation']),
                        'hauptgruppe_match': False 
                    })
                    suggestions.append(result)
        
        else:
            st.warning("RVK API is disabled. Enable it in settings for classification.")
        
        return {
            **analyzed_data,
            'parsedPica': parsed_data,
            'suggestions': suggestions[:12], 
            'rvk_combinations_used': rvk_combinations, 
            'apiUsed': {
                'ai': 'OpenAI' if ai_enabled_actual else 'Fallback',
                'rvk': 'RVK Hierarchical Priority Analysis' if self.session_state.config['rvk']['enabled'] else 'Disabled'
            }
        }

    def display_rvk_hierarchical_suggestions(self, results):
        """Display suggestions with RVK hierarchical structure information and full hierarchy paths"""
        if results['suggestions']:
            hauptgruppe_matches = []
            other_matches = []
            
            for suggestion in results['suggestions']:
                if suggestion.get('hauptgruppe_match', False):
                    hauptgruppe_matches.append(suggestion)
                else:
                    other_matches.append(suggestion)
            
            if hauptgruppe_matches:
                st.markdown("#### Priority Matches")
                
                for i, suggestion in enumerate(hauptgruppe_matches):
                    with st.container():
                        relevance = suggestion.get('relevance', 0)
                        
                        st.markdown(f"""
                        <div class="hauptgruppe-match">
                            <div class="result-header">
                                <h4 style="margin: 0;">{suggestion['notation']} - {suggestion['benennung']}</h4>
                            </div>
                            <div class="result-details">
                                <strong>Relevance:</strong> {relevance}% | <strong>Level:</strong> {suggestion.get('rvk_hierarchy_level', 'Unknown')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Technical details in expander
                        with st.expander("Details", expanded=False):
                            st.write(f"**Search Strategy:** {suggestion.get('search_strategy', 'Standard')}")
                            st.write(f"**Logic:** {suggestion.get('reasoning', 'N/A')}")
                            
                            hierarchical_display = self.format_hierarchical_display(suggestion)
                            if hierarchical_display:
                                st.write("**RVK Hierarchy:**")
                                # Shorten long hierarchy paths
                                if len(hierarchical_display) > 200:
                                    parts = hierarchical_display.split(" → ")
                                    if len(parts) > 3:
                                        shortened = f"{parts[0]} → ... → {parts[-2]} → {parts[-1]}"
                                        st.code(shortened, language='text')
                                    else:
                                        st.code(hierarchical_display, language='text')
                                else:
                                    st.code(hierarchical_display, language='text')
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(f"Copy {suggestion['notation']}", key=f"copy_priority_{i}"):
                                st.code(suggestion['notation'])
                        with col_b:
                            encoded_notation = requests.utils.quote(suggestion['notation'])
                            st.markdown(f"[RVK Online](https://rvk.uni-regensburg.de/regensburger-verbundklassifikation-online#notation/{encoded_notation})")
            
            if other_matches:
                st.markdown("#### Additional Matches")
                
                for i, suggestion in enumerate(other_matches):
                    with st.container():
                        relevance = suggestion.get('relevance', 0)
                        
                        st.markdown(f"""
                        <div class="verified-notation">
                            <div class="result-header">
                                <h4 style="margin: 0;">{suggestion['notation']} - {suggestion['benennung']}</h4>
                            </div>
                            <div class="result-details">
                                <strong>Relevance:</strong> {relevance}% | <strong>Level:</strong> {suggestion.get('rvk_hierarchy_level', 'Unknown')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Technical details in expander
                        with st.expander("Details", expanded=False):
                            st.write(f"**Search Strategy:** {suggestion.get('search_strategy', 'Standard')}")
                            
                            hierarchical_display = self.format_hierarchical_display(suggestion)
                            if hierarchical_display:
                                st.write("**RVK Hierarchy:**")
                                # Shorten long hierarchy paths
                                if len(hierarchical_display) > 200:
                                    parts = hierarchical_display.split(" → ")
                                    if len(parts) > 3:
                                        shortened = f"{parts[0]} → ... → {parts[-2]} → {parts[-1]}"
                                        st.code(shortened, language='text')
                                    else:
                                        st.code(hierarchical_display, language='text')
                                else:
                                    st.code(hierarchical_display, language='text')
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(f"Copy {suggestion['notation']}", key=f"copy_other_{i}"):
                                st.code(suggestion['notation'])
                        with col_b:
                            encoded_notation = requests.utils.quote(suggestion['notation'])
                            st.markdown(f"[RVK Online](https://rvk.uni-regensburg.de/regensburger-verbundklassifikation-online#notation/{encoded_notation})")
            
            if 'rvk_combinations_used' in results and results['rvk_combinations_used']:
                with st.expander("RVK Structure Analysis", expanded=False):
                    for combo_type, combinations in results['rvk_combinations_used'].items():
                        if combinations:
                            st.write(f"**{combo_type.replace('_', ' ').title()}:** {', '.join(combinations[:3])}")
                            if len(combinations) > 3:
                                st.write(f"... and {len(combinations) - 3} more")

    def format_hierarchical_display(self, suggestion: Dict) -> str:
        """
        Format hierarchical path for enhanced display (e.g., MG (Main Group): Political Science, Sociology → MG-MI (Subgroup): Political Systems of Individual Countries → MG 10000-MG 10999 (Fine Group): Studies on Several Countries → MG 10925 (Fine Group + Key): Migration Policy)
        """
        # Retrieve the full hierarchical path data from the validator
        hierarchical_path_data = self.notation_validator.get_hierarchical_path(suggestion['notation']) 
        
        if not hierarchical_path_data:
            return f"{suggestion['notation']} (No hierarchy available)"
        
        formatted_steps = []
        for level_data in hierarchical_path_data:
            notation = level_data.get('notation', 'N/A')
            benennung = level_data.get('benennung', 'N/A')
            
            # Determine the type of RVK hierarchy level (e.g., Hauptgruppe, Untergruppe)
            hierarchy_level_type = self.notation_validator.determine_rvk_hierarchy_level(notation)
            
            # Truncate long descriptions if necessary for better readability
            if len(benennung) > 70:
                benennung = benennung[:67] + "..."

            # Append each step in the format "Notation (Level Type): Description"
            formatted_steps.append(f"{notation} ({hierarchy_level_type}): {benennung}")
        
        # Join all formatted steps with the " → " separator
        return " → ".join(formatted_steps)


def main():
    """Main function for the Streamlit application"""
    
    classifier = RVKClassifierAI()

    # Initialize Session State keys based on configuration
    # This ensures they exist before checkboxes reference them
    # Important: This initialization must occur before the first st.checkbox call
    if 'openai_enabled_checkbox' not in st.session_state:
        st.session_state.openai_enabled_checkbox = st.session_state.config['openai']['enabled']
    if 'rvk_enabled_checkbox' not in st.session_state:
        st.session_state.rvk_enabled_checkbox = st.session_state.config['rvk']['enabled']

    def update_openai_enabled():
        # Update config value directly from checkbox value in session_state
        st.session_state.config['openai']['enabled'] = st.session_state.openai_enabled_checkbox

    def update_rvk_enabled():
        # Update config value directly from checkbox value in session_state
        st.session_state.config['rvk']['enabled'] = st.session_state.rvk_enabled_checkbox
    
    st.markdown("""
    <div class="main-header">
        <h1>RVK-PICA Classifier AI</h1>
        <p>Intelligent PICA Analysis with RVK Hierarchical Understanding v1.1</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("Configuration")
        
        # OpenAI Section
        st.checkbox("Enable OpenAI", key="openai_enabled_checkbox", on_change=update_openai_enabled)
        openai_enabled = st.session_state.config['openai']['enabled'] 
        
        if openai_enabled:
            st.text_input("API Key", type="password", value=st.session_state.config['openai']['api_key'], key="openai_key")
            st.selectbox("Model", ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'gpt-4o'], 
                        index=['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'gpt-4o'].index(st.session_state.config['openai']['model']) if st.session_state.config['openai']['model'] in ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'gpt-4o'] else 0, key="openai_model")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Test", key="test_openai"):
                    if st.session_state.get('openai_key'):
                        try:
                            response = requests.get(f"{st.session_state.config['openai']['base_url']}/models",
                                                  headers={'Authorization': f"Bearer {st.session_state.openai_key}"}, timeout=10)
                            if response.ok:
                                st.success("✓ OK")
                            else:
                                st.error("✗ Error")
                        except:
                            st.error("✗ Failed")
                    else:
                        st.warning("Key required")
        
        st.markdown("---")
        
        # RVK Section  
        st.checkbox("Enable RVK API", key="rvk_enabled_checkbox", on_change=update_rvk_enabled)
        rvk_enabled = st.session_state.config['rvk']['enabled'] 
        
        if rvk_enabled:
            if st.button("Test RVK", key="test_rvk"):
                try:
                    response = requests.get(f"{classifier.notation_validator.rvk_config['base_url']}/{classifier.notation_validator.rvk_config['format']}/nodes/informatik", timeout=10)
                    if response.ok and ET.fromstring(response.text).find('node') is not None:
                        st.success("✓ RVK OK")
                    else:
                        st.error("✗ RVK Error")
                except:
                    st.error("✗ RVK Failed")
        
        st.markdown("---")
        
        if st.button("Save Config", key="save_config"):
            if 'openai_key' in st.session_state:
                st.session_state.config['openai']['api_key'] = st.session_state.openai_key
            if 'openai_model' in st.session_state:
                st.session_state.config['openai']['model'] = st.session_state.openai_model
            
            if classifier.save_current_config():
                st.success("✓ Saved")
            else:
                st.error("✗ Failed")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### API Status")
        openai_status_text = "Active" if openai_enabled else "Inactive"
        rvk_status_text = "Active" if rvk_enabled else "Inactive"
        
        st.markdown(f"""
        <div style="display: flex; gap: 1rem; margin-bottom: 2rem;">
            <span class="api-status {'api-active' if openai_enabled else 'api-inactive'}">
                OpenAI: {openai_status_text}
            </span>
            <span class="api-status {'api-active' if rvk_enabled else 'api-inactive'}">
                RVK: {rvk_status_text}
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Enter PICA Data")
        
        col_btn1, col_btn2 = st.columns([1, 3])
        with col_btn1:
            if st.button("Load Example", key="load_example"):
                st.session_state.example_loaded = True
        
        example_data = """4000 $aMigration und Integration in Chemnitz: Eine sozialwissenschaftliche Analyse interkultureller Prozesse
4002 $aLokale Dynamiken von Zuwanderung und gesellschaftlichem Wandel
3000 $aDi Pinto, Daniela$9123456789
3000 $aKroll, Frank-Lothar$9987654321
1100 $a2024
4030 $aUniversitätsverlag Chemnitz$nChemnitz
4207 $aDiese Studie untersucht die Auswirkungen von Migration und Zuwanderung auf die Stadt Chemnitz aus sozialwissenschaftlicher Perspektive. Sie analysiert interkulturelle Beziehungen, Integrationsprozesse und den damit verbundenen gesellschaftlichen Wandel, mit Fokus auf lokale Initiativen und Herausforderungen.
5010 $a304.8
5090 $aL 1000$hMigration$jZuwanderung
"""
        
        pica_data = st.text_area(
            "PICA Data:",
            value=example_data if st.session_state.get('example_loaded', False) else "",
            height=280,
            help="Enter PICA data in K10plus format"
        )
        
        if st.button("Start Analysis", type="primary", key="analyze"):
            st.session_state.example_loaded = False 
            if pica_data.strip():
                with st.spinner("Analyzing..."):
                    try:
                        results = classifier.analyze_pica_data_with_rvk_hierarchy(pica_data)
                        st.session_state.results = results
                        st.success("Analysis completed")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter PICA data")
    
    with col2:
        if st.session_state.results:
            st.markdown("### Analysis Summary")
            results = st.session_state.results
            suggestions_count = len(results.get('suggestions', []))
            confidence = results.get('confidence', 0)
            
            st.markdown(f"""
            <div class="metric-container">
                <strong>Suggestions Found</strong><br>
                <span style="font-size: 1.5rem; color: #495057;">{suggestions_count}</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="metric-container">
                <strong>AI Confidence</strong><br>
                <span style="font-size: 1.5rem; color: #495057;">{confidence}%</span>
            </div>
            """, unsafe_allow_html=True)
            
            if suggestions_count > 0:
                hauptgruppe_count = sum(1 for s in results['suggestions'] if s.get('hauptgruppe_match', False))
                st.markdown(f"""
                <div class="metric-container">
                    <strong>Priority Matches</strong><br>
                    <span style="font-size: 1.5rem; color: #495057;">{hauptgruppe_count}</span>
                </div>
                """, unsafe_allow_html=True)
    
    if st.session_state.results:
        results = st.session_state.results
        
        st.markdown("---")
        st.markdown("## RVK Analysis Results")
        
        ai_rvk_prefixes = results.get('suggestedRVKPrefixes', [])
        ai_rvk_prefixes_display = ", ".join(ai_rvk_prefixes) if ai_rvk_prefixes else "None"
        ai_relevant_examples = results.get('relevantRVKHierarchyExamples', [])
        ai_relevant_examples_display = ", ".join(ai_relevant_examples) if ai_relevant_examples else "None"
        ai_related_concepts = results.get('relatedGermanConcepts', [])
        ai_related_concepts_display = ", ".join(ai_related_concepts) if ai_related_concepts else "None"

        st.markdown(f"""
        <div class="analysis-box">
            <h3>AI Analysis ({results['apiUsed']['ai']})</h3>
            <p><strong>Title:</strong> {results.get('title', 'N/A')[:100]}{'...' if len(results.get('title', '')) > 100 else ''}</p>
            <p><strong>Author:</strong> {results.get('author', 'N/A')}</p>
            <p><strong>Topic:</strong> {results.get('mainTopic', 'N/A')} | <strong>Keyword:</strong> {results.get('primaryKeyword', 'N/A')}</p>
            <p><strong>Discipline:</strong> {results.get('discipline', 'N/A')} | <strong>Confidence:</strong> {results.get('confidence', 'N/A')}%</p>
        </div>
        """, unsafe_allow_html=True)
        
        # More details in expander
        with st.expander("Full Analysis Details", expanded=False):
            st.write(f"**Related German Concepts:** {ai_related_concepts_display}")
            st.write(f"**Suggested Search Terms:** {', '.join(results.get('suggestedSearchTerms', []))}")
            st.write(f"**Suggested RVK Prefixes:** {ai_rvk_prefixes_display}")
            st.write(f"**Relevant RVK Hierarchy Examples:** {ai_relevant_examples_display}")
        
        st.markdown(f"### RVK Classification ({results['apiUsed']['rvk']})")
        
        # Display hierarchical suggestions with new logic
        classifier.display_rvk_hierarchical_suggestions(results)
        
        if results['suggestions']:
            with st.expander("Export Options", expanded=False):
                col_exp1, col_exp2, col_exp3 = st.columns(3)
                
                with col_exp1:
                    if st.button("JSON", key="trigger_export_json"):
                        export_data = {
                            'timestamp': datetime.now().isoformat(),
                            'analysis': results,
                            'pica_data': pica_data,
                            'version': '1.1' 
                        }
                        st.download_button(
                            label="Download JSON",
                            data=json.dumps(export_data, indent=2, ensure_ascii=False),
                            file_name=f"rvk-analysis-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                
                with col_exp2:
                    if st.button("CSV", key="trigger_export_csv"):
                        df = pd.DataFrame(results['suggestions'])
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"rvk-suggestions-{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                
                with col_exp3:
                    all_notations_string = ", ".join([s['notation'] for s in results['suggestions']])
                    if st.button("Copy All", key="copy_all_notations"):
                        st.code(all_notations_string, language='text')
        
        else:
            st.warning("No matching RVK classifications found.")
            with st.expander("Suggestions", expanded=False):
                st.write("- Enable RVK API in the sidebar")
                st.write("- Check API Status using the test buttons") 
                st.write("- Add more detailed information in PICA data")
                st.write("- Review AI-suggested keywords and main topic")
    
    st.markdown("""
    <div class="footer-clean">
        <p><strong><a href="https://github.com/thomasgerdes/RVK-PICA-Classifier-AI" target="_blank" style="color: #495057; text-decoration: none;">RVK-PICA Classifier AI v1.1</a></strong> - By <a href="https://github.com/thomasgerdes/RVK-PICA-Classifier-AI" target="_blank" style="color: #495057; text-decoration: none;">Thomas Gerdes</a></p>
        <p style="font-size: 0.85rem; color: #868e96; margin-top: 1rem;">
            All data processed securely – API keys stored locally only
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
