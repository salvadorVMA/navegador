"""
Plotting Module for Navegador Project

This module contains plotting functions extracted from nav_py13_reporte1.ipynb
for generating visualizations of survey data, including enhanced SES relationship plotting.

SES Variables:
- sexo: Gender (2 categories: '01'=mujer, '02'=hombre)
- edad: Age (6 categories: age groups)
- edu: Education (3 categories: básica, media, superior)
- region: Geographic region (4 categories: Norte, Centro, Centro Occidente, Sureste)
- empleo: Employment (4 categories: empleado, no empleado, estudiante, hogar)

Visualization logic for SES relationships:
- ≤3 categories: Barplot with target variable values for each SES category
- ≥4 categories: Line plot with one line per target category
- region variable: Regional heatmap visualization
"""

import os
import re
# Set matplotlib backend to non-GUI before importing pyplot to avoid threading issues on macOS
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend to prevent GUI threading issues
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.figure
import matplotlib.axes
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
import seaborn as sns
from typing import List, Dict, Tuple, Optional, Union
from dataset_knowledge import df_tables
import warnings


def create_plot(df: pd.DataFrame, question: str, figsize: Tuple[int, int] = (6, 8)) -> Figure:
    """
    Creates a bar plot (horizontal if rows <= 6, vertical otherwise) of the survey data.
    
    Args:
        df (pd.DataFrame): DataFrame containing the data to plot.
        question (str): The survey question to use as the plot title.
        figsize (tuple): Figure size as (width, height).
        
    Returns:
        matplotlib.pyplot.figure: The matplotlib figure object.
    """
    # Clean the data - remove NaN values and ensure we have numeric data
    df_clean = df.dropna()
    
    if df_clean.empty:
        # Create empty plot if no data
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, 'No data available for this variable', 
                ha='center', va='center', transform=ax.transAxes)
        ax.set_title(question, wrap=True, fontsize=10, fontweight='bold')
        return fig
    
    # Determine plot type based on the number of rows
    if len(df_clean) <= 6:
        # Horizontal bar plot
        fig, ax = plt.subplots(figsize=figsize)
        
        # Create horizontal bar plot
        y_pos = np.arange(len(df_clean))
        values = np.array(df_clean.iloc[:, 0].values, dtype=float)  # Convert to numpy array with float dtype
        labels = df_clean.index.tolist()
        
        bars = ax.barh(y_pos, values, color='skyblue', edgecolor='black', linewidth=0.5)
        
        # Customize the plot
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel('Percentage (%)', fontsize=9)
        ax.set_title(question, wrap=True, fontsize=10, fontweight='bold', pad=20)
        
        # Add value labels on bars
        for i, (bar, value) in enumerate(zip(bars, values)):
            width = bar.get_width()
            ax.text(width + max(values) * 0.01, bar.get_y() + bar.get_height()/2, 
                   f'{value:.1f}%', ha='left', va='center', fontsize=8)
        
        # Adjust layout
        plt.tight_layout()
        
    else:
        # Vertical bar plot for more categories
        fig, ax = plt.subplots(figsize=figsize)
        
        # Create vertical bar plot
        x_pos = np.arange(len(df_clean))
        values = np.array(df_clean.iloc[:, 0].values, dtype=float)  # Convert to numpy array with float dtype
        labels = df_clean.index.tolist()
        
        bars = ax.bar(x_pos, values, color='lightcoral', edgecolor='black', linewidth=0.5)
        
        # Customize plot
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
        ax.set_ylabel('Percentage (%)', fontsize=9)
        ax.set_title(question, wrap=True, fontsize=10, fontweight='bold', pad=20)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max(values) * 0.01,
                   f'{value:.1f}%', ha='center', va='bottom', fontsize=8, rotation=0)
        
        # Adjust layout
        plt.tight_layout()
    
    return fig


