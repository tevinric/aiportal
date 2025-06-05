import streamlit as st
import os
import openai
import pandas as pd
import json
from datetime import datetime
import io
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass
import sqlite3
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure OpenAI Configuration
class AzureOpenAIConfig:
    def __init__(self):
        self.api_base = os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.environ.get("AZURE_OPENAI_KEY")
        self.api_version = "2024-02-15-preview"
        
    def initialize_client(self):
        client = openai.AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.api_base
        )
        return client

@dataclass
class TestSuite:
    id: str
    name: str
    description: str
    created_by: str
    created_at: datetime
    scenarios: List[Dict]
    tags: List[str]
    version: str
    brd_content: Optional[str] = None
    requirements: Optional[str] = None

class DatabaseManager:
    def __init__(self, db_path: str = "test_manager.db"):
        self.db_path = db_path
        self.initialize_database()
    
    def initialize_database(self):
        """Initialize the database and create tables if they don't exist"""
        try:
            db_exists = Path(self.db_path).exists()
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            
            if not db_exists:
                logger.info("Creating new database...")
                self.create_tables()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def create_tables(self):
        """Create all necessary tables in the database"""
        try:
            with self.conn:
                # Test Suites table
                self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS test_suites (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        created_by TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        scenarios TEXT NOT NULL,
                        tags TEXT,
                        version TEXT NOT NULL,
                        brd_content TEXT,
                        requirements TEXT,
                        last_modified TIMESTAMP,
                        last_modified_by TEXT
                    )
                ''')
                
                # Comments table
                self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS comments (
                        id TEXT PRIMARY KEY,
                        suite_id TEXT NOT NULL,
                        scenario_id TEXT NOT NULL,
                        user TEXT NOT NULL,
                        comment TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (suite_id) REFERENCES test_suites (id)
                    )
                ''')
                
                # Coverage mapping table
                self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS coverage_mapping (
                        id TEXT PRIMARY KEY,
                        suite_id TEXT NOT NULL,
                        requirement_id TEXT NOT NULL,
                        scenario_ids TEXT NOT NULL,
                        coverage_percentage REAL NOT NULL,
                        last_updated TIMESTAMP NOT NULL,
                        FOREIGN KEY (suite_id) REFERENCES test_suites (id)
                    )
                ''')
                
                # User settings table
                self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS user_settings (
                        user_id TEXT PRIMARY KEY,
                        username TEXT NOT NULL,
                        preferences TEXT,
                        last_login TIMESTAMP,
                        created_at TIMESTAMP NOT NULL
                    )
                ''')
                
                # Test execution history
                self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS execution_history (
                        id TEXT PRIMARY KEY,
                        suite_id TEXT NOT NULL,
                        scenario_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        executed_by TEXT NOT NULL,
                        executed_at TIMESTAMP NOT NULL,
                        duration INTEGER,
                        notes TEXT,
                        FOREIGN KEY (suite_id) REFERENCES test_suites (id)
                    )
                ''')
                
            logger.info("All tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            raise

class TestScenarioGenerator:
    def __init__(self, client):
        self.client = client
        
    def generate_scenarios(self, user_story, test_type, complexity, requirements, brd_content=None):
        system_prompt = """You are a test scenario generator that creates detailed test scenarios in JSON format.
        Always ensure your response is valid JSON and follows the exact structure provided."""
        
        # Add BRD context if provided
        if brd_content:
            system_prompt += """
            Consider the following Business Requirements Document while generating test scenarios:
            {}
            Ensure all test scenarios align with these business requirements.""".format(brd_content)
        
        user_prompt = f"""Create test scenarios for this user story. Respond ONLY with a JSON object containing an array of test scenarios.

User Story: {user_story}
Test Type: {test_type}
Complexity Level: {complexity}
Additional Requirements: {requirements}

The JSON must follow this exact structure:
{{
    "scenarios": [
        {{
            "scenario_id": "TS001",
            "title": "Scenario title",
            "preconditions": ["list of preconditions"],
            "steps": ["list of steps"],
            "expected_results": ["list of expected results"],
            "test_data": ["required test data"],
            "priority": "High/Medium/Low",
            "complexity": "complexity level",
            "estimated_duration": "in minutes",
            "requirements_covered": ["list of requirements covered"],
            "tags": ["relevant tags"]
        }}
    ]
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                response_format={ "type": "json_object" }
            )
            
            response_content = response.choices[0].message.content
            
            try:
                scenarios = json.loads(response_content)
                if not isinstance(scenarios, dict) or "scenarios" not in scenarios:
                    raise ValueError("Invalid JSON structure: missing 'scenarios' key")
                return scenarios
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON response from API: {str(e)}")
                st.code(response_content)
                raise ValueError(f"Invalid JSON response: {str(e)}")
                
        except Exception as e:
            st.error(f"Error calling Azure OpenAI API: {str(e)}")
            raise

class TestScenarioManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        
    def create_test_suite(self, name: str, description: str, scenarios: List[Dict], 
                         tags: List[str], created_by: str, brd_content: str = None,
                         requirements: str = None) -> TestSuite:
        """Create a new test suite with complete metadata"""
        try:
            suite_id = str(uuid.uuid4())
            version = "1.0.0"
            current_time = datetime.now()
            
            test_suite = TestSuite(
                id=suite_id,
                name=name,
                description=description,
                created_by=created_by,
                created_at=current_time,
                scenarios=scenarios,
                tags=tags,
                version=version,
                brd_content=brd_content,
                requirements=requirements
            )
            
            with self.db.conn:
                self.db.conn.execute('''
                    INSERT INTO test_suites (
                        id, name, description, created_by, created_at, 
                        scenarios, tags, version, brd_content, requirements,
                        last_modified, last_modified_by
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    test_suite.id, test_suite.name, test_suite.description,
                    test_suite.created_by, test_suite.created_at,
                    json.dumps(test_suite.scenarios), json.dumps(test_suite.tags),
                    test_suite.version, test_suite.brd_content, test_suite.requirements,
                    current_time, created_by
                ))
            
            logger.info(f"Created test suite: {test_suite.name} (ID: {test_suite.id})")
            return test_suite
            
        except Exception as e:
            logger.error(f"Error creating test suite: {str(e)}")
            raise
    
    def get_test_suite(self, suite_id: str) -> Optional[TestSuite]:
        """Retrieve a test suite by ID"""
        try:
            cursor = self.db.conn.execute(
                'SELECT * FROM test_suites WHERE id = ?', (suite_id,))
            row = cursor.fetchone()
            
            if row:
                return TestSuite(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    created_by=row[3],
                    created_at=datetime.fromisoformat(row[4]),
                    scenarios=json.loads(row[5]),
                    tags=json.loads(row[6]),
                    version=row[7],
                    brd_content=row[8],
                    requirements=row[9]
                )
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving test suite: {str(e)}")
            raise
    
    def add_comment(self, suite_id: str, scenario_id: str, user: str, comment: str):
        """Add a comment to a specific scenario in a test suite"""
        try:
            comment_id = str(uuid.uuid4())
            current_time = datetime.now()
            
            with self.db.conn:
                self.db.conn.execute('''
                    INSERT INTO comments (id, suite_id, scenario_id, user, comment, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (comment_id, suite_id, scenario_id, user, comment, current_time))
            
            logger.info(f"Added comment to scenario {scenario_id} in suite {suite_id}")
            
        except Exception as e:
            logger.error(f"Error adding comment: {str(e)}")
            raise
    
    def get_comments(self, suite_id: str, scenario_id: str) -> List[Dict]:
        """Retrieve all comments for a specific scenario"""
        try:
            cursor = self.db.conn.execute('''
                SELECT id, user, comment, created_at 
                FROM comments 
                WHERE suite_id = ? AND scenario_id = ?
                ORDER BY created_at DESC
            ''', (suite_id, scenario_id))
            
            return [{
                'id': row[0],
                'user': row[1],
                'comment': row[2],
                'created_at': row[3]
            } for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error retrieving comments: {str(e)}")
            raise
    
    def generate_coverage_report(self, suite_id: str) -> Dict:
        """Generate a comprehensive coverage report for a test suite"""
        try:
            # Fetch test suite
            test_suite = self.get_test_suite(suite_id)
            if not test_suite:
                raise ValueError(f"Test suite not found: {suite_id}")
            
            scenarios = test_suite.scenarios
            
            # Initialize coverage statistics
            coverage_stats = {
                'suite_name': test_suite.name,
                'total_scenarios': len(scenarios),
                'priority_distribution': {},
                'complexity_distribution': {},
                'estimated_total_duration': 0,
                'requirements_coverage': {},
                'tags_distribution': {}
            }
            
            # Analyze scenarios
            for scenario in scenarios:
                # Priority distribution
                priority = scenario['priority']
                coverage_stats['priority_distribution'][priority] = \
                    coverage_stats['priority_distribution'].get(priority, 0) + 1
                
                # Complexity distribution
                complexity = scenario['complexity']
                coverage_stats['complexity_distribution'][complexity] = \
                    coverage_stats['complexity_distribution'].get(complexity, 0) + 1
                
                # Duration
                duration = int(scenario['estimated_duration'].split()[0])
                coverage_stats['estimated_total_duration'] += duration
                
                # Requirements coverage
                for req in scenario.get('requirements_covered', []):
                    if req not in coverage_stats['requirements_coverage']:
                        coverage_stats['requirements_coverage'][req] = {
                            'covered_by': [],
                            'scenario_count': 0
                        }
                    coverage_stats['requirements_coverage'][req]['covered_by'].append(
                        scenario['scenario_id'])
                    coverage_stats['requirements_coverage'][req]['scenario_count'] += 1
                
                # Tags distribution
                for tag in scenario.get('tags', []):
                    coverage_stats['tags_distribution'][tag] = \
                        coverage_stats['tags_distribution'].get(tag, 0) + 1
            
            logger.info(f"Generated coverage report for suite {suite_id}")
            return coverage_stats
            
        except Exception as e:
            logger.error(f"Error generating coverage report: {str(e)}")
            raise

def export_to_excel(df: pd.DataFrame) -> bytes:
    """Export DataFrame to Excel binary"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Test Scenarios')
    return output.getvalue()

def main():
    st.set_page_config(page_title="Enhanced Test Scenario Generator", layout="wide")
    
    # Initialize database and managers
    try:
        db_manager = DatabaseManager()
        test_manager = TestScenarioManager(db_manager)
        
        # Initialize Azure OpenAI client
        azure_config = AzureOpenAIConfig()
        client = azure_config.initialize_client()
        scenario_generator = TestScenarioGenerator(client)
        
    except Exception as e:
        st.error(f"Error initializing application: {str(e)}")
        st.stop()
    
    # Session state initialization
    if 'current_user' not in st.session_state:
        st.session_state.current_user = "default_user"
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", 
        ["Generator", "Test Suites", "Coverage Analysis", "Settings"])
    
    if page == "Generator":
        show_generator_page(scenario_generator, test_manager)
    elif page == "Test Suites":
        show_test_suites_page(test_manager)
    elif page == "Coverage Analysis":
        show_coverage_page(test_manager)
    else:
        show_settings_page(db_manager)

def show_generator_page(scenario_generator, test_manager):
    st.title("Test Scenario Generator")
    st.markdown("Generate comprehensive test scenarios from user stories")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # User Story Input
        st.subheader("User Story Input")
        user_story = st.text_area(
            "Enter User Story",
            height=150,
            placeholder="As a [role], I want to [action], so that [benefit]"
        )
        
        # Business Requirements Document
        st.subheader("Business Requirements Document (Optional)")
        brd_content = st.text_area(
            "Enter Business Requirements Document content",
            height=200,
            placeholder="Paste your Business Requirements Document content here...",
            help="Optional: Provide business requirements context to generate more aligned test scenarios"
        )
        
        # Additional Requirements
        st.subheader("Additional Requirements")
        requirements = st.text_area(
            "Enter any additional requirements or considerations",
            height=100,
            placeholder="Enter specific requirements, constraints, or considerations..."
        )
        
        # Configuration options
        test_type = st.selectbox(
            "Test Type",
            ["Functional", "Integration", "UI/UX", "Performance", "Security", "Accessibility"]
        )
        
        col_a, col_b = st.columns(2)
        with col_a:
            complexity = st.select_slider(
                "Test Complexity",
                options=["Low", "Medium", "High"]
            )
        
        with col_b:
            priority_filter = st.multiselect(
                "Priority Levels to Include",
                ["High", "Medium", "Low"],
                default=["High", "Medium", "Low"]
            )
        
        if st.button("Generate Test Scenarios", type="primary"):
            if user_story:
                with st.spinner("Generating test scenarios..."):
                    try:
                        scenarios = scenario_generator.generate_scenarios(
                            user_story=user_story,
                            test_type=test_type,
                            complexity=complexity,
                            requirements=requirements,
                            brd_content=brd_content if brd_content.strip() else None
                        )
                        
                        # Filter scenarios based on priority if needed
                        if priority_filter:
                            scenarios['scenarios'] = [
                                s for s in scenarios['scenarios'] 
                                if s['priority'] in priority_filter
                            ]
                        
                        # Store scenarios in session state
                        st.session_state.scenarios = scenarios
                        st.session_state.generation_metadata = {
                            'user_story': user_story,
                            'brd_content': brd_content,
                            'requirements': requirements,
                            'test_type': test_type,
                            'complexity': complexity,
                            'generated_at': datetime.now().isoformat()
                        }
                        
                        st.success("Test scenarios generated successfully!")
                        
                        # Display scenarios in expandable sections
                        for scenario in scenarios['scenarios']:
                            with st.expander(f"📝 {scenario['title']}"):
                                col_left, col_right = st.columns([3, 1])
                                with col_left:
                                    st.markdown(f"**ID:** {scenario['scenario_id']}")
                                with col_right:
                                    st.markdown(f"**Priority:** {scenario['priority']}")
                                    st.markdown(f"**Duration:** {scenario['estimated_duration']}")
                                
                                st.markdown("### Preconditions")
                                for pre in scenario['preconditions']:
                                    st.markdown(f"- {pre}")
                                
                                st.markdown("### Steps")
                                for idx, step in enumerate(scenario['steps'], 1):
                                    st.markdown(f"{idx}. {step}")
                                
                                st.markdown("### Expected Results")
                                for result in scenario['expected_results']:
                                    st.markdown(f"- {result}")
                                
                                st.markdown("### Test Data")
                                for data in scenario['test_data']:
                                    st.markdown(f"- {data}")
                                
                                if 'tags' in scenario:
                                    st.markdown("### Tags")
                                    st.markdown(", ".join(scenario['tags']))
                    
                    except Exception as e:
                        st.error(f"Error generating scenarios: {str(e)}")
                        st.error("Please try again or contact support if the error persists.")
            else:
                st.warning("Please enter a user story before generating scenarios.")
    
    with col2:
        if 'scenarios' in st.session_state:
            st.subheader("Save Test Suite")
            suite_name = st.text_input("Test Suite Name")
            suite_description = st.text_area("Description")
            suite_tags = st.text_input("Tags (comma-separated)")
            
            if st.button("Save as Test Suite"):
                try:
                    tags_list = [tag.strip() for tag in suite_tags.split(",") if tag.strip()]
                    
                    # Create test suite
                    test_suite = test_manager.create_test_suite(
                        name=suite_name,
                        description=suite_description,
                        scenarios=st.session_state.scenarios['scenarios'],
                        tags=tags_list,
                        created_by=st.session_state.current_user,
                        brd_content=st.session_state.generation_metadata['brd_content'],
                        requirements=st.session_state.generation_metadata['requirements']
                    )
                    
                    st.success(f"Test suite '{suite_name}' saved successfully!")
                    
                    # Show export options
                    st.subheader("Export Options")
                    export_format = st.radio(
                        "Select Format",
                        ["Excel", "JSON", "CSV"]
                    )
                    
                    if export_format:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        
                        if export_format == "Excel":
                            scenarios_df = pd.json_normalize(
                                st.session_state.scenarios['scenarios'],
                                sep='_'
                            )
                            excel_data = export_to_excel(scenarios_df)
                            st.download_button(
                                label="📥 Download Excel",
                                data=excel_data,
                                file_name=f"test_scenarios_{timestamp}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        
                        elif export_format == "JSON":
                            json_data = {
                                'metadata': st.session_state.generation_metadata,
                                'scenarios': st.session_state.scenarios
                            }
                            st.download_button(
                                label="📥 Download JSON",
                                data=json.dumps(json_data, indent=2),
                                file_name=f"test_scenarios_{timestamp}.json",
                                mime="application/json"
                            )
                        
                        else:  # CSV
                            scenarios_df = pd.json_normalize(
                                st.session_state.scenarios['scenarios'],
                                sep='_'
                            )
                            st.download_button(
                                label="📥 Download CSV",
                                data=scenarios_df.to_csv(index=False),
                                file_name=f"test_scenarios_{timestamp}.csv",
                                mime="text/csv"
                            )
                
                except Exception as e:
                    st.error(f"Error saving test suite: {str(e)}")
                    logger.error(f"Error saving test suite: {str(e)}")

def show_test_suites_page(test_manager):
    st.title("Test Suites")
    
    # Fetch all test suites
    try:
        cursor = test_manager.db.conn.execute('''
            SELECT id, name, description, created_by, created_at, tags, version 
            FROM test_suites 
            ORDER BY created_at DESC
        ''')
        suites = cursor.fetchall()
        
        if suites:
            # Search and filter options
            st.subheader("Search and Filter")
            search_term = st.text_input("Search by name or description")
            
            filtered_suites = suites
            if search_term:
                filtered_suites = [
                    s for s in suites 
                    if search_term.lower() in s[1].lower() or 
                    (s[2] and search_term.lower() in s[2].lower())
                ]
            
            # Display test suites
            for suite in filtered_suites:
                with st.expander(f"📁 {suite[1]} (Version: {suite[6]})"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"Description: {suite[2]}")
                        st.write(f"Created by: {suite[3]}")
                        st.write(f"Created at: {suite[4]}")
                        if suite[5]:  # Tags
                            st.write(f"Tags: {', '.join(json.loads(suite[5]))}")
                    
                    with col2:
                        if st.button("View Details", key=f"view_{suite[0]}"):
                            test_suite = test_manager.get_test_suite(suite[0])
                            st.session_state.current_suite = test_suite
                            st.rerun()
            
            # Show selected test suite details
            if 'current_suite' in st.session_state:
                st.subheader(f"Test Suite: {st.session_state.current_suite.name}")
                
                for scenario in st.session_state.current_suite.scenarios:
                    with st.expander(f"📝 {scenario['title']}"):
                        st.markdown(f"**ID:** {scenario['scenario_id']}")
                        st.markdown(f"**Priority:** {scenario['priority']}")
                        
                        tab1, tab2, tab3 = st.tabs(["Details", "Comments", "History"])
                        
                        with tab1:
                            st.markdown("### Preconditions")
                            for pre in scenario['preconditions']:
                                st.markdown(f"- {pre}")
                            
                            st.markdown("### Steps")
                            for idx, step in enumerate(scenario['steps'], 1):
                                st.markdown(f"{idx}. {step}")
                            
                            st.markdown("### Expected Results")
                            for result in scenario['expected_results']:
                                st.markdown(f"- {result}")
                        
                        with tab2:
                            # Comments section
                            comments = test_manager.get_comments(
                                st.session_state.current_suite.id,
                                scenario['scenario_id']
                            )
                            
                            # Display existing comments
                            for comment in comments:
                                st.text_area(
                                    f"Comment by {comment['user']} on {comment['created_at']}",
                                    value=comment['comment'],
                                    disabled=True,
                                    key=f"comment_{comment['id']}"
                                )
                            
                            # Add new comment
                            new_comment = st.text_area(
                                "Add a comment",
                                key=f"new_comment_{scenario['scenario_id']}"
                            )
                            if st.button("Add Comment", key=f"add_{scenario['scenario_id']}"):
                                test_manager.add_comment(
                                    st.session_state.current_suite.id,
                                    scenario['scenario_id'],
                                    st.session_state.current_user,
                                    new_comment
                                )
                                st.success("Comment added successfully!")
                                st.rerun()
                        
                        with tab3:
                            st.markdown("### Execution History")
                            # Implement execution history view
        else:
            st.info("No test suites found. Generate some test scenarios first!")
            
    except Exception as e:
        st.error(f"Error loading test suites: {str(e)}")
        logger.error(f"Error loading test suites: {str(e)}")

def show_coverage_page(test_manager):
    st.title("Coverage Analysis")
    
    try:
        # Fetch all test suites for selection
        cursor = test_manager.db.conn.execute('SELECT id, name FROM test_suites')
        suites = cursor.fetchall()
        
        if suites:
            selected_suite = st.selectbox(
                "Select Test Suite",
                options=suites,
                format_func=lambda x: x[1]
            )
            
            if selected_suite:
                coverage_stats = test_manager.generate_coverage_report(selected_suite[0])
                
                # Display coverage metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Scenarios", coverage_stats['total_scenarios'])
                
                with col2:
                    st.metric(
                        "Estimated Duration",
                        f"{coverage_stats['estimated_total_duration']} minutes"
                    )
                
                with col3:
                    requirements_count = len(coverage_stats['requirements_coverage'])
                    st.metric("Requirements Covered", requirements_count)
                
                # Priority distribution
                st.subheader("Priority Distribution")
                priority_df = pd.DataFrame.from_dict(
                    coverage_stats['priority_distribution'],
                    orient='index',
                    columns=['Count']
                )
                st.bar_chart(priority_df)
                
                # Complexity distribution
                st.subheader("Complexity Distribution")
                complexity_df = pd.DataFrame.from_dict(
                    coverage_stats['complexity_distribution'],
                    orient='index',
                    columns=['Count']
                )
                st.bar_chart(complexity_df)
                
                # Requirements coverage details
                st.subheader("Requirements Coverage")
                for req, details in coverage_stats['requirements_coverage'].items():
                    with st.expander(f"Requirement: {req}"):
                        st.write(f"Covered by {details['scenario_count']} scenarios:")
                        for scenario_id in details['covered_by']:
                            st.write(f"- {scenario_id}")
                
                # Export coverage report
                if st.button("Export Coverage Report"):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    report_json = json.dumps(coverage_stats, indent=2)
                    st.download_button(
                        label="📥 Download Coverage Report",
                        data=report_json,
                        file_name=f"coverage_report_{timestamp}.json",
                        mime="application/json"
                    )
        
        else:
            st.info("No test suites found. Generate some test scenarios first!")
            
    except Exception as e:
        st.error(f"Error analyzing coverage: {str(e)}")
        logger.error(f"Error analyzing coverage: {str(e)}")

def show_settings_page(db_manager):
    st.title("Settings")
    
    try:
        # User settings
        st.subheader("User Settings")
        username = st.text_input("Username", value=st.session_state.current_user)
        
        if st.button("Update Username"):
            # Update username in database
            with db_manager.conn:
                db_manager.conn.execute('''
                    INSERT OR REPLACE INTO user_settings (user_id, username, created_at)
                    VALUES (?, ?, ?)
                ''', (st.session_state.current_user, username, datetime.now()))
            
            st.session_state.current_user = username
            st.success("Username updated successfully!")
        
        # Export settings
        st.subheader("Export Settings")
        col1, col2 = st.columns(2)
        
        with col1:
            include_comments = st.checkbox(
                "Include comments in exports",
                help="Include scenario comments when exporting test suites"
            )
            include_history = st.checkbox(
                "Include execution history",
                help="Include test execution history in exports"
            )
        
        with col2:
            include_metrics = st.checkbox(
                "Include coverage metrics",
                help="Include coverage analysis in exports"
            )
            include_metadata = st.checkbox(
                "Include metadata",
                help="Include generation metadata in exports"
            )
        
        # Save export preferences
        if st.button("Save Export Preferences"):
            export_preferences = {
                "include_comments": include_comments,
                "include_history": include_history,
                "include_metrics": include_metrics,
                "include_metadata": include_metadata
            }
            
            with db_manager.conn:
                db_manager.conn.execute('''
                    UPDATE user_settings 
                    SET preferences = ?
                    WHERE user_id = ?
                ''', (json.dumps(export_preferences), st.session_state.current_user))
            
            st.success("Export preferences saved!")
        
        # Display settings
        st.subheader("Display Settings")
        col3, col4 = st.columns(2)
        
        with col3:
            default_page = st.selectbox(
                "Default Landing Page",
                ["Generator", "Test Suites", "Coverage Analysis"]
            )
            items_per_page = st.number_input(
                "Items per page",
                min_value=5,
                max_value=50,
                value=10
            )
        
        with col4:
            default_export = st.selectbox(
                "Default Export Format",
                ["Excel", "JSON", "CSV"]
            )
            auto_refresh = st.checkbox(
                "Auto-refresh dashboards",
                help="Automatically refresh coverage and analytics dashboards"
            )
        
        # Save display preferences
        if st.button("Save Display Preferences"):
            display_preferences = {
                "default_page": default_page,
                "items_per_page": items_per_page,
                "default_export": default_export,
                "auto_refresh": auto_refresh
            }
            
            with db_manager.conn:
                db_manager.conn.execute('''
                    UPDATE user_settings 
                    SET preferences = json_set(
                        COALESCE(preferences, '{}'),
                        '$.display',
                        ?
                    )
                    WHERE user_id = ?
                ''', (json.dumps(display_preferences), st.session_state.current_user))
            
            st.success("Display preferences saved!")
        
        # Database maintenance
        st.subheader("Database Maintenance")
        st.warning("Warning: These actions cannot be undone!")
        
        col5, col6 = st.columns(2)
        
        with col5:
            if st.button("Cleanup Old Comments"):
                # Delete comments older than 90 days
                cleanup_date = datetime.now() - pd.Timedelta(days=90)
                with db_manager.conn:
                    db_manager.conn.execute('''
                        DELETE FROM comments 
                        WHERE created_at < ?
                    ''', (cleanup_date,))
                st.success("Old comments cleaned up successfully!")
        
        with col6:
            if st.button("Optimize Database"):
                with db_manager.conn:
                    db_manager.conn.execute("VACUUM")
                st.success("Database optimized successfully!")
        
        # Integration settings
        st.subheader("Integration Settings")
        
        # JIRA integration
        st.markdown("### JIRA Integration")
        jira_url = st.text_input(
            "JIRA URL",
            placeholder="https://your-domain.atlassian.net"
        )
        jira_api_key = st.text_input(
            "JIRA API Key",
            type="password"
        )
        
        # TestRail integration
        st.markdown("### TestRail Integration")
        testrail_url = st.text_input(
            "TestRail URL",
            placeholder="https://your-domain.testrail.com"
        )
        testrail_api_key = st.text_input(
            "TestRail API Key",
            type="password"
        )
        
        if st.button("Save Integration Settings"):
            integration_settings = {
                "jira": {
                    "url": jira_url,
                    "api_key": jira_api_key
                },
                "testrail": {
                    "url": testrail_url,
                    "api_key": testrail_api_key
                }
            }
            
            # Encrypt sensitive data before storing
            # Note: In a production environment, implement proper encryption
            with db_manager.conn:
                db_manager.conn.execute('''
                    UPDATE user_settings 
                    SET preferences = json_set(
                        COALESCE(preferences, '{}'),
                        '$.integrations',
                        ?
                    )
                    WHERE user_id = ?
                ''', (json.dumps(integration_settings), st.session_state.current_user))
            
            st.success("Integration settings saved!")
        
        # About section
        st.subheader("About")
        st.markdown("""
        ### Test Scenario Generator
        Version: 1.0.0
        
        A comprehensive tool for generating and managing test scenarios using Azure OpenAI.
        
        - Generate test scenarios from user stories
        - Manage test suites and scenarios
        - Track coverage and analytics
        - Export in multiple formats
        - Integration with popular testing tools
        
        For support or feature requests, please contact support@example.com
        """)
        
    except Exception as e:
        st.error(f"Error managing settings: {str(e)}")
        logger.error(f"Error in settings page: {str(e)}")

if __name__ == "__main__":
    main()