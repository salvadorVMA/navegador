#!/usr/bin/env python3
"""
SES Relationship Plotting Utilities

This module contains functions to create visualizations for the relationship between 
any SES variable and any other variable, adapting the logic from plotting_utils.py
create_multiple_plots() function.

SES Variables:
- sexo: Gender (2 categories: '01'=mujer, '02'=hombre)
- edad: Age (7 categories: 0-18, 19-24, 25-34, 35-44, 45-54, 55-64, 65+)
- edu: Education (3 categories: básica, media, superior)
- region: Geographic region (4 categories: Norte, Centro, Centro Occidente, Sureste)
- empleo: Employment (5 categories: empleado, no empleado, estudiante, hogar, jubilado)

Visualization logic:
- ≤4 categories: Barplot with adjacent target variable values for each SES category
- ≥5 categories: Line plot with one line per SES category
- region variable: Heatmap visualization
"""

import matplotlib.pyplot as plt
import matplotlib.figure
import matplotlib.axes
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, Union, List
import warnings

# Set default style
plt.style.use('default')
sns.set_palette("husl")

def get_ses_variable_info(los_mex_dict: dict, ses_var: str, survey_name: Optional[str] = None) -> Dict:
    """
    Get information about a SES variable including its categories and labels.
    
    Parameters:
    -----------
    los_mex_dict : dict
        Dictionary containing survey data
    ses_var : str
        SES variable name (sexo, edad, edu, region, empleo)
    survey_name : str, optional
        Survey name to get specific labels from
        
    Returns:
    --------
    Dict with variable info including categories, labels, and category count
    """
    ses_info = {
        'variable': ses_var,
        'categories': [],
        'labels': {},
        'category_count': 0,
        'is_ordinal': ses_var in ['edad', 'edu']  # escol mapped to edu, edad is ordinal
    }
    
    # Standard SES variable categories based on workspace analysis
    if ses_var == 'sexo':
        ses_info['categories'] = ['01', '02']
        ses_info['labels'] = {'01': 'Mujer', '02': 'Hombre'}
        ses_info['category_count'] = 2
        
    elif ses_var == 'edad':
        ses_info['categories'] = ['0-18', '19-24', '25-34', '35-44', '45-54', '55-64', '65+']
        ses_info['labels'] = {cat: cat for cat in ses_info['categories']}
        ses_info['category_count'] = 7
        
    elif ses_var == 'edu':
        ses_info['categories'] = ['01', '02', '03']
        ses_info['labels'] = {'01': 'Básica', '02': 'Media', '03': 'Superior'}
        ses_info['category_count'] = 3
        
    elif ses_var == 'region':
        ses_info['categories'] = ['01', '02', '03', '04']
        ses_info['labels'] = {
            '01': 'Norte', 
            '02': 'Centro', 
            '03': 'Centro Occidente', 
            '04': 'Sureste'
        }
        ses_info['category_count'] = 4
        
    elif ses_var == 'empleo':
        ses_info['categories'] = ['01', '02', '03', '04', '05']
        ses_info['labels'] = {
            '01': 'Empleado',
            '02': 'No empleado', 
            '03': 'Estudiante',
            '04': 'Hogar',
            '05': 'Jubilado'
        }
        ses_info['category_count'] = 5
        
    # Try to get labels from survey metadata if available
    if survey_name and 'enc_dict' in los_mex_dict:
        try:
            survey_data = los_mex_dict['enc_dict'][survey_name]
            if 'metadata' in survey_data and 'variable_value_labels' in survey_data['metadata']:
                variable_labels = survey_data['metadata']['variable_value_labels']
                
                # For education, check if 'escol' labels are available
                label_key = 'escol' if ses_var == 'edu' and 'escol' in variable_labels else ses_var
                
                if label_key in variable_labels:
                    metadata_labels = variable_labels[label_key]
                    # Update labels with metadata info if available
                    for code, label in metadata_labels.items():
                        if str(code) in ses_info['labels'] or code in ses_info['labels']:
                            ses_info['labels'][code] = label
        except Exception as e:
            print(f"Warning: Could not retrieve labels from metadata: {e}")
    
    return ses_info


