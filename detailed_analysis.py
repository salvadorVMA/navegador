"""
Detailed Analysis Module for Navegador Project

This module contains the multi-step analysis logic extracted from nav_py13_reporte1.ipynb
for generating detailed reports. It implements the complete analysis pipeline including:
1. Pattern identification (similar/different patterns)
2. Expert summaries generation
3. Transversal analysis and final report

The main entry point is `run_detailed_analysis()` which provides the interface for
the agent workflow.
"""

import os
import re
import json
import tqdm
from typing import Dict, List, Tuple, Any, Optional
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser
from openai import OpenAI

# Import utility functions
from utility_functions import batch_documents, get_answer, clean_llm_json_output, environment_setup
from plotting_utils import get_variable_description, save_plots_for_analysis, create_summary_plots_grid
from plotting_utils import get_variable_description, save_plots_for_analysis, create_summary_plots_grid

# Pydantic Models for structured output

class PatternItem(BaseModel):
    TITLE_SUMMARY: str
    VARIABLE_STRING: str
    DESCRIPTION: str

class FlatPatternSummary(BaseModel):
    """
    A "catch-all" model so we can declare SIMILAR_PATTERN_1…n
    and DIFFERENT_PATTERN_1…n at the top level.
    """
    class Config:
        extra = "allow"

class ExpertSummaryResponse(BaseModel):
    EXPERT_REPLY: str

class TransversalAnalysisResponse(BaseModel):
    TOPIC_SUMMARIES: dict[str, str]  # A dictionary with topic names as keys and summaries as values
    TOPIC_SUMMARY: str  # A one-paragraph summary for a general audience
    QUERY_ANSWER: str  # A two-sentence answer to the query

# Pattern parsing utilities

def flat_pattern_template(n: int) -> FlatPatternSummary:
    """
    Build an "empty" flat summary with n SIMILAR_PATTERN_i
    and n DIFFERENT_PATTERN_i placeholders.
    """
    empty = {"TITLE_SUMMARY": "", "VARIABLE_STRING": "", "DESCRIPTION": ""}
    payload: dict[str, dict[str, str]] = {}
    for kind in ("SIMILAR_PATTERN", "DIFFERENT_PATTERN"):
        for i in range(1, n + 1):
            payload[f"{kind}_{i}"] = empty.copy()
    return FlatPatternSummary(**payload)

# Initialize parsers
pattern_parser_simdif = PydanticOutputParser(pydantic_object=FlatPatternSummary)
pattern_simdif_format_instructions = pattern_parser_simdif.get_format_instructions()

expert_summary_parser = PydanticOutputParser(pydantic_object=ExpertSummaryResponse)
expert_summary_format_instructions = expert_summary_parser.get_format_instructions()

transversal_parser = PydanticOutputParser(pydantic_object=TransversalAnalysisResponse)
transversal_format_instructions = transversal_parser.get_format_instructions()

# Core analysis functions

