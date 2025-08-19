"""
Test module for SES Analysis functionality
"""

import unittest
import pandas as pd
import numpy as np
import random
import pickle
from pathlib import Path
import matplotlib.pyplot as plt
from ses_analysis import (
    AnalysisConfig,
    SESDataValidator,
    SESAnalyzer,
    SESVisualizer,
    create_analysis_pipeline
)

class TestSESAnalysis(unittest.TestCase):
    """Test cases for SES analysis module."""

    def setUp(self):
        """Set up test data using real los_mex data."""
        # Load los_mex dictionary
        with open('/Users/salvadorVMA/Google Drive/01 Proyectos/2025/navegador/encuestas/los_mex_dict.pkl', 'rb') as f:
            self.los_mex_dict = pickle.load(f)
            
        # Get all available questions from pregs_list
        all_questions = [qid for qid in self.los_mex_dict['pregs_dict'].keys() if qid.startswith('p')]
        
        # Extract survey IDs from all questions
        survey_ids = set(qid.split('|')[1] for qid in all_questions)
        # Get the first survey ID to use for testing
        selected_survey_id = list(survey_ids)[0]
        
        # Find the full survey name using rev_enc_nom_dict
        rev_enc_nom_dict = {v: k for k, v in self.los_mex_dict['enc_nom_dict'].items()}
        selected_survey = rev_enc_nom_dict[selected_survey_id]
        
        # Get the dataframe for the selected survey
        self.test_data = self.los_mex_dict['enc_dict'][selected_survey]['dataframe']
        
        # Get standard SES variables that should exist in most surveys
        standard_ses_vars = ['region', 'edad', 'empleo']
        self.available_ses_vars = [var for var in standard_ses_vars if var in self.test_data.columns]
        
        # If this survey doesn't have SES variables, try other surveys
        if not self.available_ses_vars:
            for other_id in survey_ids:
                if other_id == selected_survey_id:
                    continue
                other_survey = rev_enc_nom_dict[other_id]
                test_data = self.los_mex_dict['enc_dict'][other_survey]['dataframe']
                available_ses = [var for var in standard_ses_vars if var in test_data.columns]
                if available_ses:
                    selected_survey_id = other_id
                    selected_survey = other_survey
                    self.test_data = test_data
                    self.available_ses_vars = available_ses
                    break
            
        # Ensure we have at least one SES variable
        if not self.available_ses_vars:
            raise ValueError("No surveys found with any standard SES variables (region, edad, empleo)")
                    
        # Get all questions from this survey
        survey_questions = [qid.split('|')[0] for qid in all_questions if qid.split('|')[1] == selected_survey_id]
        # Only include questions that exist in the dataframe
        available_questions = [q for q in survey_questions if q in self.test_data.columns]
        # Select 5 random questions
        self.target_vars = random.sample(available_questions, min(5, len(available_questions)))
        
        # Create flattened labels for testing
        self.ses_labels = {
            str(i): f'Level {i}' for i in range(1, 5)
        }
        
        # Create flattened labels for variables (convert nested dict to flat)
        self.var_labels = {}
        for var in self.target_vars:
            for val in self.test_data[var].unique():
                if pd.notna(val):
                    key = f"{var}_{str(val)}"
                    self.var_labels[key] = f"{var} value {val}"
        
        # Create test configuration
        self.config = AnalysisConfig(
            residual_categories=['88', '99', 'NS', 'NC'],
            weight_variable='Pondi2'
        )

    def _print_analysis_results(self, results):
        """Helper method to print analysis results."""
        print("\n📊 Analysis Results:")
        print("-" * 40)
        if 'statistics' in results:
            print("\nStatistics:")
            for stat, value in results['statistics'].items():
                if isinstance(value, (int, float)):
                    print(f"  • {stat}: {value:.4f}")
                else:
                    print(f"  • {stat}: {value}")
        
        if 'tables' in results and 'crosstab' in results['tables']:
            print("\nContingency Table:")
            print(results['tables']['crosstab'])
        
        if 'analysis' in results:
            print("\nDetailed Analysis:")
            for key, value in results['analysis'].items():
                if isinstance(value, dict):
                    print(f"\n{key}:")
                    for subkey, subval in value.items():
                        print(f"  • {subkey}: {subval}")
                else:
                    print(f"  • {key}: {value}")

    def test_data_validator(self):
        """Test data validation functionality."""
        print("\n🔍 Testing Data Validator")
        print("=" * 60)
        
        validator = SESDataValidator()
        
        # Test with one SES variable and two target variables
        test_vars = [self.available_ses_vars[0]] + self.target_vars[:2]
        print("Variables to validate:", test_vars)
        
        # Test with valid data
        valid, msg = validator.verify_metadata(
            self.test_data,
            test_vars,
            self.ses_labels,
            self.var_labels
        )
        self.assertTrue(valid)
        print("\nValidation Result:", msg)
        
        # Test with missing variables
        valid, msg = validator.verify_metadata(
            self.test_data,
            ['nonexistent_var'],
            self.ses_labels,
            self.var_labels
        )
        self.assertFalse(valid)
        print("\nValidation with invalid data:", msg)
        
        # Test variable type detection
        var_types = validator.detect_variable_types(
            self.test_data,
            ['88', '99', 'NS', 'NC']
        )
        
        # Check if some variables were classified
        self.assertTrue(len(var_types) > 0)
        
        # Print detected types
        print("\nDetected Variable Types:")
        for var, var_type in var_types.items():
            print(f"  • {var}: {var_type}")
        
        # Verify variable type classification
        for var in test_vars:
            self.assertIn(var, var_types)
            self.assertIn(var_types[var], ['nominal', 'ordinal', 'interval'])

    def _test_single_relationship(self):
        """Helper method to test single relationship analysis."""
        analyzer = SESAnalyzer(self.config)
        
        # Get a random SES variable and a random target variable
        ses_var = self.available_ses_vars[0]
        target_var = self.target_vars[0]
        
        print(f"\nAnalyzing relationship between:")
        print(f"  • SES Variable: {ses_var}")
        print(f"  • Target Variable: {target_var}")
        
        # Test single relationship analysis
        results = analyzer.analyze_single_relationship(
            self.test_data,
            target_var,
            ses_var,
            self.ses_labels,
            self.var_labels
        )
        
        self.assertIn('statistics', results)
        self.assertIn('tables', results)
        self.assertIn('analysis', results)
        
        self._print_analysis_results(results)
        
    def _test_multiple_relationships(self):
        """Helper method to test multiple relationships analysis."""
        analyzer = SESAnalyzer(self.config)
        
        # Get test variables
        ses_var = self.available_ses_vars[0]
        test_vars = self.target_vars[:2]  # Take first two target variables
        
        print("\n📊 Testing Multiple Relationships Analysis")
        print(f"Analyzing {len(test_vars)} target variables against {ses_var}")
        
        multi_results = analyzer.analyze_multiple_relationships(
            self.test_data,
            test_vars,
            ses_var,
            self.ses_labels,
            self.var_labels
        )
        
        self.assertIn('analyses', multi_results)
        self.assertEqual(len(multi_results['analyses']), len(test_vars))
        self.assertIn('summary', multi_results)
        
        print("\nAnalysis Results:")
        if 'analyses' in multi_results:
            for var, analysis in multi_results['analyses'].items():
                print(f"\n📊 Results for {var}:")
                print("-" * 30)
                if 'statistics' in analysis:
                    for stat, value in analysis['statistics'].items():
                        if isinstance(value, (int, float)):
                            print(f"  • {stat}: {value:.4f}")
                        else:
                            print(f"  • {stat}: {value}")
        
        if 'summary' in multi_results:
            print("\n📈 Summary Statistics:")
            print("-" * 30)
            for stat, value in multi_results['summary'].items():
                if isinstance(value, (int, float)):
                    print(f"  • {stat}: {value:.4f}")
                else:
                    print(f"  • {stat}: {value}")

    def test_ses_analyzer(self):
        """Test core analysis functionality."""
        print("\n🔍 Testing SES Analyzer")
        print("=" * 60)
        
        # Test single relationship analysis first
        self._test_single_relationship()
        
        # Then test multiple relationships
        self._test_multiple_relationships()
    
    def test_ses_visualizer(self):
        """Test visualization functionality."""
        print("\n🔍 Testing SES Visualizer")
        print("=" * 60)
        
        visualizer = SESVisualizer(self.config)
        
        # Get a random SES variable and a random target variable
        ses_var = self.available_ses_vars[0]
        target_var = self.target_vars[0]
        
        print(f"\nCreating visualizations for:")
        print(f"  • SES Variable: {ses_var}")
        print(f"  • Target Variable: {target_var}")
        
        # Test bar plot creation
        print("\nCreating bar plot...")
        fig, ax = visualizer.create_relationship_plot(
            self.test_data,
            target_var,
            ses_var,
            title=f"{target_var} vs {ses_var}",
            ses_labels=self.ses_labels,
            var_labels=self.var_labels,
            plot_type='bar'
        )
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)
        print("✓ Bar plot created successfully")
        
        # Test heatmap creation
        print("\nCreating heatmap...")
        fig, ax = visualizer.create_relationship_plot(
            self.test_data,
            target_var,
            ses_var,
            title=f"{target_var} vs {ses_var} Heatmap",
            ses_labels=self.ses_labels,
            var_labels=self.var_labels,
            plot_type='heatmap'
        )
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)
        print("✓ Heatmap created successfully")
        
        plt.close('all')  # Clean up plots
        
    def test_analysis_pipeline(self):
        """Test complete analysis pipeline."""
        print("\n🔍 Testing Analysis Pipeline")
        print("=" * 60)
        
        analyzer, visualizer = create_analysis_pipeline(self.config)
        
        # Get a random SES variable and a random target variable
        ses_var = self.available_ses_vars[0]
        target_var = self.target_vars[0]
        
        print(f"\nTesting full pipeline with:")
        print(f"  • SES Variable: {ses_var}")
        print(f"  • Target Variable: {target_var}")
        
        # Test analyzer
        print("\n📊 Running Analysis...")
        results = analyzer.analyze_single_relationship(
            self.test_data,
            target_var,
            ses_var,
            self.ses_labels,
            self.var_labels
        )
        self.assertIn('statistics', results)
        print("✓ Analysis complete")
        
        # Print analysis results
        print("\n📈 Results Summary:")
        print("-" * 40)
        if 'statistics' in results:
            print("Statistics:")
            for stat, value in results['statistics'].items():
                if isinstance(value, (int, float)):
                    print(f"  • {stat}: {value:.4f}")
                else:
                    print(f"  • {stat}: {value}")
            
        if 'tables' in results and 'crosstab' in results['tables']:
            print("\nContingency Table:")
            print(results['tables']['crosstab'])
        
        if 'analysis' in results and 'leaders' in results['analysis']:
            print("\n📈 Leader Analysis:")
            for category, info in results['analysis']['leaders'].items():
                print(f"  • {category}: {info}")
                
        # Test visualizer
        print("\n🎨 Creating Visualization...")
        fig, ax = visualizer.create_relationship_plot(
            self.test_data,
            target_var,
            ses_var,
            title=f"{target_var} vs {ses_var}"
        )
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)
        print("✓ Visualization created")
        
        plt.close('all')  # Clean up plots
        print("\n✨ Pipeline test complete!")

if __name__ == '__main__':
    unittest.main()