def create_ses_relationship_plot(df: pd.DataFrame, 
                                ses_var: str, 
                                target_var: str,
                                ses_labels: Optional[Dict] = None,
                                target_labels: Optional[Dict] = None,
                                title: Optional[str] = None,
                                figsize: Tuple[int, int] = (12, 8),
                                color_palette: str = "random",
                                save_path: Optional[str] = None) -> matplotlib.figure.Figure:
    """
    Create a plot to showcase the relationship between any SES variable and any other variable.
    
    Visualization logic adapted from create_multiple_plots():
    - ≤4 SES categories: Barplot with adjacent target variable values for each SES category
    - ≥5 SES categories: Line plot with one line per SES category
    - SES 'region': Heatmap visualization
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the data
    ses_var : str
        SES variable name (sexo, edad, edu, region, empleo)
    target_var : str
        Target variable to analyze relationship with
    ses_labels : dict, optional
        Labels for SES variable categories
    target_labels : dict, optional
        Labels for target variable categories
    title : str, optional
        Plot title
    figsize : tuple
        Figure size (width, height)
    color_palette : str
        Color palette for visualization
    save_path : str, optional
        Path to save the plot
        
    Returns:
    --------
    matplotlib.figure.Figure
        The created figure
    """
    # Clean data - remove missing values
    clean_df = df[[ses_var, target_var]].dropna()
    
    if clean_df.empty:
        raise ValueError(f"No valid data found for variables {ses_var} and {target_var}")
    
    # Get SES variable info
    ses_categories = clean_df[ses_var].unique()
    ses_category_count = len(ses_categories)
    
    # Set up labels
    if ses_labels is None:
        ses_labels = {cat: str(cat) for cat in ses_categories}
    if target_labels is None:
        target_labels = {cat: str(cat) for cat in clean_df[target_var].unique()}
    
    # Set color palette - create CONSISTENT color mapping across all plots
    # Get all possible target categories to ensure consistent coloring
    all_target_categories = sorted(clean_df[target_var].unique())
    
    # Handle random colormap selection
    if color_palette == "random":
        import random
        seasonal_colormaps = ['spring', 'summer', 'autumn', 'winter', 'viridis', 'plasma', 'inferno', 'magma']
        color_palette = random.choice(seasonal_colormaps)
        print(f"🎨 Randomly selected colormap: {color_palette}")
    
    # Identify residual/non-response categories (typically 8, 9, 88, 99, etc.)
    residual_categories = []
    substantive_categories = []
    
    for cat in all_target_categories:
        cat_num = float(cat) if pd.notna(cat) else None
        # Common patterns for residual categories in surveys
        if (cat_num is not None and 
            ((cat_num >= 8.0 and cat_num <= 10.0) or  # 8, 9, 10 (no answer, don't know, etc.)
             cat_num >= 88.0) or  # 88, 99, etc.
            (target_labels and str(target_labels.get(cat, '')).lower() in 
             ['no answer', 'no contesta', 'no sabe', 'does not know', 'doesn\'t know', 'dk', 'na', 'refuse'])):
            residual_categories.append(cat)
        else:
            substantive_categories.append(cat)
    
    # Use matplotlib colormap for substantive categories only
    if color_palette in ['spring', 'summer', 'autumn', 'winter', 'viridis', 'plasma', 'inferno', 'magma']:
        import matplotlib.pyplot as plt
        cmap = plt.cm.get_cmap(color_palette)
        substantive_colors = [cmap(i / max(1, len(substantive_categories) - 1)) for i in range(len(substantive_categories))]
    else:
        # Fallback to seaborn palette for substantive categories
        substantive_colors = sns.color_palette(color_palette, n_colors=len(substantive_categories))
    
    # Create consistent color mapping 
    target_color_map = {}
    
    # Assign colorful colors to substantive categories
    for i, cat in enumerate(substantive_categories):
        target_color_map[cat] = substantive_colors[i % len(substantive_colors)]
    
    # Assign dark gray to residual categories
    dark_gray = '#404040'  # Dark gray color
    for cat in residual_categories:
        target_color_map[cat] = dark_gray
    
    print(f"🎨 Color assignment: {len(substantive_categories)} substantive categories (colorful), {len(residual_categories)} residual categories (dark gray)")
    
    # Import matplotlib for plotting (ensure it's available in the function scope)
    import matplotlib.pyplot as plt
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Determine plot type based on SES variable characteristics
    if ses_var == 'region' or ses_var == 'Region':
        # Special case: Always use enhanced heatmap for region
        _create_regional_heatmap_plot(clean_df, ses_var, target_var, ses_labels, target_labels, ax, target_color_map)
        plot_type = "Regional Heatmap"
        
    elif ses_category_count <= 3:
        # Barplot for ≤3 categories (stacked bars)
        _create_barplot_ses(clean_df, ses_var, target_var, ses_labels, target_labels, ax, target_color_map)
        plot_type = "Barplot"
        
    else:
        # Line plot for ≥4 categories  
        _create_lineplot_ses(clean_df, ses_var, target_var, ses_labels, target_labels, ax, target_color_map)
        plot_type = "Line Plot"
    
    # Set title
    if title is None:
        ses_name = ses_labels.get(list(ses_categories)[0], ses_var) if len(ses_categories) > 0 else ses_var
        title = f"{plot_type}: Relationship between {ses_var.title()} and {target_var.title()}\n({ses_category_count} SES categories)"
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Improve layout
    plt.tight_layout()
    
    # Save if requested
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")
    
    return fig