def create_multiple_plots(var_ids: List[str], save_plots: bool = True, plot_dir: str = "plot_images") -> Dict[str, Figure]:
    """
    Creates multiple plots for a list of variable IDs.
    
    Args:
        var_ids (list): List of variable IDs to plot.
        save_plots (bool): Whether to save plots to disk.
        plot_dir (str): Directory to save plots.
        
    Returns:
        dict: Dictionary mapping variable IDs to matplotlib figure objects.
    """
    plots = {}
    
    # Create plot directory if it doesn't exist
    if save_plots and not os.path.exists(plot_dir):
        os.makedirs(plot_dir)
    
    for var_id in var_ids:
        print(f"Creating plot for {var_id}...")
        
        try:
            # Check if variable exists in df_tables
            if var_id in df_tables:
                df = df_tables[var_id]
                
                # Get question text (this should be improved to get actual question text)
                question = f"Variable: {var_id}"
                
                # Try to get a better question title from the data structure
                if hasattr(df, 'name') and df.name:
                    question = df.name
                elif len(df.columns) > 0:
                    question = str(df.columns[0])
                
                print(f"plotting {question} ({len(df)} rows)")
                
                # Create the plot
                fig = create_plot(df, question)
                plots[var_id] = fig
                
                # Save plot if requested
                if save_plots:
                    plot_filename = f"plot_{var_id.replace('|', '_')}.png"
                    plot_path = os.path.join(plot_dir, plot_filename)
                    fig.savefig(plot_path, dpi=150, bbox_inches='tight')
                    print(f"Saved plot to {plot_path}")
                
            else:
                print(f"Warning: Variable {var_id} not found in df_tables")
                
        except Exception as e:
            print(f"Error creating plot for {var_id}: {e}")
            continue
    
    return plots


def create_summary_plots_grid(var_ids: List[str], max_cols: int = 2, figsize: Tuple[int, int] = (12, 8)) -> Figure:
    """
    Creates a grid of plots for multiple variables in a single figure.
    
    Args:
        var_ids (list): List of variable IDs to plot.
        max_cols (int): Maximum number of columns in the grid.
        figsize (tuple): Figure size as (width, height).
        
    Returns:
        matplotlib.pyplot.figure: The matplotlib figure object containing all plots.
    """
    n_plots = len(var_ids)
    
    if n_plots == 0:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, 'No variables selected for plotting', 
                ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Survey Data Visualization')
        return fig
    
    # Calculate grid dimensions
    ncols = min(max_cols, n_plots)
    nrows = (n_plots + ncols - 1) // ncols
    
    # Create subplots
    fig, axes = plt.subplots(nrows, ncols, 
                            figsize=(figsize[0] * ncols, figsize[1] * nrows),
                            squeeze=False)
    
    # Flatten axes array for easier indexing
    axes_flat = axes.flatten()
    
    for i, var_id in enumerate(var_ids):
        ax = axes_flat[i]
        
        try:
            if var_id in df_tables:
                df = df_tables[var_id]
                df_clean = df.dropna()
                
                if not df_clean.empty:
                    # Create mini plot
                    question = f"{var_id}"
                    
                    if len(df_clean) <= 6:
                        # Horizontal bar plot
                        y_pos = np.arange(len(df_clean))
                        values = df_clean.iloc[:, 0].values
                        labels = df_clean.index.tolist()
                        
                        ax.barh(y_pos, values, color='skyblue', edgecolor='black', linewidth=0.5)
                        ax.set_yticks(y_pos)
                        ax.set_yticklabels(labels, fontsize=8)
                        ax.set_xlabel('Percentage (%)', fontsize=8)
                        
                    else:
                        # Vertical bar plot
                        x_pos = np.arange(len(df_clean))
                        values = df_clean.iloc[:, 0].values
                        labels = df_clean.index.tolist()
                        
                        ax.bar(x_pos, values, color='lightcoral', edgecolor='black', linewidth=0.5)
                        ax.set_xticks(x_pos)
                        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
                        ax.set_ylabel('Percentage (%)', fontsize=8)
                    
                    ax.set_title(question, fontsize=9, fontweight='bold')
                    
                else:
                    ax.text(0.5, 0.5, f'No data for {var_id}', 
                           ha='center', va='center', transform=ax.transAxes)
                    ax.set_title(var_id, fontsize=9)
                    
            else:
                ax.text(0.5, 0.5, f'{var_id}\nNot found', 
                       ha='center', va='center', transform=ax.transAxes)
                ax.set_title(var_id, fontsize=9)
                
        except Exception as e:
            ax.text(0.5, 0.5, f'{var_id}\nError: {str(e)}', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(var_id, fontsize=9)
    
    # Hide unused subplots
    for i in range(n_plots, len(axes_flat)):
        axes_flat[i].set_visible(False)
    
    plt.tight_layout()
    return fig

# TODO: variable description comes from summaries in dbf_1, not from the data description below
def get_variable_description(var_id: str) -> str:
    """
    Get description/summary for a variable.
    
    Args:
        var_id (str): Variable ID
        
    Returns:
        str: Description of the variable
    """
    try:
        if var_id in df_tables:
            df = df_tables[var_id]
            
            # Create a basic statistical description
            if not df.empty:
                df_clean = df.dropna()
                if not df_clean.empty:
                    values = df_clean.iloc[:, 0]
                    description = f"Variable {var_id} has {len(df_clean)} categories. "
                    
                    # Find top categories
                    top_values = values.nlargest(3)
                    if len(top_values) > 0:
                        description += f"Top responses: "
                        for idx, val in top_values.items():
                            description += f"{idx} ({val:.1f}%), "
                        description = description.rstrip(", ")
                    
                    return description
                else:
                    return f"Variable {var_id} has no valid data."
            else:
                return f"Variable {var_id} is empty."
        else:
            return f"Variable {var_id} not found in dataset."
            
    except Exception as e:
        return f"Error describing variable {var_id}: {str(e)}"


def save_plots_for_analysis(var_ids: List[str], analysis_id: str = "analysis") -> Dict[str, str]:
    """
    Save plots for selected variables and return file paths.
    
    Args:
        var_ids (list): List of variable IDs to plot
        analysis_id (str): Unique identifier for this analysis
        
    Returns:
        dict: Dictionary mapping variable IDs to plot file paths
    """
    plot_dir = "plot_images"
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)
    
    plot_paths = {}
    
    # Create individual plots
    plots = create_multiple_plots(var_ids, save_plots=True, plot_dir=plot_dir)
    
    for var_id in var_ids:
        if var_id in plots:
            plot_filename = f"plot_{var_id.replace('|', '_')}.png"
            plot_paths[var_id] = os.path.join(plot_dir, plot_filename)
    
    # Create summary grid plot
    if len(var_ids) > 1:
        summary_fig = create_summary_plots_grid(var_ids)
        summary_filename = f"summary_plots_{analysis_id}.png"
        summary_path = os.path.join(plot_dir, summary_filename)
        summary_fig.savefig(summary_path, dpi=150, bbox_inches='tight')
        plot_paths['summary'] = summary_path
        plt.close(summary_fig)
    
    # Close individual plots to free memory
    for fig in plots.values():
        plt.close(fig)
    
    return plot_paths


