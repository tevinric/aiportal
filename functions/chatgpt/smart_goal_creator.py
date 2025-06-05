import streamlit as st
from openai import AzureOpenAI
import os

from config import api_key, endpoint    

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=api_key,
    api_version="2024-02-15-preview",
    azure_endpoint=endpoint 
)

# Define pillar contexts
PILLAR_CONTEXTS = {
    "business improvement": """
    Key considerations:
    - Processes, frameworks, systems to improve the status quo
    - Must directly impact Growth, Customer, People pillars (Strengthen the core)
    - Strategies, processes, frameworks, systems to improve the future
    - Must driectly impact Growth, Customer, People pillars
    - Risk management and compliance
    """,
    
    "people": """
    Key considerations:
    - Key people metrics: Find, grow, keep, engage
    - Personal development and behaviourial feedback
    - Teamwork
    """,
    
    "customer": """
    Key considerations:
    - External Customer feedback.Lead and lag indicators of customer loyalty
    - Internal customer
    """,
    
    "growth": """
    Key considerations:
    - Finacial results, growth targets, costs.
    - Lead and Lag indictors of sustainable finacial growth, market share, brand equit
    """
}

# Initialize session state
if 'department' not in st.session_state:
    st.session_state.department = ""
if 'additional_context' not in st.session_state:
    st.session_state.additional_context = ""
if 'employee_role' not in st.session_state:
    st.session_state.employee_role = ""

