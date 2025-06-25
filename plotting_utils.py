"""
Plotting Module for Navegador Project

This module contains plotting functions extracted from nav_py13_reporte1.ipynb
for generating visualizations of survey data.
"""

import os
import re
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from dataset_knowledge import df_tables


def create_plot(df: pd.DataFrame, question: str, figsize: Tuple[int, int] = (6, 8)) -> plt.Figure:
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
        values = df_clean.iloc[:, 0].values  # Use first column for values
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
        values = df_clean.iloc[:, 0].values  # Use first column for values
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


def create_multiple_plots(var_ids: List[str], save_plots: bool = True, plot_dir: str = "plot_images") -> Dict[str, plt.Figure]:
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


def create_summary_plots_grid(var_ids: List[str], max_cols: int = 2, figsize: Tuple[int, int] = (12, 8)) -> plt.Figure:
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