# ============================================================================
# SES RELATIONSHIP PLOTTING FUNCTIONS
# ============================================================================

# def get_ses_variable_info(ses_var: str) -> Dict:
#     """
#     Get information about a SES variable including its categories and labels.
    
#     Parameters:
#     -----------
#     ses_var : str
#         SES variable name (sexo, edad, edu, region, empleo)
        
#     Returns:
#     --------
#     Dict with variable info including categories, labels, and category count
#     """
#     ses_info = {
#         'variable': ses_var,
#         'categories': [],
#         'labels': {},
#         'category_count': 0,
#         'is_ordinal': ses_var in ['edad', 'edu']  # edad and edu are ordinal
#     }
    
#     # Standard SES variable categories based on workspace analysis
#     if ses_var == 'sexo':
#         ses_info['categories'] = ['Female', 'Male']
#         ses_info['labels'] = {'Female': 'Female', 'Male': 'Male'}
#         ses_info['category_count'] = 2
        
#     elif ses_var == 'edad':
#         ses_info['categories'] = ['25-34', '35-44', '45-54', '55-64', '65-74', '75+']
#         ses_info['labels'] = {cat: cat for cat in ses_info['categories']}
#         ses_info['category_count'] = 6
        
#     elif ses_var == 'edu':
#         ses_info['categories'] = ['básica', 'media']
#         ses_info['labels'] = {'básica': 'Básica', 'media': 'Media'}
#         ses_info['category_count'] = 2
        
#     elif ses_var == 'region':
#         ses_info['categories'] = ['Region 01', 'Region 02', 'Region 03', 'Region 04']
#         ses_info['labels'] = {
#             'Region 01': 'Region 01', 
#             'Region 02': 'Region 02', 
#             'Region 03': 'Region 03', 
#             'Region 04': 'Region 04'
#         }
#         ses_info['category_count'] = 4
        
#     elif ses_var == 'empleo':
#         ses_info['categories'] = ['1.0', '2.0', '3.0', '4.0']
#         ses_info['labels'] = {
#             '1.0': 'Empleado',
#             '2.0': 'No empleado', 
#             '3.0': 'Estudiante',
#             '4.0': 'Hogar'
#         }
#         ses_info['category_count'] = 4
        