def _create_barplot_ses(df: pd.DataFrame,
                       ses_var: str,
                       target_var: str,
                       ses_labels: Dict,
                       target_labels: Dict,
                       ax: matplotlib.axes.Axes,
                       target_color_map: Dict) -> None:
    """
    Create stacked barplot with parallel bars for each SES category.
    Colors represent target variable categories, with consistent color mapping across plots.
    """
    # Create crosstab - SES categories as columns, target as rows for stacking
    crosstab = pd.crosstab(df[target_var], df[ses_var], normalize='columns') * 100
    
    # Get target categories in consistent order for color mapping
    target_categories = list(crosstab.index)
    
    # Create the stacked horizontal bar plot
    bar_height = 0.6
    y_positions = np.arange(len(crosstab.columns))
    
    # Initialize bottom values for stacking
    bottom_values = np.zeros(len(crosstab.columns))
    
    # Create stacked bars - each target category becomes a segment with its consistent color
    for target_cat in target_categories:
        if target_cat in target_color_map:  # Only plot categories that exist in color map
            values = crosstab.loc[target_cat].values
            label = target_labels.get(target_cat, str(target_cat))
            color = target_color_map[target_cat]
            
            bars = ax.barh(y_positions, values, height=bar_height,
                          left=bottom_values, label=label, 
                          color=color, alpha=0.8,
                          edgecolor='white', linewidth=0.5)
            
            # Add percentage labels for segments > 5%
            for j, (bar, value) in enumerate(zip(bars, values)):
                if value > 5:  # Only label segments > 5%
                    x_pos = bottom_values[j] + value / 2
                    ax.text(x_pos, bar.get_y() + bar.get_height()/2, 
                           f'{value:.1f}%', ha='center', va='center', 
                           fontsize=8, fontweight='bold')
            
            bottom_values += values
    
    # Set labels and formatting
    ax.set_xlabel('Percentage')
    ax.set_ylabel(f'{ses_var.title()} Categories')
    ax.set_yticks(y_positions)
    ax.set_yticklabels([ses_labels.get(cat, str(cat)) for cat in crosstab.columns])
    ax.set_xlim(0, 100)
    
    # Add legend for target variable categories using proper labels
    ax.legend(title=f'{target_var.title()} Categories', 
              bbox_to_anchor=(1.05, 1), loc='upper left')
def _create_lineplot_ses(df: pd.DataFrame,
                        ses_var: str,
                        target_var: str, 
                        ses_labels: Dict,
                        target_labels: Dict,
                        ax: matplotlib.axes.Axes,
                        target_color_map: Dict) -> None:
    """
    Create line plot with one line per target category, using enhanced colormap system.
    X-axis shows SES categories, Y-axis shows percentages, lines represent target categories.
    """
    # Create crosstab for the relationship - SES categories as columns, target as rows
    crosstab = pd.crosstab(df[target_var], df[ses_var], normalize='columns') * 100
    
    # Get SES and target categories in proper order
    ses_categories = sorted(list(crosstab.columns))
    target_categories = sorted(list(crosstab.index))
    
    # Plot lines for each target category using the enhanced colormap
    for target_cat in target_categories:
        if target_cat in target_color_map:  # Only plot categories that exist in color map
            values = crosstab.loc[target_cat, ses_categories].values
            label = target_labels.get(target_cat, str(target_cat))
            color = target_color_map[target_cat]
            
            ax.plot(range(len(ses_categories)), values, marker='o', linewidth=2.5, 
                    label=label, color=color, markersize=6, alpha=0.8)
    
    # Set labels and formatting with SES categories on x-axis
    ses_x_labels = [ses_labels.get(cat, str(cat)) for cat in ses_categories]
    ax.set_xticks(range(len(ses_categories)))
    ax.set_xticklabels(ses_x_labels, rotation=0, ha='center')
    ax.set_xlabel(f'{ses_var.title()} Categories', fontweight='bold')
    ax.set_ylabel('Percentage', fontweight='bold')
    ax.set_title(f'Line Plot: {target_var.title()} by {ses_var.title()}\n(Enhanced Colormap Applied)', 
                fontweight='bold')
    
    # Enhanced legend showing target categories with proper colors
    ax.legend(title=f'{target_var.title()} Categories', 
              bbox_to_anchor=(1.05, 1), loc='upper left',
              title_fontsize=10, fontsize=9)
    ax.grid(True, alpha=0.3, linestyle='--')


