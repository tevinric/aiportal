import streamlit as st
import os
import openai
import pandas as pd
import json
from datetime import datetime
import io

from config import  api_key, endpoint

# Azure OpenAI Configuration
class AzureOpenAIConfig:
    def __init__(self):
        self.api_base = endpoint
        self.api_key = api_key
        self.api_version = "2024-02-15-preview"
        
    def initialize_client(self):
        client = openai.AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.api_base
        )
        return client


class TestScenarioGenerator:
    def __init__(self, client):
        self.client = client
        
    def generate_scenarios(self, user_story, test_type, complexity, requirements):
        system_prompt = """You are a test scenario generator that creates detailed test scenarios in JSON format.
        Always ensure your response is valid JSON and follows the exact structure provided.
        Do not include any explanatory text outside the JSON structure."""
        
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
            "estimated_duration": "in minutes"
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
                response_format={ "type": "json_object" }  # Ensure JSON response
            )
            
            response_content = response.choices[0].message.content
            
            # Validate JSON before returning
            try:
                scenarios = json.loads(response_content)
                if not isinstance(scenarios, dict) or "scenarios" not in scenarios:
                    raise ValueError("Invalid JSON structure: missing 'scenarios' key")
                return scenarios
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON response from API: {str(e)}")
                st.code(response_content)  # Display the problematic response
                raise ValueError(f"Invalid JSON response: {str(e)}")
                
        except Exception as e:
            st.error(f"Error calling Azure OpenAI API: {str(e)}")
            raise

def export_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Test Scenarios')
    return output.getvalue()


def test_case_generator():
    
    st.title("AI Test Scenario Generator")
    st.markdown("Use the power of AI to generate comprehensive test cases.")
    
    # Initialize Azure OpenAI client
    try:
        azure_config = AzureOpenAIConfig()
        client = azure_config.initialize_client()
        scenario_generator = TestScenarioGenerator(client)
    except Exception as e:
        st.error(f"Error initializing Azure OpenAI client: {str(e)}")
        st.stop()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        test_type = st.selectbox(
            "Test Type",
            ["Functional", "Integration", "UI/UX", "Performance", "Security", "Accessibility"]
        )
        
        complexity = st.select_slider(
            "Test Complexity",
            options=["Low", "Medium", "High"]
        )
        
        st.markdown("### Additional Features")
        export_format = st.radio(
            "Export Format",
            ["Excel", "JSON", "CSV"]
        )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("User Story Input")
        user_story = st.text_area(
            "Enter User Story",
            height=150,
            placeholder="As a [role], I want to [action], so that [benefit]"
        )
        
        st.subheader("Additional Requirements")
        requirements = st.text_area(
            "Enter any additional requirements or considerations",
            height=100,
            placeholder="Enter specific requirements, constraints, or considerations..."
        )
        
        if st.button("Generate Test Scenarios", type="primary"):
            if user_story:
                with st.spinner("Generating test scenarios..."):
                    try:
                        scenarios = scenario_generator.generate_scenarios(
                            user_story, test_type, complexity, requirements
                        )
                        
                        # Store scenarios in session state
                        st.session_state.scenarios = scenarios
                        
                        # Display scenarios
                        st.success("Test scenarios generated successfully!")
                        
                        # Create expandable sections for each scenario
                        for scenario in scenarios['scenarios']:
                            with st.expander(f"📝 {scenario['title']}"):
                                st.markdown(f"**ID:** {scenario['scenario_id']}")
                                st.markdown(f"**Priority:** {scenario['priority']}")
                                st.markdown(f"**Estimated Duration:** {scenario['estimated_duration']}")
                                
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
                    
                    except Exception as e:
                        st.error(f"Error generating scenarios: {str(e)}")
                        st.error("Please try again or contact support if the error persists.")
            else:
                st.warning("Please enter a user story before generating scenarios.")
    
    with col2:
        if 'scenarios' in st.session_state:
            st.subheader("Export Options")
            
            # Generate timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            try:
                # Create DataFrame for exports
                scenarios_df = pd.json_normalize(
                    st.session_state.scenarios['scenarios'],
                    sep='_'
                )
                
                if export_format == "Excel":
                    excel_data = export_to_excel(scenarios_df)
                    st.download_button(
                        label="📥 Download Excel",
                        data=excel_data,
                        file_name=f"test_scenarios_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                elif export_format == "JSON":
                    json_str = json.dumps(st.session_state.scenarios, indent=2)
                    st.download_button(
                        label="📥 Download JSON",
                        data=json_str,
                        file_name=f"test_scenarios_{timestamp}.json",
                        mime="application/json"
                    )
                    
                else:  # CSV
                    csv = scenarios_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"test_scenarios_{timestamp}.csv",
                        mime="text/csv"
                    )
                
                # Display statistics
                st.subheader("Statistics")
                scenarios = st.session_state.scenarios['scenarios']
                st.metric("Total Scenarios", len(scenarios))
                
                priorities = pd.DataFrame(scenarios)['priority'].value_counts()
                st.markdown("### Priority Distribution")
                st.bar_chart(priorities)
                
            except Exception as e:
                st.error(f"Error preparing export: {str(e)}")
