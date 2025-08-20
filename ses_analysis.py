"""
SES Analysis Module for Processing Survey Data
This module provides a comprehensive set of tools for analyzing socioeconomic status (SES)
relationships in survey data, including data validation, statistical analysis, and visualization.
"""

from typing import Dict, List, Tuple, Any, Optional, Union, cast
import logging
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats.contingency import association
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import seaborn as sns

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional, Any, Union
import seaborn as sns
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AnalysisConfig:
    """Configuration for SES analysis."""
    
    def __init__(self,
                residual_categories: Optional[List[str]] = None,
                weight_variable: str = 'Pondi2',
                min_sample_size: int = 30,
                confidence_level: float = 0.95,
                colormap: str = 'viridis'):
        """Initialize analysis configuration."""
        self.residual_categories = residual_categories or []
        self.weight_variable = weight_variable
        self.min_sample_size = min_sample_size
        self.confidence_level = confidence_level
        self.colormap = colormap

    @staticmethod
    def categorize_age(age_value):
        """
        Categorize continuous age values into age groups.
        Based on standard demographic categories used in Mexican surveys.
        """
        if pd.isna(age_value) or age_value < 0:
            return None
        
        age = float(age_value)
        
        if age <= 18:
            return '0-18'
        elif age <= 24:
            return '19-24'
        elif age <= 34:
            return '25-34'
        elif age <= 44:
            return '35-44'
        elif age <= 54:
            return '45-54'
        elif age <= 64:
            return '55-64'
        else:
            return '65+'

    @staticmethod
    def preprocess_survey_data(los_mex_dict: Dict) -> Dict:
        """
        Create missing SES variables (edad, region, empleo) from available raw variables.
        
        Mappings based on investigation:
        - Region → region (24/26 surveys have this)
        - sd2 → edad (24/26 surveys, needs categorization)
        - sd5 → empleo (23/26 surveys)
        
        Returns:
            Updated los_mex_dict with new SES variables added to dataframes
        """
        logger.info("🔧 CREATING MISSING SES VARIABLES")
        
        mapping_stats = {
            'region_created': 0,
            'edad_created': 0, 
            'empleo_created': 0,
            'total_surveys': 0
        }
        
        # Variable mappings
        region_mapping = {
            1.0: '01',  # Norte
            2.0: '02',  # Centro
            3.0: '03',  # Centro Occidente
            4.0: '04',  # Sureste
            5.0: '01'   # Some surveys have 5 regions, map to Norte
        }
        
        empleo_mapping = {
            -1.0: None,  # Invalid/missing
            1.0: '01',   # Empleado
            2.0: '02',   # No empleado/Desempleado
            3.0: '03',   # Estudiante
            4.0: '04',   # Hogar/Ama de casa
            5.0: '05',   # Jubilado/Pensionado
            9.0: None    # No answer/Don't know
        }
        
        for survey_name, survey_data in los_mex_dict['enc_dict'].items():
            df = survey_data['dataframe'].copy()
            mapping_stats['total_surveys'] += 1
            changes_made = []
            
            # 1. Create 'region' from 'Region'
            if 'Region' in df.columns and 'region' not in df.columns:
                df['region'] = df['Region'].map(region_mapping)
                changes_made.append('region')
                mapping_stats['region_created'] += 1
            
            # 2. Create 'edad' from 'sd2' (with categorization)
            if 'sd2' in df.columns and 'edad' not in df.columns:
                df['edad'] = df['sd2'].apply(AnalysisConfig.categorize_age)
                changes_made.append('edad')
                mapping_stats['edad_created'] += 1
            
            # 3. Create 'empleo' from 'sd5' 
            if 'sd5' in df.columns and 'empleo' not in df.columns:
                df['empleo'] = df['sd5'].map(empleo_mapping)
                changes_made.append('empleo')
                mapping_stats['empleo_created'] += 1
            
            # Update the dataframe in the dictionary
            if changes_made:
                los_mex_dict['enc_dict'][survey_name]['dataframe'] = df
                logger.info(f"✅ {survey_name}: Created {changes_made}")
            else:
                logger.info(f"⏭️  {survey_name}: No new SES variables needed")
        
        # Log summary
        logger.info(f"✅ region created in {mapping_stats['region_created']}/{mapping_stats['total_surveys']} surveys")
        logger.info(f"✅ edad created in {mapping_stats['edad_created']}/{mapping_stats['total_surveys']} surveys")
        logger.info(f"✅ empleo created in {mapping_stats['empleo_created']}/{mapping_stats['total_surveys']} surveys")
        
        total_new_variables = sum([mapping_stats['region_created'], 
                                mapping_stats['edad_created'], 
                                mapping_stats['empleo_created']])
        logger.info(f"🎉 Total new SES variables created: {total_new_variables}")
        
        return los_mex_dict
        