def _create_regional_heatmap_plot(df: pd.DataFrame,
                                ses_var: str,
                                target_var: str,
                                ses_labels: Dict,
                                target_labels: Dict,
                                ax: matplotlib.axes.Axes,
                                target_color_map: Dict) -> None:
    """
    Create enhanced heatmap visualization for regional data with Mexican geography context.
    Uses enhanced colormap system to distinguish substantive vs residual categories.
    """
    # Create crosstab for the relationship
    crosstab = pd.crosstab(df[ses_var], df[target_var], normalize='index') * 100
    
    # Enhanced Mexican regional labels (based on typical Mexican geographical divisions)
    default_regional_labels = {
        1.0: 'Centro Norte\n(Bajío)',
        2.0: 'Centro\n(Ciudad de México)', 
        3.0: 'Centro Sur\n(Morelos, Guerrero)',
        4.0: 'Norte\n(Frontera)'
    }
    
    # Use provided labels or fallback to enhanced defaults
    if not ses_labels or all(str(v).replace('.0', '') == str(k).replace('.0', '') for k, v in ses_labels.items()):
        enhanced_labels = default_regional_labels
    else:
        enhanced_labels = ses_labels
    
    # Create heatmap with relabeled data
    heatmap_data = crosstab.copy()
    
    # Rename indices and columns with enhanced labels
    new_index = [enhanced_labels.get(cat, f'Region {cat}') for cat in heatmap_data.index]
    new_columns = [target_labels.get(cat, str(cat)) for cat in heatmap_data.columns]
    heatmap_data.index = pd.Index(new_index)
    heatmap_data.columns = pd.Index(new_columns)
    
    # Create enhanced heatmap with custom colormap that respects residual category distinction
    # Use a diverging colormap for better visual separation
    sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='RdYlBu_r',
                ax=ax, cbar_kws={'label': 'Percentage (%)', 'shrink': 0.8},
                linewidths=1, linecolor='white',
                annot_kws={'fontsize': 10, 'fontweight': 'bold'})
    
    # Enhanced styling for geographical context with colormap note
    ax.set_xlabel(f'{target_var.title()} Categories', fontsize=12, fontweight='bold')
    ax.set_ylabel('Mexican Regions', fontsize=12, fontweight='bold')
    ax.set_title(f'Regional Analysis - Enhanced Colormap\n(Substantive Categories Highlighted, Residual in Gray)', 
                fontsize=13, fontweight='bold', pad=20)
    
    # Rotate labels for better readability
    ax.tick_params(axis='x', rotation=45)
    ax.tick_params(axis='y', rotation=0)


def _create_heatmap_plot(df: pd.DataFrame,
                        ses_var: str,
                        target_var: str,
                        ses_labels: Dict,
                        target_labels: Dict,
                        ax: matplotlib.axes.Axes,
                        target_color_map: Dict) -> None:
    """
    Create heatmap visualization with enhanced colormap system that respects residual categories.
    """
    # Create crosstab for the relationship
    crosstab = pd.crosstab(df[ses_var], df[target_var], normalize='index') * 100
    
    # Create heatmap with relabeled data
    heatmap_data = crosstab.copy()
    
    # Rename indices and columns with labels
    new_index = [ses_labels.get(cat, str(cat)) for cat in heatmap_data.index]
    new_columns = [target_labels.get(cat, str(cat)) for cat in heatmap_data.columns]
    heatmap_data.index = pd.Index(new_index)
    heatmap_data.columns = pd.Index(new_columns)
    
    # Create heatmap using enhanced colormap approach
    # Use a neutral diverging colormap that works well with the enhanced legend
    sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='RdYlBu_r',
                ax=ax, cbar_kws={'label': 'Percentage (%)', 'shrink': 0.8},
                linewidths=0.5, linecolor='white')
    
    # Set labels with enhanced colormap context
    ax.set_xlabel(f'{target_var.title()} Categories\n(Enhanced Colormap Applied)', fontsize=11)
    ax.set_ylabel(f'{ses_var.title()} Categories', fontsize=11)
    ax.set_title(f'Heatmap Analysis - Enhanced Colors\n(Residual Categories in Gray)', 
                fontsize=12, fontweight='bold', pad=15)
    
    # Rotate labels for better readability
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    plt.setp(ax.get_yticklabels(), rotation=0)


