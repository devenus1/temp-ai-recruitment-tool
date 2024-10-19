import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import json
import os
from typing import Dict, List, Union
import time

# Load environment variables and OpenAI client
load_dotenv()
client = OpenAI()

st.markdown("""
    <style>
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
    .score-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        background-color: #f0f2f6;
    }
    .score-header {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .justification-text {
        font-style: italic;
        color: #666;
    }
    </style>
""", unsafe_allow_html=True)


# Define the competency
competency_definition = {
    "Risk and Adaptability": {
        "definition": "Measures how candidates handle risk and adapt to challenges. Reflects willingness to step out of their comfort zone and respond to uncertain situations.",
        "scoring_rubric": {
            1: "Avoids risks; struggles with adaptability.",
            3: "Takes calculated risks; moderately adaptable.",
            5: "Embraces significant risks; highly adaptable to change."
        }
    },
    "Work Style and Approach": {
        "definition": "Assesses whether candidates are strategic or tactical, and their focus on quality versus efficiency.",
        "scoring_rubric": {
            1: "Highly tactical; focuses on immediate action and efficiency.",
            3: "Balances strategic planning with action; considers both quality and efficiency.",
            5: "Highly strategic; prioritizes planning and quality over immediate efficiency."
        }
    },
    "Motivation and Passion": {
        "definition": "Evaluates what drives the candidate—financial gain, influence, or intrinsic passion.",
        "scoring_rubric": {
            1: "Primarily motivated by financial gain.",
            3: "Equally motivated by financial gain and influence/passion.",
            5: "Driven by intrinsic passion and the desire to influence positively."
        }
    },
    "Interpersonal Skills and Stress Management": {
        "definition": "Looks at conflict resolution, stress handling, and preference for collaboration or solitude.",
        "scoring_rubric": {
            1: "Struggles with conflict resolution; prefers solitude under stress.",
            3: "Moderate interpersonal skills; sometimes seeks support.",
            5: "Excellent at handling conflicts; collaborates and seeks support when needed."
        }
    },
    "Self-awareness and Learning Orientation": {
        "definition": "Gauges the candidate's self-understanding and commitment to professional growth.",
        "scoring_rubric": {
            1: "Limited self-awareness; does not actively pursue growth.",
            3: "Moderate self-awareness; occasionally engages in professional development.",
            5: "Highly self-aware; continuously seeks learning and growth opportunities."
        }
    }
}

# Define the list of questions
questions = [
    "What is the most significant professional risk you have taken, and what was the outcome?",
    "How do you typically handle frustrations or conflicts in the workplace?",
    "Do you tend to focus more on strategic planning or immediate action in your work, and why?",
    "What is the most recent skill or professional development you have pursued, and how has it impacted your work?",
    "On a scale of 1 to 10, how would you rate your professional self-worth, and what factors contribute to that rating?",
    "If you could collaborate with any historical business leader, who would it be and why?",
    "What situations or behaviors trigger impatience for you at work?",
    "What aspects of your professional life energize and motivate you the most?",
    "In your career, do you prioritize financial gain or the ability to influence others, and why?",
    "Can you describe a time when you felt professionally challenged or threatened, and how you responded?",
    "What are your typical work hours, and how do you maintain a balance between work and personal life?",
    "Is the reputation of your employer more important to you than your specific role, or vice versa? Please explain.",
    "Which professional field or project are you most passionate about, and what draws you to it?",
    "Have you ever doubted a professional decision you made? If so, how did you address that doubt?",
    "When experiencing stress at work, do you prefer to seek support from others or handle it on your own?",
    "What are three key professional lessons you have learned throughout your career?",
    "In your work, do you prioritize efficiency or quality, and how do you balance the two?",
    "If asked, what might your toughest competitor say about your professional approach?",
    "If you could change one aspect of your professional behavior without any judgment, what would it be and why?",
    "What do you consider to be your core professional strength, and how has it contributed to your success?"
]


def initialize_session_state():
    """Initialize all session state variables"""
    if 'question_index' not in st.session_state:
        st.session_state.question_index = 0
    if 'responses' not in st.session_state:
        st.session_state.responses = []
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'evaluation_result' not in st.session_state:
        st.session_state.evaluation_result = None
    if 'show_justifications' not in st.session_state:
        st.session_state.show_justifications = {}


def display_progress_bar():
    """Display progress bar for questions completed"""
    progress = st.session_state.question_index / len(questions)
    st.progress(progress)
    st.write(f"Progress: {st.session_state.question_index}/{len(questions)} questions completed")

def validate_response(response: str) -> bool:
    """Validate if the response is adequate"""
    if not response or len(response.strip()) < 10:
        st.error("Please provide a more detailed response (at least 10 characters).")
        return False
    return True

# def submit_response():
#     """Handle response submission with validation"""
#     current_response = st.session_state['current_response'].strip()
#     if validate_response(current_response):
#         st.session_state.responses.append(current_response)
#         st.session_state.current_response = ""
#         st.session_state.question_index += 1
#         st.rerun()