def create_prompt_crosssum(user_query: str, tmp_res_st: str, n_topics: int = 5, format_instructions: str = "") -> str:
    """
    Optimized prompt for extracting non-empty, detailed patterns from survey results.
    """
    prompt = f"""
You are a research assistant analyzing survey results to answer the QUERY below.

Your job is to:
- Identify the top {n_topics} SIMILAR PATTERNS (trends or agreements) and {n_topics} DIFFERENT PATTERNS (contrasts or contradictions) relevant to the QUERY.
- For each pattern, provide:
    1. TITLE_SUMMARY: A short, descriptive title (never empty).
    2. VARIABLE_STRING: Comma-separated QUESTION_IDs used in the pattern (never empty).
    3. DESCRIPTION: A detailed explanation, citing numbers and QUESTION_IDs in parentheses (never empty).

Instructions:
- Do NOT leave any field empty. If information is limited, generalize or summarize what is available.
- Use only facts you are sure about, and always cite the QUESTION_ID for each fact.
- Do NOT repeat the same pattern in multiple fields.
- Ignore any results marked as 'NaN' or not available.
- If you combine categories (e.g., "like a lot" + "like somewhat"), only mention the sum if all original values are present.
- Do NOT invent data; if a pattern is weak, explain that.
- Each pattern must be unique and relevant to the QUERY.

Example input format:
* QUESTION_ID: p1_1|ABC
  QUESTION: 'Do you like ice cream?'
  SUMMARY: 85% of people like ice cream, 10% do not, 5% do not know.
* QUESTION_ID: p2_1|ABC
  QUESTION: 'Do you like marshmallow treats?'
  SUMMARY: 80% like, 15% do not, 5% do not know.
* QUESTION_ID: p10_1|DEF:
  QUESTION: 'Do you like sour apple candies?'
  SUMMARY: 40% of people like sour apple candies, while 50% said they do not like it, and 10% said they do not know.

In these cases, the SIMILAR PATTERN is that 'people really like sweet treats because 85% like ice cream and 80% like marshmallow treats', 
and the DIFFERENT PATTERN is that 'people do not like sour treats as much because only 40% said they liked them'.

Example output for a SIMILAR PATTERN:
TITLE_SUMMARY: High preference for sweet treats
VARIABLE_STRING: p1_1|ABC,p2_1|ABC
DESCRIPTION: A large majority like ice cream (85%, p1_1|ABC) and marshmallow treats (80%, p2_1|ABC).

Note that the QUESTION_IDS of the format 'question_id|table_id' (e.g., pxx|YYY where xx is any combination of numbers and '_', and YYY are any three capital letters). 
There are examples of valid QUESTION_IDS: 'p2|ABC', 'p1_1|ABC', 'p20_2|EFG', 'p23_12|EFG'. Be careful to include all the elements of the QUESTION_ID.

Example output (strict JSON, no markdown, no code block, no extra text):
{{
  "SIMILAR_PATTERN_1": {{"TITLE_SUMMARY": "...", "VARIABLE_STRING": "...", "DESCRIPTION": "..."}},
  "SIMILAR_PATTERN_2": {{"TITLE_SUMMARY": "...", "VARIABLE_STRING": "...", "DESCRIPTION": "..."}},
  ...
  "DIFFERENT_PATTERN_5": {{"TITLE_SUMMARY": "...", "VARIABLE_STRING": "...", "DESCRIPTION": "..."}}
}}

QUERY: {user_query}
RESULTS: {tmp_res_st}

{format_instructions}

Checklist before submitting:
- [ ] All fields are filled for each pattern.
- [ ] Each DESCRIPTION includes at least one number and QUESTION_ID.
- [ ] No field is left empty.
"""
    return prompt