class SESDataValidator:
    """Validates and prepares survey data for SES analysis."""
    
    @staticmethod
    def verify_metadata(df: pd.DataFrame, 
                       required_vars: List[str],
                       ses_labels: Optional[Dict[str, str]] = None,
                       var_labels: Optional[Dict[str, str]] = None) -> Tuple[bool, str]:
        """Verify all required variables and metadata are present."""
        # Check dataframe
        if df is None or df.empty:
            return False, "Dataset is empty or None"
            
        # Check required variables
        missing_vars = [var for var in required_vars if var not in df.columns]
        if missing_vars:
            return False, f"Missing required variables: {missing_vars}"
            
        # Verify label dictionaries if provided
        if ses_labels is not None and not isinstance(ses_labels, dict):
            return False, "SES labels must be a dictionary"
        if var_labels is not None and not isinstance(var_labels, dict):
            return False, "Variable labels must be a dictionary"
            
        return True, "All metadata verified"

    @staticmethod
    def detect_variable_types(df: pd.DataFrame,
                            cats_residuales: Optional[List[str]] = None) -> Dict[str, str]:
        """Detect and categorize variables as nominal, ordinal, or interval."""
        var_types = {}
        cats_residuales = cats_residuales or ['NS', 'NC', 'No sabe', 'No contesta']
        
        for col in df.columns:
            unique_vals = df[col].dropna().unique()
            
            # Check if values are numeric
            if pd.api.types.is_numeric_dtype(df[col]):
                # Check if mostly integers
                if np.all(np.mod(df[col].dropna(), 1) == 0):
                    # Check for ordinal pattern
                    clean_vals = [x for x in unique_vals 
                                if str(x) not in cats_residuales]
                    if len(clean_vals) > 0 and all(isinstance(x, (int, float)) 
                                                 for x in clean_vals):
                        var_types[col] = 'ordinal'
                    else:
                        var_types[col] = 'nominal'
                else:
                    var_types[col] = 'interval'
            else:
                var_types[col] = 'nominal'
                
        return var_types