def convert_to_smart_goal(client, simple_goal: str, timeframe: str, pillar: str, department: str, employee_role: str = "", additional_context: str = "") -> str:
    """
    Convert a simple goal to a SMART goal using Azure OpenAI GPT-4
    Returns a paragraph of text representing the SMART goal
    """
    # Get pillar-specific context
    pillar_context = PILLAR_CONTEXTS[pillar.lower()]
    
    # Add department and role context to the system prompt
    department_context = f"\nDepartment Context: This goal is specifically for the {department} department. Consider the department's functions, responsibilities, and scope when crafting the SMART goal." if department else ""
    role_context = f"\nRole Context: This goal is specifically for an employee in the role of {employee_role}. Consider the role's responsibilities, scope, and level of influence when crafting the SMART goal." if employee_role else ""
    
    user_additional_context = f"\nAdditional Context: {additional_context}" if additional_context else ""
    
    system_prompt = f"""
    You are a SMART goal expert specializing in {pillar} objectives. Convert simple goals into SMART goals by creating a clear, 
    actionable paragraph that incorporates all SMART criteria:
    - Specific: Are the objectives specific?
    - Measurable: Can you measure the objectives? If you cant measure it in some way, you wont know whether the objective has been achieved
    - Attainable: Are the objectives attainable or within one's influence?
    - Relevant: Are the objectives realistic and relevant? Do they Contribute to the strategic goals?
    - Time-bound: Is there a time period within which the performance outputs need to be achieved?
    
    Consider this pillar-specific context when crafting the goal:
    {pillar_context}
    {department_context}
    {role_context}
    {user_additional_context}
    
    Respond with a single paragraph that naturally incorporates all these elements without explicitly labeling them. 
    Provide each goal as a mission statement for an employee to achieve. Do not use first person pronouns.
    Adapt the goal to work with any provided timeframe format, whether it's a specific date, duration, or recurring period.
    Do not include percentages or targets if it is not explicitely provided in the simple goal.
    
    If a specific role is provided, ensure the goal:
    - Aligns with typical responsibilities for that role
    - Is achievable within the scope of authority for that position
    - Uses metrics and activities relevant to that role level
    - Considers the role's impact on team and organizational objectives
    
    You must also provide lagging indicators for the goal according to the following guidelines:
    
    - Time to step up (Not making desired progress)
    - Making progress (Making progress and moving in the right direction)
    - Right on track (Making desired progress)
    - Setting the example (Exceeding desired progress)
    """
    
    user_prompt = f"""
    Business Pillar: {pillar}
    Department: {department}
    Employee Role: {employee_role if employee_role else "Not specified"}
    Simple Goal: {simple_goal}
    Timeframe: {timeframe}
    Additional Context: {additional_context if additional_context else "None provided"}
    
    Please convert this into a SMART goal paragraph that aligns with the {pillar} pillar objectives, {department} department focus{f", and {employee_role} role responsibilities" if employee_role else ""}.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt4omini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error in API call: {str(e)}")
        return None

def smart_goal_creator(client):
    # Custom CSS
    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .stTextInput, .stTextArea {
            margin-bottom: 1rem;
        }
        .smart-goal-box {
            padding: 20px;
            border-radius: 10px;
            background-color: #f0f2f6;
            margin: 10px 0;
        }
        .timeframe-examples {
            font-size: 0.9em;
            color: #666;
            padding: 10px;
            border-left: 3px solid #ccc;
            margin: 10px 0;
        }
        .pillar-info {
            font-size: 0.9em;
            color: #666;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 5px;
            margin: 10px 0;
        }
        .context-info {
            font-style: italic;
            color: #666;
            font-size: 0.8em;
            margin-top: 4px;
        }
        .stAlert {
            margin-top: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    
    # Display the Chat Header
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1: 
        st.write(" ")
    with col2:
        st.write(" ")
    with col3:
        st.image("Telesure-logo.png", width=200)
    with col4:
        st.write(" ")
    with col5:
        st.write(" ")
    
    
    # App header
    st.markdown("<h1 style='text-align: center;'>TIH SMART Goal Creator</h1>", unsafe_allow_html=True)
    st.markdown("""
        Transform your goals into SMART objectives:
        **S**pecific • **M**easurable • **A**chievable • **R**elevant • **T**ime-bound
    """)
    
    # Create a form for input collection
    with st.form(key="goal_form"):
        # Business Pillar selection
        pillar = st.selectbox(
            "Select Business Pillar",
            options=["Business Improvement", "People", "Customer", "Growth"],
            help="Choose the business pillar that best aligns with your goal"
        )
        
        # Department input
        department = st.text_input(
            "Department",
            value=st.session_state.department,
            help="Enter your department name",
            placeholder="Example: Marketing, IT, Finance, HR..."
        )
        
        # Employee Role input (optional)
        employee_role = st.text_input(
            "Employee Role (Optional)",
            value=st.session_state.employee_role,
            help="Enter the role of the employee this goal is for",
            placeholder="Example: Senior Developer, Marketing Manager, Sales Representative..."
        )
        
        # Simple goal input
        simple_goal = st.text_input(
            "What is your goal?",
            key="goal_input",
            help="Enter a brief description of your goal",
            placeholder=f"Example: {'Reduce operational costs' if pillar == 'Business Improvement' else 'Improve employee retention' if pillar == 'People' else 'Enhance customer satisfaction' if pillar == 'Customer' else 'Increase market share'}"
        )
        
        
        timeframe = st.text_input(
            "When do you want to achieve this goal?",
            help="Enter any timeframe format - specific date, duration, or recurring period",
            placeholder="Example: within 3 months, by end of 2024, monthly..."
        )
        
        # Additional Context input
        additional_context = st.text_area(
            "Additional Context (Optional)",
            value=st.session_state.additional_context,
            help="Provide any additional context or specific requirements for your goal",
            placeholder="Example: This goal is part of our digital transformation initiative...",
            height=100
        )
        
        # Submit button
        submit_button = st.form_submit_button(
            label="Generate SMART Goal",
            type="primary",
            use_container_width=True
        )
    
    # Process form submission
    if submit_button:
        # Validate required fields
        if not simple_goal:
            st.error("Please enter your goal!")
        elif not timeframe:
            st.error("Please specify a timeframe!")
        elif not department:
            st.error("Please specify your department!")
        else:
            # Update session state
            st.session_state.department = department
            st.session_state.additional_context = additional_context
            st.session_state.employee_role = employee_role
            
            with st.spinner("Creating your SMART goal..."):
                smart_goal = convert_to_smart_goal(
                    client,
                    simple_goal,
                    timeframe,
                    pillar,
                    department,
                    employee_role,
                    additional_context
                )
                
                if smart_goal:
                    # Success message
                    st.success("Your SMART goal has been generated!")
                    
                    # Display the SMART goal in a nice container
                    st.markdown("### Your SMART Goal:")
                    st.markdown(smart_goal)