#     return ses_info


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
    
    Visualization logic:
    - ≤3 SES categories: Barplot with target variable values for each SES category
    - ≥4 SES categories: Line plot with one line per target category
    - SES 'region': Regional heatmap visualization
    
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
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Determine plot type based on SES variable characteristics
    if ses_var == 'region' or ses_var == 'Region':
        # Special case: Always use enhanced heatmap for region
        _create_regional_heatmap_plot(clean_df, ses_var, target_var, ses_labels, target_labels, ax, target_color_map)
        plot_type = "Regional Heatmap"
        
    elif ses_category_count <= 3:
        # Barplot for ≤3 categories
        _create_barplot_ses(clean_df, ses_var, target_var, ses_labels, target_labels, ax, target_color_map)
        plot_type = "Bar Plot"
        
    else:
        # Line plot for ≥4 categories  
        _create_lineplot_ses(clean_df, ses_var, target_var, ses_labels, target_labels, ax, target_color_map)
        plot_type = "Line Plot"
    
    # Set title
    if title is None:
        if len(ses_categories) > 0:
            title = f"{plot_type}: Relationship between {ses_var.title()} and {target_var.title()}\n({ses_category_count} SES categories)"
        else:
            title = f"{plot_type}: Relationship between {ses_var.title()} and {target_var.title()}"
    
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
    Create stacked barplot with SES categories on Y-axis and target categories as colors.
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
    
    # Add legend for target variable categories
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
    Create line plot with one line per target category.
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
    
    # Enhanced legend showing target categories
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
    Create enhanced heatmap visualization for regional data.
    """
    # Create crosstab for the relationship
    crosstab = pd.crosstab(df[ses_var], df[target_var], normalize='index') * 100
    
    # Create heatmap with relabeled data
    heatmap_data = crosstab.copy()
    
    # Rename indices and columns with labels
    new_index = [ses_labels.get(cat, f'Region {cat}') for cat in heatmap_data.index]
    new_columns = [target_labels.get(cat, str(cat)) for cat in heatmap_data.columns]
    heatmap_data.index = pd.Index(new_index)
    heatmap_data.columns = pd.Index(new_columns)
    
    # Create heatmap
    sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='RdYlBu_r',
                ax=ax, cbar_kws={'label': 'Percentage (%)', 'shrink': 0.8},
                linewidths=1, linecolor='white',
                annot_kws={'fontsize': 10, 'fontweight': 'bold'})
    
    # Set labels
    ax.set_xlabel(f'{target_var.title()} Categories', fontsize=12, fontweight='bold')
    ax.set_ylabel('Mexican Regions', fontsize=12, fontweight='bold')
    
    # Rotate labels for better readability
    ax.tick_params(axis='x', rotation=45)
    ax.tick_params(axis='y', rotation=0)


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


def create_ses_summary_grid(df: pd.DataFrame,
                           ses_vars: List[str],
                           target_var: str,
                           title: Optional[str] = None,
                           figsize: Tuple[int, int] = (20, 12),
                           save_path: Optional[str] = None) -> matplotlib.figure.Figure:
    """
    Create a summary grid showing relationships between multiple SES variables and a target variable.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the data
    ses_vars : list
        List of SES variables to include
    target_var : str
        Target variable to analyze relationships with
    title : str, optional
        Overall plot title
    figsize : tuple
        Figure size (width, height)
    save_path : str, optional
        Path to save the plot
        
    Returns:
    --------
    matplotlib.figure.Figure
        The created figure with subplots
    """
    # Filter SES variables that exist in the data
    available_ses_vars = [var for var in ses_vars if var in df.columns]
    
    if not available_ses_vars:
        raise ValueError("None of the specified SES variables found in data")
    
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
    for i, ses_var in enumerate(available_ses_vars):
        ax = axes[i]
        
        try:
            # Get SES variable info
            ses_info = get_ses_variable_info(ses_var)
            
            # Clean data for this specific pair
            clean_df = df[[ses_var, target_var]].dropna()
            
            if clean_df.empty:
                ax.text(0.5, 0.5, f'No data available\nfor {ses_var} vs {target_var}', 
                       ha='center', va='center', transform=ax.transAxes)
                ax.set_title(f'{ses_var.title()} vs {target_var.title()}')
                continue
            
            # Create a simple version of the SES plot for the grid
            # This is a simplified version for the grid display
            crosstab = pd.crosstab(clean_df[ses_var], clean_df[target_var], normalize='index') * 100
            
            # Create simple heatmap for grid display
            sns.heatmap(crosstab, annot=True, fmt='.1f', cmap='RdYlBu_r',
                       ax=ax, cbar=False, linewidths=0.5)
            
            # Set subplot title
            ax.set_title(f'{ses_var.title()} vs {target_var.title()}\n(n={len(clean_df)})', fontsize=10)
            ax.tick_params(axis='both', labelsize=8)
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Error creating plot\nfor {ses_var}:\n{str(e)}', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'{ses_var.title()} vs {target_var.title()} (Error)', fontsize=10)
    
    # Hide empty subplots
    for j in range(n_plots, len(axes)):
        axes[j].set_visible(False)
    
    # Set overall title
    if title is None:
        title = f'SES Variables Relationship Analysis: {target_var.title()}'
    
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
    
    # Improve layout
    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    
    # Save if requested
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Summary grid saved to: {save_path}")
    
    return fig