def analyze_ses_relationship_strength(df: pd.DataFrame,
                                     ses_var: str,
                                     target_var: str) -> Dict:
    """
    Analyze the strength of relationship between SES variable and target variable.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the data
    ses_var : str
        SES variable name
    target_var : str
        Target variable name
        
    Returns:
    --------
    Dict with relationship statistics
    """
    from scipy.stats import chi2_contingency
    
    # Clean data
    clean_df = df[[ses_var, target_var]].dropna()
    
    if clean_df.empty:
        return {'error': 'No valid data for analysis'}
    
    # Create contingency table
    contingency_table = pd.crosstab(clean_df[ses_var], clean_df[target_var])
    
    # Perform chi-square test
    chi2, p_value, dof, expected = chi2_contingency(contingency_table)
    
    # Calculate Cramér's V
    n = contingency_table.sum().sum()
    cramers_v = np.sqrt(chi2 / (n * (min(contingency_table.shape) - 1)))
    
    # Sample size by SES category
    ses_counts = clean_df[ses_var].value_counts().to_dict()
    
    return {
        'chi_square': chi2,
        'p_value': p_value,
        'degrees_of_freedom': dof,
        'cramers_v': cramers_v,
        'sample_size': len(clean_df),
        'ses_category_counts': ses_counts,
        'relationship_strength': 'strong' if cramers_v > 0.25 else 'moderate' if cramers_v > 0.1 else 'weak'
    }