def submit_response():
    """Handle response submission with validation"""
    current_response = st.session_state['current_response'].strip()
    if validate_response(current_response):
        st.session_state.responses.append(current_response)
        st.session_state.current_response = ""  # Clear the input for the next question
        st.session_state.question_index += 1  # Move to the next question


def analyze_results():
    """Trigger the analysis of all responses"""
    with st.spinner("Analyzing responses..."):
        try:
            evaluation = evaluate_full_responses(st.session_state.responses)
            st.session_state.evaluation_result = json.loads(evaluation)
            st.session_state.analysis_complete = True
            st.rerun()
        except Exception as e:
            st.error(f"An error occurred during analysis: {str(e)}")



def generate_full_prompt(responses):
    prompt = """
    You are an expert evaluator using the Professional Compass Framework to assess a candidate's responses. Return a JSON response with the following structure:

    {
        "competencies": [
        {
            "competency": "Risk and Adaptability",
            "score": <int Score>,
            "justification": "<Explanation of why this score was given>"
        },
        {
            "competency": "Work Style and Approach",
            "score": <int Score>,
            "justification": "<Explanation of why this score was given>"
        },
        {
            "competency": "Motivation and Passion",
            "score": <int Score>,
            "justification": "<Explanation of why this score was given>"
        },
        {
            "competency": "Interpersonal Skills and Stress Management",
            "score": <int Score>,
            "justification": "<Explanation of why this score was given>"
        },
        {
            "competency": "Self-awareness and Learning Orientation",
            "score": <int Score>,
            "justification": "<Explanation of why this score was given>"
        }
        ]
    }

    Evaluate the following candidate's responses based on these competencies and provide the corresponding score and justification for each. The scoring should be done according to Scoring Rubric sctrictly:
    """

    competency_mapping = {
        "Risk and Adaptability": [0, 6, 9],
        "Work Style and Approach": [2, 16, 17],
        "Motivation and Passion": [5, 7, 8, 12],
        "Interpersonal Skills and Stress Management": [1, 13, 14, 18],
        "Self-awareness and Learning Orientation": [3, 4, 11, 15, 19]
    }

    for competency, question_indices in competency_mapping.items():
        prompt += f"\nCompetency: {competency}\nDefinition: {competency_definition[competency]['definition']}\n"
        prompt += f"Scoring Rubric:\n1: {competency_definition[competency]['scoring_rubric'][1]}\n"
        prompt += f"3: {competency_definition[competency]['scoring_rubric'][3]}\n"
        prompt += f"5: {competency_definition[competency]['scoring_rubric'][5]}\n"

        for idx in question_indices:
            question = questions[idx]
            response = responses[idx]
            prompt += f"\nQuestion: {question}\nResponse: {response}\n"
    return prompt

    # Call OpenAI API to evaluate
def evaluate_full_responses(responses):
    prompt = generate_full_prompt(responses)
    try:
        api_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional evaluator."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
            response_format={"type": "json_object"},
            temperature=0
    )
    
        evaluation = api_response.choices[0].message.content
    except Exception as e:
        return f"Error during evaluation: {str(e)}"
    
    return evaluation



def display_results():
    """Display the evaluation results with scores and optional justifications"""
    if not st.session_state.evaluation_result:
        return

    total_score = 0
    results = st.session_state.evaluation_result['competencies']

    # Display individual competency scores
    st.subheader("Competency Scores")
    
    for comp in results:
        comp_name = comp['competency']
        score = comp['score']
        total_score += score
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{comp_name}**")
        with col2:
            st.write(f"Score: {score}/5")
        with col3:
            if comp_name not in st.session_state.show_justifications:
                st.session_state.show_justifications[comp_name] = False
            if st.button(f"{'Hide' if st.session_state.show_justifications[comp_name] else 'Show'} Details", 
                        key=f"btn_{comp_name}"):
                st.session_state.show_justifications[comp_name] = not st.session_state.show_justifications[comp_name]
        
        if st.session_state.show_justifications[comp_name]:
            st.info(comp['justification'])
        st.markdown("---")

    # Display total score
    st.subheader("Overall Assessment")
    total_possible = len(results) * 5
    percentage = (total_score / total_possible) * 100
    st.write(f"Total Score: {total_score}/{total_possible} ({percentage:.1f}%)")
    
    # Provide overall assessment based on percentage
    if percentage >= 80:
        st.success("Outstanding Performance! Shows exceptional professional competencies.")
    elif percentage >= 60:
        st.info("Good Performance. Shows solid professional competencies with room for growth.")
    else:
        st.warning("Development Needed. Key areas require significant improvement.")

def main():
    """Main application flow"""
    st.title("Professional Compass Demo")
    st.markdown("### Comprehensive Professional Assessment Tool")
    
    initialize_session_state()
    
    if st.session_state.question_index < len(questions):
        display_progress_bar()
        
        st.write(f"### Question {st.session_state.question_index + 1}:")
        st.write(questions[st.session_state.question_index])
        st.text_area("Your Answer", key="current_response", height=150)
        st.button("Submit Answer", on_click=submit_response)
        
    elif not st.session_state.analysis_complete:
        st.success("You have completed all the questions!")
        if st.button("Analyze Results"):
            analyze_results()
    
    else:
        display_results()
        if st.button("Start Over"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()