class SESAnalyzer:
    """Core SES analysis functionality."""
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """Initialize the analyzer with configuration."""
        self.config = config or AnalysisConfig()
        self.validator = SESDataValidator()
        
    def analyze_single_relationship(self,
                                  df: pd.DataFrame,
                                  target_var: str,
                                  ses_var: str,
                                  ses_labels: Optional[Dict[str, str]] = None,
                                  var_labels: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Analyze relationship between target variable and SES variable."""
        # Validate inputs
        valid, msg = self.validator.verify_metadata(
            df, [target_var, ses_var], ses_labels, var_labels
        )
        if not valid:
            logger.error(f"Validation failed: {msg}")
            return {"error": msg}
            
        # Initialize results
        results = {
            "target_var": target_var,
            "ses_var": ses_var,
            "statistics": {},
            "tables": {},
            "analysis": {}
        }
        
        try:
            # Detect variable types
            var_types = self.validator.detect_variable_types(df[[target_var, ses_var]])
            results["variable_types"] = var_types
            
                        # Create cross-tabulation
            if self.config.weight_variable in df.columns:
                valid_data = df.dropna(subset=[target_var, ses_var, self.config.weight_variable])
                crosstab = pd.crosstab(
                    valid_data[target_var], 
                    valid_data[ses_var],
                    values=valid_data[self.config.weight_variable],
                    aggfunc='sum'
                )
            else:
                valid_data = df.dropna(subset=[target_var, ses_var])
                crosstab = pd.crosstab(
                    valid_data[target_var], 
                    valid_data[ses_var]
                )
            
            # Replace NaN with 0 and convert to integers
            crosstab = crosstab.fillna(0).round().astype(int)
            results["tables"]["crosstab"] = crosstab
            
            # Calculate appropriate statistics based on variable types
            both_ordinal = (var_types[target_var] in ['ordinal', 'interval'] and 
                          var_types[ses_var] in ['ordinal', 'interval'])
            
            # Always calculate chi-square for categorical relationships
            chi2, p_value, dof, expected = stats.chi2_contingency(crosstab)
            results["statistics"].update({
                "chi_square": chi2,
                "p_value": p_value,
                "degrees_of_freedom": dof,
                "cramers_v": association(crosstab, method="cramer")
            })
            
            # Add correlation analysis for ordinal variables
            if both_ordinal:
                # Spearman correlation for ordinal data
                spearman_corr, spearman_p = stats.spearmanr(
                    valid_data[target_var], 
                    valid_data[ses_var]
                )
                # Kendall's Tau for ordinal data
                kendall_corr, kendall_p = stats.kendalltau(
                    valid_data[target_var], 
                    valid_data[ses_var]
                )
                results["statistics"].update({
                    "spearman_correlation": spearman_corr,
                    "spearman_p_value": spearman_p,
                    "kendall_tau": kendall_corr,
                    "kendall_p_value": kendall_p
                })
            
            # Perform leader analysis with significance testing
            prop_table, leaders = self._leader_analysis(
                crosstab, ses_labels, var_labels
            )
            results["tables"]["proportions"] = prop_table
            results["analysis"]["leaders"] = leaders
            
            return results
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            return {"error": str(e)}
    
    def analyze_multiple_relationships(self,
                                     df: pd.DataFrame,
                                     target_vars: List[str],
                                     ses_var: str,
                                     ses_labels: Optional[Dict[str, str]] = None,
                                     var_labels: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Analyze relationships between multiple target variables and a SES variable."""
        results = {}
        for target_var in target_vars:
            results[target_var] = self.analyze_single_relationship(
                df, target_var, ses_var, ses_labels, var_labels
            )
        return results
    
    def _leader_analysis(self,
                        crosstab: pd.DataFrame,
                        ses_labels: Optional[Dict[str, str]] = None,
                        var_labels: Optional[Dict[str, str]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Perform leader analysis with significance testing."""
        proportions = crosstab.div(crosstab.sum(axis=0), axis=1)
        leaders: Dict[str, Any] = {}
        
        for col in proportions.columns:
            # Get all proportions for this column
            col_props = proportions[col].sort_values(ascending=False)
            top_cats = col_props.nlargest(2)
            ses_label = ses_labels.get(str(col), str(col)) if ses_labels else str(col)
            
            # Calculate standard error and confidence interval for difference
            n = crosstab[col].sum()  # Sample size for this column
            p1, p2 = top_cats.iloc[0], top_cats.iloc[1]
            
            # Standard error of difference between proportions
            se_diff = np.sqrt((p1 * (1-p1) + p2 * (1-p2)) / n)
            
            # Calculate z-score and p-value
            diff = p1 - p2
            z_score = diff / se_diff
            p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))  # Two-tailed test
            
            # Calculate confidence interval
            ci_margin = stats.norm.ppf(1 - (1 - self.config.confidence_level) / 2) * se_diff
            ci_lower = diff - ci_margin
            ci_upper = diff + ci_margin
            
            leaders[ses_label] = {
                "first": {
                    "category": var_labels.get(str(top_cats.index[0]), str(top_cats.index[0]))
                    if var_labels else str(top_cats.index[0]),
                    "proportion": float(p1)
                },
                "second": {
                    "category": var_labels.get(str(top_cats.index[1]), str(top_cats.index[1]))
                    if var_labels else str(top_cats.index[1]),
                    "proportion": float(p2)
                },
                "difference": float(diff),
                "significance_test": {
                    "z_score": float(z_score),
                    "p_value": float(p_value),
                    "confidence_interval": {
                        "lower": float(ci_lower),
                        "upper": float(ci_upper)
                    },
                    "standard_error": float(se_diff),
                    "sample_size": int(n)
                }
            }
            
        return proportions, leaders

class SESVisualizer:
    """Visualization tools for SES analysis."""
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """Initialize with optional configuration."""
        self.config = config or AnalysisConfig()
        
    def create_relationship_plot(self,
                               df: pd.DataFrame,
                               target_var: str,
                               ses_var: str,
                               title: Optional[str] = None,
                               ses_labels: Optional[Dict[str, str]] = None,
                               var_labels: Optional[Dict[str, str]] = None,
                               plot_type: str = 'auto',
                               figsize: Tuple[int, int] = (10, 6)) -> Tuple[Figure, Axes]:
        """Create visualization for SES relationship."""
        # Determine plot type if auto
        if plot_type == 'auto':
            n_categories = len(df[ses_var].unique())
            plot_type = 'bar' if n_categories <= 4 else 'heatmap'
            
        fig, ax = plt.subplots(figsize=figsize)
        
        if plot_type == 'bar':
            self._create_bar_plot(df, target_var, ses_var, ax, ses_labels, var_labels)
        elif plot_type == 'heatmap':
            self._create_heatmap(df, target_var, ses_var, ax, ses_labels, var_labels)
        
        if title:
            ax.set_title(title)
            
        return fig, ax
    
    def _create_bar_plot(self,
                        df: pd.DataFrame,
                        target_var: str,
                        ses_var: str,
                        ax: Axes,
                        ses_labels: Optional[Dict[str, str]] = None,
                        var_labels: Optional[Dict[str, str]] = None):
        """Create stacked bar plot."""
        # Calculate proportions
        props = pd.crosstab(
            df[target_var], 
            df[ses_var], 
            normalize='columns'
        )
        
        # Create stacked bar plot
        props.plot(kind='bar', stacked=True, ax=ax)
        
        # Get current ticks and ensure we have same number of labels
        xticks = ax.get_xticks()
        # Customize labels
        if ses_labels:
            labels = [ses_labels.get(str(x), str(x)) for x in props.columns]
            ax.set_xticks(xticks[:len(labels)])  # Ensure ticks match labels
            ax.set_xticklabels(labels)
            
        if var_labels:
            legend_labels = [var_labels.get(str(x), str(x)) for x in props.index]
            ax.legend(legend_labels)
            
        ax.set_ylabel('Proportion')
    
    def _create_heatmap(self,
                       df: pd.DataFrame,
                       target_var: str,
                       ses_var: str,
                       ax: Axes,
                       ses_labels: Optional[Dict[str, str]] = None,
                       var_labels: Optional[Dict[str, str]] = None):
        """Create heatmap visualization."""
        # Calculate proportions
        props = pd.crosstab(
            df[target_var],
            df[ses_var],
            normalize='columns'
        )
        
        # Create heatmap
        sns.heatmap(props, annot=True, fmt='.2f', cmap=self.config.colormap, ax=ax)
        
        # Customize labels
        if ses_labels:
            ax.set_xticklabels([ses_labels.get(x, str(x)) for x in props.columns])
        if var_labels:
            ax.set_yticklabels([var_labels.get(x, str(x)) for x in props.index])

def create_analysis_pipeline(config: Optional[AnalysisConfig] = None) -> Tuple[SESAnalyzer, SESVisualizer]:
    """Create a complete analysis pipeline."""
    config = config or AnalysisConfig()
    analyzer = SESAnalyzer(config)
    visualizer = SESVisualizer(config)
    return analyzer, visualizer