def get_structured_summary(user_query: str, tmp_res_st: str, tmp_grade_dict: dict, 
                          model_name: str = 'gpt-4o-mini-2024-07-18', temperature: float = 0.9) -> Tuple[str, dict]:
    """
    This function combines the prompt creation and LLM call,
    then parses the response using the PydanticOutputParser.
    """
    # Calculate number of patterns: three results minimum for each pattern to minimize hallucinations
    n_topics = min(len(tmp_grade_dict) // 4, 5)

    prompt = create_prompt_crosssum(
        user_query=user_query, 
        tmp_res_st=tmp_res_st, 
        n_topics=n_topics, 
        format_instructions=pattern_simdif_format_instructions
    )
    
    content = get_answer(prompt, model=model_name, temperature=temperature)
    content = clean_llm_json_output(content)
    
    try:
        parsed = pattern_parser_simdif.parse(content)
        return content, parsed.model_dump()
    except Exception as e:
        print("Parsing failed. Raw output:")
        print(content)
        print("Error:", e)
        return content, {}

def create_prompt_expt_smry(tst_lgc_dict: dict, tmp_ky: str, db_f1, format_instructions: str = "") -> str:
    """
    Creates a prompt for analyzing expert statements and survey summaries.

    Parameters:
        tst_lgc_dict (dict): Dictionary containing logical group data.
        tmp_ky (str): Key for the current logical group.
        db_f1: The database/vector store for retrieving implications.
        format_instructions (str): The format instructions generated by the PydanticOutputParser.

    Returns:
        str: The generated prompt.
    """
    ky = tmp_ky

    # Variables identified by the model
    tst_str_lst = tst_lgc_dict[ky]['VARIABLE_STRING'].split(',')
    tst_str_lst = [st + '__question' for st in tst_str_lst]
    print(f'Variables identified by the model: {tst_str_lst}')

    # Variables in the database
    try:
        tmp_db_var_lst = db_f1.get(ids=tst_str_lst)['ids']
        tmp_db_var_lst = list(set(tmp_db_var_lst))
        print(f'Variables in the database: {tmp_db_var_lst}')
    except Exception as e:
        print(f"Error accessing database: {e}")
        tmp_db_var_lst = []

    # Hallucinated variables
    tmp_hlc_var_lst = set(tst_str_lst) - set(tmp_db_var_lst)
    if tmp_hlc_var_lst:
        print(f'🤪 HALLUCINATED variables by the model: {tmp_hlc_var_lst}')

    # Implications for the identified variables
    if tmp_db_var_lst:
        tmp_imp_lst = [st.replace('question', 'implications') for st in tmp_db_var_lst]
        tmp_ky_lst = [st.split('__')[0] for st in tmp_imp_lst]
        try:
            tmp_imp_dict = dict(
                zip(
                    tmp_ky_lst,
                    db_f1.get(ids=tmp_imp_lst)['documents']
                )
            )
            imp_st = ' * '.join(tmp_imp_dict.values())
        except Exception as e:
            print(f"Error retrieving implications: {e}")
            imp_st = "No expert implications available."
    else:
        imp_st = "No expert implications available."

    tmp_smry = tst_lgc_dict[ky]['DESCRIPTION']

    # Generate the prompt
    prompt = f"""
    You are a very thorough research assistant that is working on a survey research project.
    The objective of this project is to study public opinion on a variety of topics.
    You are fully bilingual in English and Spanish, and can do your work in either language. But you will reply in English.
    
    Your task is to read the EXPERT STATEMENTS from one or more experts about what information they consider important to receive from the survey results. 
    Then you will read a SURVEY SUMMARY of some survey results and will write a one-paragraph reply to the experts, elaborating on how the results relate and illustrate their concerns. 
    Note that they are experts and expect a detailed and thorough reply. Reply to all of them in the same paragraph, but be sure to address all of their points. 
    Do not refer to the experts or to yourself in the first person, just write the paragraph as if it was a report.

    Note that the SURVEY SUMMARY will have QUESTION_IDS of the format 'question_id|table_id' (e.g., pxx|YYY where x, which may include strings like x_x where x is a number, and YYY is a table id). 
    They are not relevant to your answer, but you will need to keep track of these QUESTION_IDS of format pxx|YYY in your RETURN OBJECT.
    There are examples of valid QUESTION_IDS: 'p2|ABC', 'p1_1|ABC', 'p20_2|EFG', 'p23_12|EFG'. Be careful to include all the elements of the QUESTION_ID.

    Be sure to include as many relevant facts (numbers) as possible and for each fact you include, you will include the QUESTION_ID in parenthesis (e.g., pxx|TYY).

    EXPERT STATEMENTS: * {imp_st}
    SURVEY SUMMARY: {tmp_smry}

    {format_instructions}
    """
    return prompt

def get_structured_expert_summary(tst_lgc_dict: dict, tmp_ky: str, db_f1, 
                                model_name: str = "gpt-4o-mini-2024-07-18", temperature: float = 0.9) -> dict:
    """
    Generates a structured expert summary for a given key in the logical group dictionary.

    Parameters:
        tst_lgc_dict (dict): Dictionary containing logical group data.
        tmp_ky (str): Key for the current logical group.
        db_f1: The database/vector store for retrieving implications.
        model_name (str): Name of the LLM model to use.
        temperature (float): Temperature setting for the LLM.

    Returns:
        dict: Parsed response as a dictionary.
    """
    # Generate the prompt
    prompt = create_prompt_expt_smry(
        tst_lgc_dict=tst_lgc_dict,
        tmp_ky=tmp_ky,
        db_f1=db_f1,
        format_instructions=expert_summary_format_instructions
    )
    
    # Get the response from the model
    response = get_answer(prompt=prompt, model=model_name, temperature=temperature)
    
    if response is None:
        return {'EXPERT_REPLY': 'Error: No response from model'}
    
    try:
        # Parse the response
        parsed = expert_summary_parser.parse(response)
        # Ensure the parsed response is returned as a dictionary
        return parsed.model_dump()
    except Exception as e:
        print(f"Error parsing expert summary: {e}")
        return {'EXPERT_REPLY': f'Error generating expert summary: {str(e)}'}

def batch_process_expert_summaries(tst_lgc_dict: dict, db_f1, batch_size: int = 8192) -> dict:
    """
    Processes expert summaries in batches, saving checkpoints after each batch.

    Parameters:
        tst_lgc_dict (dict): Dictionary containing logical group data.
        db_f1: The database/vector store for retrieving implications.
        batch_size (int): Maximum token limit for each batch.

    Returns:
        dict: A dictionary of structured results.
    """
    # Prepare prompts and keys
    prompts = [
        create_prompt_expt_smry(tst_lgc_dict, key, db_f1, format_instructions=expert_summary_format_instructions)
        for key in tst_lgc_dict.keys()
    ]
    keys = list(tst_lgc_dict.keys())
    
    # Batch the documents
    try:
        batches = batch_documents(prompts, keys, max_tokens=batch_size, encoding_name="cl100k_base")
    except Exception as e:
        print(f"Error batching documents: {e}")
        # Fallback: process each item individually
        batches = [([prompt], [key]) for prompt, key in zip(prompts, keys)]
    
    # Initialize results dictionary
    structured_results = {}
    
    # Process each batch
    with tqdm.tqdm(total=len(keys), desc="Processing Expert Summaries") as pbar:
        for batch_docs, batch_keys in batches:
            for prompt, key in zip(batch_docs, batch_keys):
                try:
                    # Call get_structured_expert_summary for each key
                    structured_results[key] = get_structured_expert_summary(
                        tst_lgc_dict=tst_lgc_dict,
                        tmp_ky=key,
                        db_f1=db_f1,
                        model_name="gpt-4o-mini-2024-07-18",
                        temperature=0.9
                    )
                except Exception as e:
                    structured_results[key] = {'EXPERT_REPLY': f'Error: {str(e)}'}
                pbar.update(1)
    
    return structured_results

def create_prompt_trnsvl(tmp_smry_st: str, user_query: str, n_cmn_tpc: int = 3, format_instructions: str = "") -> str:
    """
    Creates a prompt for analyzing expert statements and answering a query.

    Parameters:
        tmp_smry_st (str): The list of expert statements.
        user_query (str): The query to be answered.
        n_cmn_tpc (int): Number of common topics to identify.
        format_instructions (str): The format instructions generated by the PydanticOutputParser.

    Returns:
        str: The generated prompt.
    """
    prompt = f"""
    You are a very thorough research assistant and expert in survey research and public opinion.
    You are fully bilingual in English and Spanish, and can do your work in either language.

    Your task is to perform three analyses and return a single Python dictionary with the results.

    1) Read the following list of STATEMENTS made by experts in several topics, which mention results, their implications, and their relevance.
    Each statement starts with the marker `*` and contains all information for a single statement: results, implications, and relevance.
    Identify {n_cmn_tpc} common topics across the STATEMENTS and write a one-paragraph summary of each topic, citing the most relevant numbers and explanations for each.
    Format your answer as a Python dictionary with the names of the topics as keys in ALL CAPS in the same language as the query, and the summaries as values.

    Note that the STATEMENTS will have QUESTION_IDS of the format 'question_id|table_id' (e.g., pxx|YYY where x, which may include strings like x_x where x is a number, and YYY is a table id). 
    There are examples of valid QUESTION_IDS: 'p2|ABC', 'p1_1|ABC', 'p20_2|EFG', 'p23_12|EFG'. Be careful to include all the elements of the QUESTION_ID.
    They are not relevant to your answer and your will use them only to identify the variables in the statements that your will use to write the summaries.

    Be sure to include as many relevant facts (numbers) as possible and for each fact you include, you will include the QUESTION_ID in parenthesis (e.g., pxx|TYY).

    Here are the statements: {tmp_smry_st}

    Save your summaries in a Python dictionary with the key `TOPIC_SUMMARIES`.

    2) Read your `TOPIC_SUMMARIES` and write a one-paragraph summary of the most relevant results and implications of the survey results, written for a general audience.
    Be sure to include as many relevant facts (numbers) as possible and for each fact you include, you will include the QUESTION_ID in parenthesis (e.g., pxx|TYY).
    Save your summary in a Python dictionary with the key `TOPIC_SUMMARY`.

    3) Read the QUERY and your `TOPIC_SUMMARY` and write a two-sentence answer to the QUERY that summarizes the most important points of your `TOPIC_SUMMARY`.
    Do not include any numbers or facts in your answer, just your reply to the QUERY.
    Be concise and do not repeat numbers; just answer the QUERY with the relevant ideas.
    
    Here is the QUERY: {user_query}

    Save your answer in a Python dictionary with the key `QUERY_ANSWER`.

    IMPORTANT: Your replies for all three tasks must be in the language of the QUERY.
    IMPORTANT: Make sure to return only a correctly formatted Python dictionary, without any code block formatting, markdown, or additional text.

    {format_instructions}
    """
    return prompt

def get_transversal_analysis(tmp_smry_st: str, user_query: str, 
                           model_name: str = 'gpt-4o-mini-2024-07-18', temperature: float = 0.9) -> dict:
    """
    Generates transversal analysis combining expert summaries into final report.
    """
    # Generate the prompt
    prompt = create_prompt_trnsvl(
        tmp_smry_st=tmp_smry_st,
        user_query=user_query,
        n_cmn_tpc=3,
        format_instructions=transversal_format_instructions
    )
    
    # Get the response from the model
    response = get_answer(prompt=prompt, model=model_name, temperature=temperature)
    
    if response is None:
        return {
            'TOPIC_SUMMARIES': {'ERROR': 'No response from model'},
            'TOPIC_SUMMARY': 'Error generating summary: No response from model',
            'QUERY_ANSWER': 'Error generating answer: No response from model'
        }
    
    try:
        parsed = transversal_parser.parse(response)
        return parsed.model_dump()  # Returns the parsed response as a dictionary.
    except Exception as e:
        print(f"Error parsing transversal analysis: {e}")
        return {
            'TOPIC_SUMMARIES': {'ERROR': f'Failed to generate topic summaries: {str(e)}'},
            'TOPIC_SUMMARY': f'Error generating summary: {str(e)}',
            'QUERY_ANSWER': f'Error generating answer: {str(e)}'
        }

def _deep_analyzer(tmp_pre_res_dict: dict, tmp_grade_dict: dict, user_query: str, db_f1) -> Tuple[dict, dict, dict]:
    """
    Internal function to produce the transversal analysis and expert summaries.
    This is the core analysis pipeline extracted from the notebook.
    
    Args: 
        tmp_pre_res_dict (dict): Dictionary containing preprocessed results.
        tmp_grade_dict (dict): Dictionary containing graded/relevant variables.
        user_query (str): The user's query.
        db_f1: The database/vector store for retrieving implications.
        
    Returns:
        tuple: A tuple containing three dictionaries:
        - tmp_preproc_dic: Filtered dictionary with relevant questions and summaries.
        - final_smry_dict: Dictionary with the final transversal analysis.
        - structured_expert_results: Dictionary with structured expert summaries.
    """
    print("Starting deep analysis...")
    
    # Filter for questions and summaries only
    tmp_preproc_dic = {k: v for k, v in tmp_pre_res_dict.items() if k.split('__')[1] in ['question', 'summary']}

    # Filter for relevant questions only (those in tmp_grade_dict)
    tmp_preproc_dic = {k: v for k, v in tmp_preproc_dic.items() if any(k.startswith(grade_key) for grade_key in tmp_grade_dict.keys())}

    print(f"Filtered to {len(tmp_preproc_dic)} relevant items")

    # Combine strings for processing
    tmp_combined_strings = []

    for i, (k, v) in enumerate(tmp_preproc_dic.items(), start=1):
        facet = k.split("__", 1)[1].upper()
        p_id = k

        grouped_index = (i + 1) // 2 
        parts = v.split("|", 1)
        text = parts[1] if len(parts) > 1 else parts[0]

        p_id = p_id.split("__")[0]

        tmp_combined_strings.append(f"{facet}_{grouped_index}|{p_id}: {text}")

    tmp_res_st = '\n'.join(tmp_combined_strings)
    print(f"Created combined result string with {len(tmp_combined_strings)} entries")

    # Get structured summary (patterns identification)
    print("Generating structured summary...")
    try:
        raw_content, tst_lgc_dict = get_structured_summary(
            user_query=user_query, 
            tmp_res_st=tmp_res_st, 
            tmp_grade_dict=tmp_grade_dict,
            model_name='gpt-4o-mini-2024-07-18', 
            temperature=0.0
        )
        print(f"Generated {len(tst_lgc_dict)} pattern groups")
    except Exception as e:
        print(f"Error in structured summary: {e}")
        tst_lgc_dict = {}

    # Generate expert summaries
    print("Processing expert summaries...")
    if tst_lgc_dict:
        try:
            structured_expert_results = batch_process_expert_summaries(tst_lgc_dict, db_f1)
            print(f"Generated {len(structured_expert_results)} expert summaries")
        except Exception as e:
            print(f"Error in expert summaries: {e}")
            structured_expert_results = {}
    else:
        structured_expert_results = {}

    # Create transversal analysis
    print("Generating transversal analysis...")
    if structured_expert_results:
        try:
            tmp_smry_st = ' * '.join([v['EXPERT_REPLY'] for v in structured_expert_results.values() if 'EXPERT_REPLY' in v])
            final_smry_dict = get_transversal_analysis(tmp_smry_st, user_query)
            print("Completed transversal analysis")
        except Exception as e:
            print(f"Error in transversal analysis: {e}")
            final_smry_dict = {
                'TOPIC_SUMMARIES': {'ERROR': f'Failed to generate analysis: {str(e)}'},
                'TOPIC_SUMMARY': f'Error in analysis: {str(e)}',
                'QUERY_ANSWER': f'Unable to provide answer due to error: {str(e)}'
            }
    else:
        final_smry_dict = {
            'TOPIC_SUMMARIES': {'ERROR': 'No expert summaries generated'},
            'TOPIC_SUMMARY': 'Unable to generate analysis due to lack of expert summaries',
            'QUERY_ANSWER': 'Cannot provide answer without analysis data'
        }
    
    return tmp_preproc_dic, final_smry_dict, structured_expert_results


def run_detailed_analysis(selected_variables: list, user_query: str, analysis_params: Optional[dict] = None) -> dict:
    """
    Main entry point for detailed analysis. This function provides the interface 
    between the agent workflow and the detailed analysis pipeline.
    
    Args:
        selected_variables (list): List of variable IDs selected for analysis
        user_query (str): The user's query
        analysis_params (dict): Additional parameters for analysis (optional)
        
    Returns:
        dict: Comprehensive analysis results including patterns, expert summaries, and final report
    """
    print(f"Starting detailed analysis for query: {user_query}")
    print(f"Selected variables: {selected_variables}")
    
    try:
        # Import required modules for database access
        from utility_functions import environment_setup, embedding_fun_openai
        
        # Load database and setup environment
        print("Loading database and setting up environment...")
        client, db_f1 = environment_setup(embedding_fun_openai)
        
        # For now, we'll create a mock preprocessed results dict based on selected variables
        # In the future, this should be properly integrated with the variable selection pipeline
        tmp_pre_res_dict = {}
        
        # Mock preprocessed results structure based on selected variables
        for var_id in selected_variables:
            tmp_pre_res_dict[f"{var_id}__question"] = f"{var_id}|Example question for {var_id}"
            tmp_pre_res_dict[f"{var_id}__summary"] = f"{var_id}|Mock summary data for variable {var_id}"
        
        # Create grade dictionary from selected variables
        # This simulates the grading process from the notebook
        tmp_grade_dict = {var_id: 1.0 for var_id in selected_variables}  # Simple grading for now
        
        # Run the core analysis pipeline
        print("Running deep analysis pipeline...")
        tmp_preproc_dic, final_smry_dict, structured_expert_results = _deep_analyzer(
            tmp_pre_res_dict=tmp_pre_res_dict,
            tmp_grade_dict=tmp_grade_dict,
            user_query=user_query,
            db_f1=db_f1
        )
        
        # Package results for agent workflow
        analysis_results = {
            'query': user_query,
            'selected_variables': selected_variables,
            'analysis_type': 'detailed_report',
            'success': True,
            'patterns': structured_expert_results,
            'final_analysis': final_smry_dict,
            'processed_data': {
                'filtered_data': tmp_preproc_dic,
                'expert_summaries': structured_expert_results
            },
            'report_sections': {
                'query_answer': final_smry_dict.get('QUERY_ANSWER', 'No answer available'),
                'topic_summary': final_smry_dict.get('TOPIC_SUMMARY', 'No summary available'),
                'topic_summaries': final_smry_dict.get('TOPIC_SUMMARIES', {}),
                'expert_replies': [v.get('EXPERT_REPLY', '') for v in structured_expert_results.values()]
            }
        }
        
        print("Detailed analysis completed successfully")
        return analysis_results
        
    except Exception as e:
        print(f"Error in detailed analysis: {e}")
        return {
            'query': user_query,
            'selected_variables': selected_variables,
            'analysis_type': 'detailed_report',
            'success': False,
            'error': str(e),
            'report_sections': {
                'query_answer': f'Error occurred during analysis: {str(e)}',
                'topic_summary': 'Analysis could not be completed due to technical issues',
                'topic_summaries': {},
                'expert_replies': []
            }
        }

# TODO: variable description comes from summaries in dbf_1, not from get_variable_description

def run_quick_insights_analysis(selected_variables: list, user_query: str, analysis_params: Optional[dict] = None) -> dict:
    """
    Run quick insights analysis that summarizes variable descriptions and includes plots
    for selected variables without running the full detailed analysis pipeline.
    
    Args:
        selected_variables (list): List of variable IDs selected for analysis
        user_query (str): The user's query
        analysis_params (dict): Additional parameters for analysis (optional)
        
    Returns:
        dict: Quick insights results including variable descriptions and plots
    """
    print(f"Starting quick insights analysis for query: {user_query}")
    print(f"Selected variables: {selected_variables}")
    
    try:
        # Generate variable descriptions
        variable_descriptions = {}
        for var_id in selected_variables:
            description = get_variable_description(var_id)
            variable_descriptions[var_id] = description
            print(f"Generated description for {var_id}")
        
        # Create and save plots
        print("Generating plots for selected variables...")
        plot_paths = save_plots_for_analysis(selected_variables, analysis_id=f"quick_insights_{len(selected_variables)}_vars")
        
        # Create summary insights
        insights_summary = _generate_quick_insights_summary(variable_descriptions, user_query)
        
        # Package results
        analysis_results = {
            'query': user_query,
            'selected_variables': selected_variables,
            'analysis_type': 'quick_insights',
            'success': True,
            'variable_descriptions': variable_descriptions,
            'plot_paths': plot_paths,
            'insights_summary': insights_summary,
            'report_sections': {
                'query_answer': insights_summary.get('query_answer', 'Quick insights generated successfully'),
                'variable_summaries': variable_descriptions,
                'key_findings': insights_summary.get('key_findings', []),
                'plot_references': plot_paths
            }
        }
        
        print("Quick insights analysis completed successfully")
        return analysis_results
        
    except Exception as e:
        print(f"Error in quick insights analysis: {e}")
        return {
            'query': user_query,
            'selected_variables': selected_variables,
            'analysis_type': 'quick_insights',
            'success': False,
            'error': str(e),
            'report_sections': {
                'query_answer': f'Error occurred during quick insights analysis: {str(e)}',
                'variable_summaries': {},
                'key_findings': [],
                'plot_references': {}
            }
        }


def run_plots_only_analysis(selected_variables: list, user_query: str, analysis_params: Optional[dict] = None) -> dict:
    """
    Run plots-only analysis that returns only the plots for the selected variables.
    
    Args:
        selected_variables (list): List of variable IDs selected for analysis
        user_query (str): The user's query
        analysis_params (dict): Additional parameters for analysis (optional)
        
    Returns:
        dict: Results containing only plots for the selected variables
    """
    print(f"Starting plots-only analysis for query: {user_query}")
    print(f"Selected variables: {selected_variables}")
    
    try:
        # Create and save plots
        print("Generating plots for selected variables...")
        plot_paths = save_plots_for_analysis(selected_variables, analysis_id=f"plots_only_{len(selected_variables)}_vars")
        
        # Package results
        analysis_results = {
            'query': user_query,
            'selected_variables': selected_variables,
            'analysis_type': 'plots_only',
            'success': True,
            'plot_paths': plot_paths,
            'report_sections': {
                'query_answer': f'Generated {len(plot_paths)} plots for the selected variables',
                'plot_references': plot_paths,
                'plot_count': len(plot_paths)
            }
        }
        
        print("Plots-only analysis completed successfully")
        return analysis_results
        
    except Exception as e:
        print(f"Error in plots-only analysis: {e}")
        return {
            'query': user_query,
            'selected_variables': selected_variables,
            'analysis_type': 'plots_only',
            'success': False,
            'error': str(e),
            'report_sections': {
                'query_answer': f'Error occurred during plots generation: {str(e)}',
                'plot_references': {},
                'plot_count': 0
            }
        }

# TODO: this shoould be a LLM call to generate a summary - not an automated text creation.
def _generate_quick_insights_summary(variable_descriptions: dict, user_query: str) -> dict:
    """
    Generate a quick summary based on variable descriptions.
    
    Args:
        variable_descriptions (dict): Dictionary mapping variable IDs to descriptions
        user_query (str): The user's query
        
    Returns:
        dict: Summary insights including key findings and query answer
    """
    try:
        # Extract key findings from variable descriptions
        key_findings = []
        for var_id, description in variable_descriptions.items():
            if "Top responses:" in description:
                # Extract the main finding
                finding = f"{var_id}: {description.split('Top responses:')[1].strip()}"
                key_findings.append(finding)
            elif "categories" in description:
                # Extract category information
                finding = f"{var_id}: {description}"
                key_findings.append(finding)
            else:
                # Use the full description as a finding
                key_findings.append(f"{var_id}: {description}")
        
        # Generate a query answer based on the findings
        query_answer = f"Quick insights for {len(variable_descriptions)} variables related to: {user_query}. "
        if key_findings:
            query_answer += f"Key patterns identified across {len(key_findings)} variables with visualizations provided."
        else:
            query_answer += "Variable summaries generated with accompanying plots."
        
        return {
            'key_findings': key_findings,
            'query_answer': query_answer,
            'variable_count': len(variable_descriptions)
        }
        
    except Exception as e:
        print(f"Error generating quick insights summary: {e}")
        return {
            'key_findings': [],
            'query_answer': f"Quick insights generated for {len(variable_descriptions)} variables",
            'variable_count': len(variable_descriptions)
        }


def format_detailed_report(analysis_results: dict) -> str:
    """
    Format the analysis results into a readable report.
    
    Args:
        analysis_results (dict): Results from run_detailed_analysis
        
    Returns:
        str: Formatted report text
    """
    if not analysis_results.get('success', False):
        return f"""
# Analysis Report

**Query:** {analysis_results.get('query', 'Unknown')}

**Status:** Failed
**Error:** {analysis_results.get('error', 'Unknown error')}

The analysis could not be completed. Please try again or contact support.
"""
    
    report_sections = analysis_results.get('report_sections', {})
    
    report = f"""
# Detailed Analysis Report

**Query:** {analysis_results.get('query', 'Unknown')}

## Executive Summary
{report_sections.get('query_answer', 'No summary available')}

## Analysis Overview  
{report_sections.get('topic_summary', 'No overview available')}

## Topic Analysis
"""
    
    # Add topic summaries
    topic_summaries = report_sections.get('topic_summaries', {})
    if topic_summaries:
        for topic, summary in topic_summaries.items():
            report += f"\n### {topic}\n{summary}\n"
    else:
        report += "\nNo topic summaries available.\n"
    
    # Add expert insights if available
    expert_replies = report_sections.get('expert_replies', [])
    if expert_replies and any(expert_replies):
        report += "\n## Expert Analysis\n"
        for i, reply in enumerate(expert_replies, 1):
            if reply.strip():
                report += f"\n### Expert Insight {i}\n{reply}\n"
    
    # Add metadata
    report += f"""
## Analysis Metadata
- **Analysis Type:** {analysis_results.get('analysis_type', 'Unknown')}
- **Variables Analyzed:** {len(analysis_results.get('selected_variables', []))}
- **Patterns Identified:** {len(analysis_results.get('patterns', {}))}
"""
    
    return report


def format_quick_insights_report(analysis_results: dict) -> str:
    """
    Format the quick insights analysis results into a readable report.
    
    Args:
        analysis_results (dict): Results from run_quick_insights_analysis
        
    Returns:
        str: Formatted report text
    """
    if not analysis_results.get('success', False):
        return f"""
# Quick Insights Report

**Query:** {analysis_results.get('query', 'Unknown')}

**Status:** Failed
**Error:** {analysis_results.get('error', 'Unknown error')}

The quick insights analysis could not be completed. Please try again or contact support.
"""
    
    report_sections = analysis_results.get('report_sections', {})
    variable_summaries = report_sections.get('variable_summaries', {})
    key_findings = report_sections.get('key_findings', [])
    plot_references = report_sections.get('plot_references', {})
    
    report = f"""
# Quick Insights Report

**Query:** {analysis_results.get('query', 'Unknown')}

## Summary
{report_sections.get('query_answer', 'No summary available')}

## Variable Summaries
"""
    
    # Add variable descriptions
    if variable_summaries:
        for var_id, description in variable_summaries.items():
            report += f"\n### {var_id}\n{description}\n"
    else:
        report += "\nNo variable summaries available.\n"
    
    # Add key findings
    if key_findings:
        report += "\n## Key Findings\n"
        for i, finding in enumerate(key_findings, 1):
            report += f"{i}. {finding}\n"
    
    # Add plot references
    if plot_references:
        report += "\n## Generated Visualizations\n"
        for var_id, plot_path in plot_references.items():
            if var_id != 'summary':
                report += f"- **{var_id}**: Plot saved to `{plot_path}`\n"
        
        if 'summary' in plot_references:
            report += f"- **Summary Grid**: Combined plot saved to `{plot_references['summary']}`\n"
    
    # Add metadata
    report += f"""
## Analysis Metadata
- **Analysis Type:** Quick Insights
- **Variables Analyzed:** {len(analysis_results.get('selected_variables', []))}
- **Plots Generated:** {len(plot_references)}
"""
    
    return report


def format_plots_only_report(analysis_results: dict) -> str:
    """
    Format the plots-only analysis results into a readable report.
    
    Args:
        analysis_results (dict): Results from run_plots_only_analysis
        
    Returns:
        str: Formatted report text
    """
    if not analysis_results.get('success', False):
        return f"""
# Plots Report

**Query:** {analysis_results.get('query', 'Unknown')}

**Status:** Failed
**Error:** {analysis_results.get('error', 'Unknown error')}

The plots generation could not be completed. Please try again or contact support.
"""
    
    report_sections = analysis_results.get('report_sections', {})
    plot_references = report_sections.get('plot_references', {})
    
    report = f"""
# Plots Report

**Query:** {analysis_results.get('query', 'Unknown')}

## Summary
{report_sections.get('query_answer', 'No summary available')}

## Generated Visualizations
"""
    
    # Add plot references
    if plot_references:
        for var_id, plot_path in plot_references.items():
            if var_id != 'summary':
                report += f"- **{var_id}**: `{plot_path}`\n"
        
        if 'summary' in plot_references:
            report += f"- **Summary Grid**: `{plot_references['summary']}`\n"
    else:
        report += "\nNo plots were generated.\n"
    
    # Add metadata
    report += f"""
## Analysis Metadata
- **Analysis Type:** Plots Only
- **Variables Analyzed:** {len(analysis_results.get('selected_variables', []))}
- **Plots Generated:** {report_sections.get('plot_count', 0)}
"""
    
    return report