def create_ses_summary_grid(los_mex_dict: dict,
                           survey_name: str,
                           target_var: str,
                           ses_vars: Optional[List[str]] = None,
                           figsize: Tuple[int, int] = (20, 12),
                           save_path: Optional[str] = None) -> matplotlib.figure.Figure:
    """
    Create a summary grid showing relationships between multiple SES variables and a target variable.
    Uses enhanced colormap system to distinguish substantive vs residual categories.
    
    Parameters:
    -----------
    los_mex_dict : dict
        Dictionary containing survey data
    survey_name : str
        Name of the survey to analyze
    target_var : str
        Target variable to analyze relationships with
    ses_vars : list, optional
        List of SES variables to include. Default: ['sexo', 'edad', 'edu', 'region', 'empleo']
    figsize : tuple
        Figure size (width, height)
    save_path : str, optional
        Path to save the plot
        
    Returns:
    --------
    matplotlib.figure.Figure
        The created figure with subplots
    """
    # Import matplotlib for plotting
    import matplotlib.pyplot as plt
    
    if ses_vars is None:
        ses_vars = ['sexo', 'edad', 'edu', 'region', 'empleo']
    
    # Get survey data
    if 'enc_dict' not in los_mex_dict or survey_name not in los_mex_dict['enc_dict']:
        raise ValueError(f"Survey '{survey_name}' not found in dictionary")
    
    df = los_mex_dict['enc_dict'][survey_name]['dataframe']
    
    # Filter SES variables that exist in the data
    available_ses_vars = [var for var in ses_vars if var in df.columns]
    
    if not available_ses_vars:
        raise ValueError(f"None of the specified SES variables found in {survey_name}")
    
    # Calculate grid dimensions
    n_plots = len(available_ses_vars)
    n_cols = min(3, n_plots)
    n_rows = (n_plots + n_cols - 1) // n_cols
    
    # Create subplots
    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    if n_plots == 1:
        axes = [axes]
    elif n_rows == 1:
        axes = [axes] if n_plots == 1 else axes
    else:
        axes = axes.flatten()
    
    # Create individual plots
    i = 0  # Initialize i to avoid unbound variable
    for i, ses_var in enumerate(available_ses_vars):
        ax = axes[i]
        
        try:
            # Get SES variable info
            ses_info = get_ses_variable_info(los_mex_dict, ses_var, survey_name)
            
            # Clean data for this specific pair
            clean_df = df[[ses_var, target_var]].dropna()
            
            if clean_df.empty:
                ax.text(0.5, 0.5, f'No data available\nfor {ses_var} vs {target_var}', 
                       ha='center', va='center', transform=ax.transAxes)
                ax.set_title(f'{ses_var.title()} vs {target_var.title()}')
                continue
            
            # Determine plot type and create color map for target variable
            ses_category_count = len(clean_df[ses_var].unique())
            
            # Create consistent color mapping for this target variable using enhanced system
            target_categories = sorted(clean_df[target_var].unique())
            
            # Apply enhanced colormap logic for residual category detection
            import random
            seasonal_colormaps = ['spring', 'summer', 'autumn', 'winter', 'viridis', 'plasma', 'inferno', 'magma']
            selected_colormap = random.choice(seasonal_colormaps)
            
            # Identify residual/non-response categories
            residual_categories = []
            substantive_categories = []
            
            for cat in target_categories:
                cat_num = float(cat) if pd.notna(cat) else None
                # Common patterns for residual categories in surveys
                if (cat_num is not None and 
                    ((cat_num >= 8.0 and cat_num <= 10.0) or  # 8, 9, 10
                     cat_num >= 88.0)):  # 88, 99, etc.
                    residual_categories.append(cat)
                else:
                    substantive_categories.append(cat)
            
            # Create color mapping with enhanced logic
            if selected_colormap in ['spring', 'summer', 'autumn', 'winter', 'viridis', 'plasma', 'inferno', 'magma']:
                import matplotlib.pyplot as plt
                cmap = plt.cm.get_cmap(selected_colormap)
                substantive_colors = [cmap(i / max(1, len(substantive_categories) - 1)) for i in range(len(substantive_categories))]
            else:
                substantive_colors = sns.color_palette(selected_colormap, n_colors=len(substantive_categories))
            
            target_color_map = {}
            # Assign colorful colors to substantive categories
            for i, cat in enumerate(substantive_categories):
                target_color_map[cat] = substantive_colors[i % len(substantive_colors)]
            # Assign dark gray to residual categories
            dark_gray = '#404040'
            for cat in residual_categories:
                target_color_map[cat] = dark_gray
            
            if ses_var == 'region' or ses_var == 'Region':
                _create_regional_heatmap_plot(clean_df, ses_var, target_var, 
                                           ses_info['labels'], {}, ax, target_color_map)
                plot_type = "Regional Heatmap"
            elif ses_category_count <= 4:
                _create_barplot_ses(clean_df, ses_var, target_var,
                                  ses_info['labels'], {}, ax, target_color_map)
                plot_type = "Barplot"
            else:
                _create_lineplot_ses(clean_df, ses_var, target_var,
                                    ses_info['labels'], {}, ax, target_color_map)
                plot_type = "Line Plot"
            
            # Set subplot title
            ax.set_title(f'{ses_var.title()} vs {target_var.title()}\n({plot_type}, n={len(clean_df)})')
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Error creating plot\nfor {ses_var}:\n{str(e)}', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'{ses_var.title()} vs {target_var.title()} (Error)')
    
    # Hide empty subplots
    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)
    
    # Set overall title
    fig.suptitle(f'SES Variables Relationship Analysis: {target_var.title()}\nSurvey: {survey_name}', 
                fontsize=16, fontweight='bold', y=0.98)
    
    # Improve layout
    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    
    # Save if requested
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Summary grid saved to: {save_path}")
    
    return fig


# Example usage and testing functions
def test_ses_plotting():
    """
    Test function to verify SES plotting functionality.
    """
    print("SES Relationship Plotting Module Loaded Successfully!")
    print("\nAvailable functions:")
    print("- create_ses_relationship_plot(): Main function for individual SES-target relationships")
    print("- create_ses_summary_grid(): Create grid of multiple SES relationships")
    print("- analyze_ses_relationship_strength(): Statistical analysis of relationships")
    print("- get_ses_variable_info(): Get SES variable category information")
    
    print("\nSES Variables supported:")
    print("- sexo (2 categories): Gender")
    print("- edad (7 categories): Age groups")  
    print("- edu (3 categories): Education level")
    print("- region (4 categories): Geographic regions")
    print("- empleo (5 categories): Employment status")
    
    print("\nVisualization logic:")
    print("- ≤4 SES categories: Barplot with adjacent target values")
    print("- ≥5 SES categories: Line plot with one line per SES category")
    print("- SES 'region': Always uses heatmap visualization")


if __name__ == "__main__":
    test_ses_plotting()
